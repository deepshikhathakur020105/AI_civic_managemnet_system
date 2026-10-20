"""Create an officer or admin account (public registration only makes citizens).

    python -m app.create_user officer@city.gov.in officer
Prompts for the password so it never lands in shell history.
"""
import getpass
import sys

from sqlalchemy import text

from . import db
from .auth import ROLES, hash_password


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in ROLES:
        raise SystemExit(f"usage: python -m app.create_user <email> <{'|'.join(sorted(ROLES))}>")
    email, role = sys.argv[1].strip().lower(), sys.argv[2]
    password = getpass.getpass("Password (8-72 chars): ")
    if not 8 <= len(password.encode()) <= 72:
        raise SystemExit("Password must be 8 to 72 characters")
    with db.engine.begin() as conn:
        conn.execute(text("INSERT INTO users (email, password_hash, role) VALUES (:e,:p,:r)"),
                     {"e": email, "p": hash_password(password), "r": role})
    print(f"Created {role} {email}")


if __name__ == "__main__":
    main()
