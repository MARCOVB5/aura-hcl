from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.common import ID, enum_values

if TYPE_CHECKING:
  from app.models.encounter import Encounter


class AdmissionStatus(enum.Enum):
  IN_PROGRESS = "IN_PROGRESS"
  COMPLETE = "COMPLETE"


class Hospitalization(Base):
  __tablename__ = "hospitalization"

  encounter_id: Mapped[int] = mapped_column(
    ID, ForeignKey("encounter.id"), primary_key=True
  )
  admission_status: Mapped[AdmissionStatus] = mapped_column(
    Enum(AdmissionStatus, values_callable=enum_values),
    default=AdmissionStatus.IN_PROGRESS,
    server_default="IN_PROGRESS",
  )
  assessment_completed_at: Mapped[datetime | None] = mapped_column(DateTime)

  encounter: Mapped[Encounter] = relationship(back_populates="hospitalization")
