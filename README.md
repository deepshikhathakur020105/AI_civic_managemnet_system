# AI Assisted Civic Management

Team CSE27-197, Graphic Era Hill University. Citizens submit a photo and GPS location; the
system classifies the issue, detects duplicates, assigns a P1-P4 priority and routes it to a
department. Officers review everything on a dashboard.

## Tiers
1. **Tier 1 (current):** upload API, classifier hook, geo duplicate check, rule-based priority and routing, Postgres/PostGIS.
2. **Tier 2:** image-embedding duplicate ranking, trust checks (EXIF, perceptual hash, rate limits), severity.
3. **Tier 3:** mobile app with integrity attestation, bias audit by area.

## Run
    docker compose up --build        # API on :8000, docs at /docs
    cd backend && pip install -r requirements.txt && python -m pytest

The classifier is a stub until a trained model is placed at `backend/models/best.pt`
(until then every complaint goes to the Manual Review queue).

## Frontend
    cd frontend && npm install && npm run dev    # http://localhost:5173, proxies /api to :8000

## Login and roles
Public sign-up creates a `citizen` (can submit and see their own complaints). Officers and admins
(can see all complaints and change status) are created by an administrator:

    docker compose exec api python -m app.create_user officer@example.com officer

Set `JWT_SECRET` (e.g. `export JWT_SECRET=$(openssl rand -hex 32)`) before `docker compose up`.
If unset, a random key is generated at start and everyone is signed out on restart.
Tokens expire after 60 minutes (`JWT_EXPIRE_MINUTES`).
