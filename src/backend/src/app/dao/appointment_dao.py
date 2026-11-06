"""Provide queries, stay-window checks, and persistence for care `Appointment` records."""
import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.dao.patient_dao import PATIENT_OPTIONS
from app.models.care import Appointment
from app.models.practitioner import Practitioner

# everything an appointment shows: patient, stay, caregivers
_DETAIL_OPTIONS = (
  selectinload(Appointment.patient).options(*PATIENT_OPTIONS),
  selectinload(Appointment.encounter),
  selectinload(Appointment.performers).selectinload(Practitioner.person),
  selectinload(Appointment.validated_by).selectinload(Practitioner.person),
)


class AppointmentDAO:
  """Query and persist care `Appointment` records with full patient, stay, and caregiver graphs."""

  def __init__(self, session: Session):
    self.session = session

  def get(self, id: int) -> Appointment | None:
    stmt = select(Appointment).options(*_DETAIL_OPTIONS).where(Appointment.id == id)
    return self.session.scalar(stmt)

  def search(
    self,
    start: datetime.date | None = None,
    end: datetime.date | None = None,
    patient_id: int | None = None,
  ) -> list[Appointment]:
    """Search appointments within an inclusive calendar-day range and optional patient filter.

    Convert `end` into a strict upper bound at `00:00:00` on `end + 1 day` so all
    appointments scheduled anywhere on the `end` calendar day are included.

    Args:
      start (datetime.date | None): Inclusive lower-bound date for `scheduled_start`.
      end (datetime.date | None): Inclusive upper-bound date for `scheduled_start`.
      patient_id (int | None): Optional patient primary key filter.

    Returns:
      list[Appointment]: Matching eager-loaded appointments ordered by `(scheduled_start, id)`.
    """
    stmt = select(Appointment).options(*_DETAIL_OPTIONS)
    if start is not None:
      stmt = stmt.where(Appointment.scheduled_start >= datetime.datetime.combine(start, datetime.time.min))
    if end is not None:
      # end is included: everything before the next day
      next_day = datetime.datetime.combine(end + datetime.timedelta(days=1), datetime.time.min)
      stmt = stmt.where(Appointment.scheduled_start < next_day)
    if patient_id is not None:
      stmt = stmt.where(Appointment.patient_id == patient_id)
    return list(self.session.scalars(stmt.order_by(Appointment.scheduled_start, Appointment.id)))

  def exists_for_encounter(self, encounter_id: int) -> bool:
    stmt = select(Appointment.id).where(Appointment.encounter_id == encounter_id).limit(1)
    return self.session.scalar(stmt) is not None

  def exists_outside(
    self,
    encounter_id: int,
    start: datetime.datetime,
    end: datetime.datetime | None,
  ) -> bool:
    """Check whether any care appointment of the stay falls outside `[start, end]`.

    Args:
      encounter_id (int): Primary key of the encounter.
      start (datetime.datetime): Stay admission timestamp (`scheduled_start` must not precede this).
      end (datetime.datetime | None): Actual discharge timestamp, or `None` if not yet discharged.

    Returns:
      bool: `True` if at least one appointment starts before `start` or ends after `end`.
    """
    outside = Appointment.scheduled_start < start
    if end is not None:
      last = func.coalesce(Appointment.scheduled_end, Appointment.scheduled_start)
      outside = or_(outside, last > end)
    stmt = select(Appointment.id).where(Appointment.encounter_id == encounter_id, outside).limit(1)
    return self.session.scalar(stmt) is not None

  def create(self, appointment: Appointment) -> Appointment:
    self.session.add(appointment)
    self.session.flush()
    return appointment
