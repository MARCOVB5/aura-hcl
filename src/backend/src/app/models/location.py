from __future__ import annotations

from app.models import Base
from app.models.common import ID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

'''
Where a patient stays in the department (service · room · bed)
'''

class Location(Base):
  __tablename__ = "location"

  id : Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
  code : Mapped[str] = mapped_column(String(32), unique=True)
  # shown as is in the UI, e.g. "Réanimation · Chambre 12 · Lit A"
  name : Mapped[str] = mapped_column(String(128))
