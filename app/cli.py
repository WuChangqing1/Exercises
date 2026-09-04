"""Command-line utilities: init-db and create-admin."""
from __future__ import annotations

import getpass
import sys

from alembic import command
from alembic.config import Config

from app.database import SessionLocal
from app.models import User
from app.security import hash_password


def run_migrations() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def create_admin() -> None:
    run_migrations()

    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty.", file=sys.stderr)
        sys.exit(1)

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.", file=sys.stderr)
        sys.exit(1)
    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first() is not None:
            print(f"User '{username}' already exists.", file=sys.stderr)
            sys.exit(1)
        db.add(User(username=username, password_hash=hash_password(password)))
        db.commit()
    finally:
        db.close()

    print(f"Admin user '{username}' created.")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli {init-db|create-admin}", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "init-db":
        run_migrations()
        print("Database initialized.")
    elif sys.argv[1] == "create-admin":
        create_admin()
    else:
        print("Unknown command.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
