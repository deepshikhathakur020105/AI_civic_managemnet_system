import json
import os
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy import create_engine, text

from .ml.classifier import predict
from .services.priority import compute_priority
from .services.routing import route

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://civic:civic@localhost:5432/civic")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_TYPES = {"image/jpeg", "image/png"}
MAX_BYTES = 8 * 1024 * 1024
DUP_RADIUS_M = 50

app = FastAPI(title="AI Assisted Civic Management")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/complaints")
async def create_complaint(
    image: UploadFile = File(...),
    lat: float = Form(..., ge=-90, le=90),
    lon: float = Form(..., ge=-180, le=180),
    description: str = Form(""),
):
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Only JPEG or PNG images are accepted")
    data = await image.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Image too large (max 8 MB)")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.jpg")
    with open(path, "wb") as f:
        f.write(data)

    category, confidence, severity = predict(path)
    dept_name = route(category, confidence)

    with engine.begin() as conn:
        dup = conn.execute(text("""
            SELECT id FROM complaints
            WHERE category = :cat AND parent_id IS NULL
              AND ST_DWithin(geom, ST_SetSRID(ST_MakePoint(:lon,:lat),4326)::geography, :r)
            ORDER BY created_at LIMIT 1"""),
            {"cat": category, "lon": lon, "lat": lat, "r": DUP_RADIUS_M}).scalar()
        n_reports = 1 + (conn.execute(text(
            "SELECT count(*) FROM complaints WHERE parent_id = :p"), {"p": dup}).scalar() if dup else 0)
        pr = compute_priority(category, severity, 0.0, n_reports + (1 if dup else 0), 0)
        dept_id = conn.execute(text("SELECT id FROM departments WHERE name=:n"),
                               {"n": dept_name}).scalar()
        status = "needs_review" if dept_name == "Manual Review" else "open"
        new_id = conn.execute(text("""
            INSERT INTO complaints (category, category_confidence, description, image_path,
                geom, severity, priority, priority_score, status, department_id, parent_id, created_at)
            VALUES (:cat,:conf,:desc,:img, ST_SetSRID(ST_MakePoint(:lon,:lat),4326)::geography,
                :sev,:pri,:score,:status,:dept,:parent,:ts) RETURNING id"""),
            {"cat": category, "conf": confidence, "desc": description, "img": path,
             "lon": lon, "lat": lat, "sev": severity, "pri": pr["level"], "score": pr["score"],
             "status": status, "dept": dept_id, "parent": dup,
             "ts": datetime.now(timezone.utc)}).scalar()
        conn.execute(text("""INSERT INTO complaint_events (complaint_id, actor, action, detail)
            VALUES (:c,'system','created', CAST(:d AS jsonb))"""),
            {"c": new_id, "d": json.dumps({"priority_factors": pr["factors"]})})

    return {"id": new_id, "category": category, "confidence": confidence,
            "department": dept_name, "priority": pr["level"],
            "duplicate_of": dup, "status": status}


@app.get("/complaints")
def list_complaints(status: str | None = None, limit: int = 100):
    q = """SELECT c.id, c.category, c.priority, c.status, c.parent_id, d.name AS department,
                  ST_Y(c.geom::geometry) AS lat, ST_X(c.geom::geometry) AS lon, c.created_at
           FROM complaints c LEFT JOIN departments d ON d.id = c.department_id
           WHERE (:s IS NULL OR c.status = :s)
           ORDER BY c.priority, c.created_at DESC LIMIT :l"""
    with engine.connect() as conn:
        rows = conn.execute(text(q), {"s": status, "l": min(limit, 500)}).mappings().all()
    return [dict(r) for r in rows]
