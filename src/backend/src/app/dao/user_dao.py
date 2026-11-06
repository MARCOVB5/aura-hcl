"""Provide database lookups and flush-only creation for `User` authentication accounts."""
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.practitioner import Practitioner
from app.models.user import User


class UserDAO:
    """Query and persist `User` accounts with joined `Practitioner` and `Person` profiles."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.scalar(self._query().where(User.id == user_id))

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(self._query().where(User.username == username))

    def get_by_practitioner(self, practitioner_id: int) -> User | None:
        return self.db.scalar(select(User).where(User.practitioner_id == practitioner_id))

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    @staticmethod
    def _query():
        return select(User).options(joinedload(User.practitioner).joinedload(Practitioner.person))
