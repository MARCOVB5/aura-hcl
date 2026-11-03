import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dao.patient_dao import PATIENT_OPTIONS
from app.models.care import Appointment
from app.models.practitioner import Practitioner

# everything an appointment shows: patient, stay and room, care type, caregivers
_DETAIL_OPTIONS = (
  selectinload(Appointment.patient).options(*PATIENT_OPTIONS),
  selectinload(Appointment.encounter),
  selectinload(Appointment.activity_definition),
  selectinload(Appointment.performers).selectinload(Practitioner.person),
  selectinload(Appointment.validated_by).selectinload(Practitioner.person),
)


class AppointmentDAO:

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

  def create(self, appointment: Appointment) -> Appointment:
    self.session.add(appointment)
    self.session.flush()
    return appointment
