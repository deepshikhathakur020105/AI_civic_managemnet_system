import os

os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests-only-0123456789"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app import auth, db
from app.main import app


@pytest.fixture()
def client(monkeypatch):
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with eng.begin() as c:
        c.execute(text("""CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'citizen', reputation REAL DEFAULT 1.0)"""))
    monkeypatch.setattr(db, "engine", eng)
    return TestClient(app)


def register(client, email="a@b.com", pw="correct-horse"):
    return client.post("/auth/register", json={"email": email, "password": pw})


def login(client, email="a@b.com", pw="correct-horse"):
    return client.post("/auth/login", data={"username": email, "password": pw})


def test_register_login_me(client):
    assert register(client).status_code == 201
    r = login(client)
    assert r.status_code == 200 and r.json()["role"] == "citizen"
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.json()["email"] == "a@b.com"


def test_password_is_hashed(client):
    register(client)
    with db.engine.connect() as c:
        h = c.execute(text("SELECT password_hash FROM users")).scalar()
    assert h != "correct-horse" and h.startswith("$2")


def test_duplicate_email_and_bad_input(client):
    register(client)
    assert register(client).status_code == 409
    assert register(client, email="not-an-email").status_code == 422
    assert register(client, email="c@d.com", pw="short").status_code == 422
    assert register(client, email="c@d.com", pw="x" * 73).status_code == 422


def test_wrong_password_and_unknown_user_look_identical(client):
    register(client)
    a = login(client, pw="wrong-password")
    b = login(client, email="nobody@x.com")
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_email_case_insensitive(client):
    register(client, email="Mixed@Case.com")
    assert login(client, email="mixed@case.com").status_code == 200


def test_register_cannot_choose_role(client):
    client.post("/auth/register", json={"email": "e@f.com", "password": "correct-horse", "role": "admin"})
    with db.engine.connect() as c:
        assert c.execute(text("SELECT role FROM users WHERE email='e@f.com'")).scalar() == "citizen"


def test_protected_endpoints_need_token(client):
    assert client.get("/complaints").status_code == 401
    assert client.post("/complaints").status_code == 401
    assert client.patch("/complaints/1/status", json={"status": "open"}).status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_citizen_cannot_change_status_but_officer_passes_auth(client):
    cit = {"Authorization": "Bearer " + auth.create_token(1, "c@x.com", "citizen")}
    off = {"Authorization": "Bearer " + auth.create_token(2, "o@x.com", "officer")}
    assert client.patch("/complaints/1/status", json={"status": "resolved"}, headers=cit).status_code == 403
    # officer is authorised; invalid status is then rejected by the handler (422), before any DB access
    assert client.patch("/complaints/1/status", json={"status": "bogus"}, headers=off).status_code == 422


def test_expired_and_tampered_tokens_rejected(client, monkeypatch):
    monkeypatch.setattr(auth, "TOKEN_MINUTES", -1)
    expired = auth.create_token(1, "a@b.com", "citizen")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    monkeypatch.setattr(auth, "TOKEN_MINUTES", 60)
    good = auth.create_token(1, "a@b.com", "citizen")
    tampered = good[:-3] + ("AAA" if not good.endswith("AAA") else "BBB")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401
