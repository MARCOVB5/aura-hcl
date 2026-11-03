"""Provision an account for an existing practitioner (no public signup)."""
import argparse
from getpass import getpass

from app.dao.user_dao import UserDAO
from app.db import SessionLocal
from app.errors import AppError
from app.services.auth_service import AuthService


def prompt_password() -> str:
    password = getpass("Password: ")
    if not password or password != getpass("Confirm password: "):
        raise ValueError("Passwords must match and must not be empty")
    return password


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--practitioner-id", type=int, required=True)
    parser.add_argument("--username", required=True)
    args = parser.parse_args()
    try:
        password = prompt_password()
        with SessionLocal() as db:
            user = AuthService(db, UserDAO(db)).create_user(args.practitioner_id, args.username, password)
            print(f"Created {user.username} (practitioner {user.practitioner_id})")
    except AppError as exc:
        parser.exit(1, f"{exc.message}\n")
    except ValueError:
        parser.exit(1, "Invalid username or password; username must contain 1–64 characters and passwords must match.\n")


if __name__ == "__main__":
    main()
