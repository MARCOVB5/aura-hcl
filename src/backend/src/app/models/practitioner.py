from __future__ import annotations

from typing import TYPE_CHECKING

from app.models import Base
from app.models.common import ID

from sqlalchemy import ForeignKey, String, text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
  from app.models.person import Person

class Practitioner(Base):
  __tablename__ = "practitioner"

  id : Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
  person_id : Mapped[int] = mapped_column(ID, ForeignKey("person.id"))
  active : Mapped[bool] = mapped_column(Boolean, default =True, server_default=text("true"))
  # shown next to the name, e.g. "Médecin", "Infirmier"
  profession : Mapped[str | None] = mapped_column(String(64))

  person : Mapped[Person] = relationship()
