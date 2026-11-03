from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dao.user_dao import UserDAO
from app.errors import Conflict, NotFound
from app.models.person import Person
from app.models.practitioner import Practitioner
from app.models.user import User
from app.schemas.Auth import LoginRequest
from app.security import create_access_token, hash_password, verify_password

# Equalize password verification work when a username does not exist.
DUMMY_HASH = hash_password("unused-dummy-password")


def unauthorized() -> HTTPException:
    return HTTPException(401, "Invalid credentials or session", headers={"WWW-Authenticate": "Bearer"})


class AuthService:
    def __init__(self, db: Session, users: UserDAO):
        self.db = db
        self.users = users

    def login(self, username: str, password: str) -> str:
        user = self.users.get_by_username(username)
        valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
        if not valid or user is None or not user.practitioner.active:
            raise unauthorized()
        return create_access_token(user.id)

    def create_user(self, practitioner_id: int, username: str, password: str) -> User:
        credentials = LoginRequest(username=username, password=password)
        try:
            practitioner = self.db.get(Practitioner, practitioner_id)
            if practitioner is None:
                raise NotFound("Practitioner not found")
            if not practitioner.active:
                raise Conflict("Practitioner is inactive")
            if self.users.get_by_username(credentials.username) or self.users.get_by_practitioner(practitioner_id):
                raise Conflict("Username or practitioner already has an account")
            user = self.users.create(User(
                username=credentials.username, password_hash=hash_password(password), practitioner=practitioner,
            ))
            self.db.commit()
            return user
        except IntegrityError as exc:
            self.db.rollback()
            raise Conflict("Username or practitioner already has an account") from exc
        except Exception:
            self.db.rollback()
            raise


DEMO_PRACTITIONERS = (
    ("demo.medecin", "Camille", "Demo", "Médecin"),
    ("demo.infirmier", "Alex", "Demo", "Infirmier"),
    ("demo.kine", "Sam", "Demo", "Kinésithérapeute"),
)


def populate_demo_practitioners(db: Session, password: str) -> list[tuple[str, int]]:
    """Create demo staff atomically; matching accounts are left untouched."""
    if not password:
        raise ValueError("Password must not be empty")
    users = UserDAO(db)
    result = []
    try:
        for username, given, family, profession in DEMO_PRACTITIONERS:
            user = users.get_by_username(username)
            if user:
                practitioner = user.practitioner
                person = practitioner.person
                if (person.name_given, person.name_family, practitioner.profession, practitioner.active) != (given, family, profession, True):
                    raise ValueError(f"Conflicting demo account: {username}")
            else:
                practitioner = Practitioner(
                    person=Person(name_given=given, name_family=family),
                    profession=profession, active=True,
                )
                user = users.create(User(
                    username=username, password_hash=hash_password(password), practitioner=practitioner,
                ))
            result.append((username, user.practitioner_id))
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
