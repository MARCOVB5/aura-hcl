from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.common import ID
from app.models.practitioner import Practitioner


class User(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    practitioner_id: Mapped[int] = mapped_column(
        ID, ForeignKey("practitioner.id", ondelete="RESTRICT"), unique=True
    )
    practitioner: Mapped[Practitioner] = relationship()
