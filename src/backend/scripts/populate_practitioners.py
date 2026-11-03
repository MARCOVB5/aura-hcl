"""Populate three synthetic practitioners and login accounts for local demos."""
import argparse

from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.services.auth_service import populate_demo_practitioners
from create_user import prompt_password


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        password = prompt_password()
        with SessionLocal() as db:
            accounts = populate_demo_practitioners(db, password)
        for username, practitioner_id in accounts:
            print(f"{username} (practitioner {practitioner_id})")
    except IntegrityError:
        parser.exit(1, "Demo accounts conflict with existing database records; no changes committed.\n")
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
