from __future__ import annotations

from app.models import Base
from app.models.common import ID

from sqlalchemy import ForeignKey, text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

class Practitioner(Base):
  __tablename__ = "practitioner"

  id : Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
  person_id : Mapped[int] = mapped_column(ID, ForeignKey("person.id"))
  active : Mapped[bool] = mapped_column(Boolean, default =True, server_default=text("1"))
