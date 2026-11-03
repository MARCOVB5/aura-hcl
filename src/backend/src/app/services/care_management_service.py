import datetime

from sqlalchemy.orm import Session

from app.dao.appointment_dao import AppointmentDAO
from app.dao.encounter_dao import EncounterDAO
from app.dao.patient_dao import PatientDAO
from app.dao.reference_dao import ReferenceDAO
from app.errors import Conflict, NotFound
from app.models.care import ActivityDefinition, Appointment
from app.models.location import Location
from app.models.practitioner import Practitioner
from app.schemas.Care import AppointmentCreate, AppointmentUpdate


class CareManagementService:
  """Care appointments, and the reference lists the care and stay forms need"""

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

  # reference lists

  def list_locations(self) -> list[Location]:
    return self.references.list_locations()

  def list_care_types(self) -> list[ActivityDefinition]:
    return self.references.list_care_types()

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
    care_type = self.references.get_care_type(data.activity_definition_id)
    if care_type is None:
      raise NotFound("Care type not found")
    performers = self.references.get_practitioners(data.performer_ids)
    if len(performers) != len(set(data.performer_ids)):
      raise NotFound("Practitioner not found")
    validated_by = None
    if data.validated_by_id is not None:
      found = self.references.get_practitioners([data.validated_by_id])
      if not found:
        raise NotFound("Practitioner not found")
      validated_by = found[0]

    appointment.activity_definition = care_type
    appointment.prescribed_on = data.prescribed_on
    appointment.time_constraint = data.time_constraint
    appointment.scheduled_start = data.scheduled_start
    appointment.scheduled_end = data.scheduled_end
    appointment.performers = performers
    appointment.validated_by = validated_by
    appointment.note = data.note.strip() if data.note and data.note.strip() else None
    appointment.status = data.status

  def create_appointment(self, data: AppointmentCreate) -> Appointment:
    if self.patients.get(data.patient_id) is None:
      raise NotFound("Patient not found")
    # a care is always attached to the stay in progress: no stay, no care
    encounter = self.encounters.get_current(data.patient_id, datetime.datetime.now())
    if encounter is None:
      raise Conflict("No current stay")

    appointment = Appointment(patient_id=data.patient_id, encounter_id=encounter.id)
    self._apply(appointment, data)
    self.appointments.create(appointment)
    self.session.commit()
    return self.get_appointment(appointment.id)

  def update_appointment(self, appointment_id: int, data: AppointmentUpdate) -> Appointment:
    appointment = self.get_appointment(appointment_id)
    self._apply(appointment, data)
    self.session.commit()
    return self.get_appointment(appointment_id)
