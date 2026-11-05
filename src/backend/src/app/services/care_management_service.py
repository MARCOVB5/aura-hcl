import datetime

from sqlalchemy.orm import Session

from app.dao.appointment_dao import AppointmentDAO
from app.dao.encounter_dao import EncounterDAO
from app.dao.patient_dao import PatientDAO
from app.dao.reference_dao import ReferenceDAO
from app.errors import AppError, Conflict, NotFound
from app.models.care import Appointment
from app.models.encounter import Encounter
from app.models.practitioner import Practitioner
from app.schemas.Care import AppointmentCreate, AppointmentUpdate


class CareManagementService:
  """Care appointments, and the list of caregivers the care form needs"""

  def __init__(
    self,
    session: Session,
    patients: PatientDAO,
    encounters: EncounterDAO,
    appointments: AppointmentDAO,
    references: ReferenceDAO,
  ):
    self.session = session
    self.patients = patients
    self.encounters = encounters
    self.appointments = appointments
    self.references = references

  # reference list

  def list_practitioners(self) -> list[Practitioner]:
    return self.references.list_practitioners()

  # care appointments

  def list_appointments(
    self,
    start: datetime.date | None,
    end: datetime.date | None,
    patient_id: int | None,
  ) -> list[Appointment]:
    return self.appointments.search(start, end, patient_id)

  def get_appointment(self, appointment_id: int) -> Appointment:
    appointment = self.appointments.get(appointment_id)
    if appointment is None:
      raise NotFound("Appointment not found")
    return appointment

  def _apply(self, appointment: Appointment, data: AppointmentUpdate) -> None:
    """Copies the form's fields onto the appointment, after checking the ids it refers to.
    Related objects are assigned (not only their ids): the session keeps loaded objects
    after a commit (expire_on_commit=False), so a changed id alone would leave them stale."""
    performers = self.references.get_practitioners(data.performer_ids)
    if len(performers) != len(set(data.performer_ids)):
      raise NotFound("Practitioner not found")
    validated_by = None
    if data.validated_by_id is not None:
      found = self.references.get_practitioners([data.validated_by_id])
      if not found:
        raise NotFound("Practitioner not found")
      validated_by = found[0]

    appointment.care_type = data.care_type
    appointment.prescribed_on = data.prescribed_on
    appointment.time_constraint = data.time_constraint
    appointment.scheduled_start = data.scheduled_start
    appointment.scheduled_end = data.scheduled_end
    appointment.performers = performers
    appointment.validated_by = validated_by
    appointment.note = data.note.strip() if data.note and data.note.strip() else None
    appointment.status = data.status

  @staticmethod
  def _check_within_stay(data: AppointmentUpdate, encounter: Encounter) -> None:
    """A care takes place during its stay: from the admission to the discharge, if there is one
    (the expected discharge is only a forecast: it does not limit the care)"""
    last = data.scheduled_end or data.scheduled_start
    if data.scheduled_start < encounter.admission_date:
      raise AppError("Care outside its stay")
    if encounter.actual_discharge_date is not None and last > encounter.actual_discharge_date:
      raise AppError("Care outside its stay")

  def create_appointment(self, data: AppointmentCreate) -> Appointment:
    if self.patients.get(data.patient_id) is None:
      raise NotFound("Patient not found")
    # a care is always attached to the stay in progress: no stay, no care
    encounter = self.encounters.get_current(data.patient_id, datetime.datetime.now())
    if encounter is None:
      raise Conflict("No current stay")
    self._check_within_stay(data, encounter)

    appointment = Appointment(patient_id=data.patient_id, encounter_id=encounter.id)
    self._apply(appointment, data)
    self.appointments.create(appointment)
    self.session.commit()
    return self.get_appointment(appointment.id)

  def update_appointment(self, appointment_id: int, data: AppointmentUpdate) -> Appointment:
    appointment = self.get_appointment(appointment_id)
    self._check_within_stay(data, appointment.encounter)
    self._apply(appointment, data)
    self.session.commit()
    return self.get_appointment(appointment_id)
