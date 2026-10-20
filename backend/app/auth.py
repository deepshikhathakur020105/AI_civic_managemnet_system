"""JWT authentication with roles: citizen, officer, admin.

- Passwords are hashed with bcrypt (never stored or logged in plain text).
- Access tokens are short-lived JWTs carrying user id, email and role. The role is read from
  the token, so a role change takes effect when the token expires (default 60 min).
- Public registration always creates a `citizen`. Officers/admins are created by an
  administrator with `python -m app.create_user`.
"""
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from . import db

log = logging.getLogger("auth")
ALGORITHM = "HS256"
TOKEN_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
ROLES = {"citizen", "officer", "admin"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SECRET = os.getenv("JWT_SECRET") or ""
if not SECRET:
    SECRET = secrets.token_urlsafe(48)
    log.warning("JWT_SECRET not set: using a random key. Tokens become invalid on restart. "
                "Set JWT_SECRET in production.")

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")
router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def create_token(user_id: int, email: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "email": email, "role": role,
               "iat": now, "exp": now + timedelta(minutes=TOKEN_MINUTES)}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def current_user(token: str = Depends(oauth2)) -> dict:
    try:
        data = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return {"id": int(data["sub"]), "email": data["email"], "role": data["role"]}
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Invalid or expired token",
                            headers={"WWW-Authenticate": "Bearer"})


def require_role(*allowed: str):
    def dep(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in allowed:
            raise HTTPException(403, "You do not have permission for this action")
        return user
    return dep


class Credentials(BaseModel):
    email: str
    password: str


@router.post("/register", status_code=201)
def register(body: Credentials):
    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(422, "Enter a valid email address")
    if not 8 <= len(body.password.encode()) <= 72:  # bcrypt ignores bytes past 72
        raise HTTPException(422, "Password must be 8 to 72 characters")
    try:
        with db.engine.begin() as conn:
            uid = conn.execute(
                text("INSERT INTO users (email, password_hash, role) VALUES (:e,:p,'citizen') RETURNING id"),
                {"e": email, "p": hash_password(body.password)}).scalar()
    except IntegrityError:
        raise HTTPException(409, "An account with this email already exists")
    return {"id": uid, "email": email, "role": "citizen"}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    email = form.username.strip().lower()
    with db.engine.connect() as conn:
        row = conn.execute(text("SELECT id, password_hash, role FROM users WHERE email = :e"),
                           {"e": email}).mappings().first()
    # Same message for unknown email and wrong password (no account enumeration).
    if row is None or not verify_password(form.password, row["password_hash"]):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(row["id"], email, row["role"]),
            "token_type": "bearer", "role": row["role"]}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return user
