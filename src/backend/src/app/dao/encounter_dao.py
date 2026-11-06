"""Provide database queries and flush-only persistence for clinical `Encounter` stays."""
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.encounter import Encounter, EncounterStatus

# a stay in one of these states is over (or never happened)
CLOSED_STATUSES = (EncounterStatus.FINISHED, EncounterStatus.CANCELLED, EncounterStatus.ENTERED_IN_ERROR)


class EncounterDAO:
  """Query and persist `Encounter` records, including active-stay resolution.

  Mutating methods flush changes to the session without committing so the calling
  service owns the transaction boundary.
  """

  def __init__(self, session: Session):
    self.session = session

  def get(self, id: int) -> Encounter | None:
    return self.session.get(Encounter, id)

  def get_by_stay_number(self, stay_number: str) -> Encounter | None:
    stmt = select(Encounter).where(Encounter.stay_number == stay_number)
    return self.session.scalar(stmt)

  def get_current(self, patient_id: int, now: datetime) -> Encounter | None:
    """Return the patient's most recently admitted active stay in progress at `now`.

    Exclude stays in `CLOSED_STATUSES`, stays whose `admission_date` is after
    `now`, and stays whose `actual_discharge_date` is at or before `now`.

    Args:
      patient_id (int): Primary key of the patient.
      now (datetime): Reference timestamp used to evaluate admission and discharge bounds.

    Returns:
      Encounter | None: Latest active `Encounter` for the patient, or `None`.
    """
    stmt = (
      select(Encounter)
      .where(
        Encounter.patient_id == patient_id,
        Encounter.admission_date <= now,
        or_(Encounter.actual_discharge_date.is_(None), Encounter.actual_discharge_date > now),
        Encounter.status.not_in(CLOSED_STATUSES),
      )
      .order_by(Encounter.admission_date.desc())
      .limit(1)
    )
    return self.session.scalar(stmt)

  def create(self, encounter: Encounter) -> Encounter:
    self.session.add(encounter)
    self.session.flush()
    return encounter

  def delete(self, encounter: Encounter) -> None:
    self.session.delete(encounter)
    self.session.flush()
