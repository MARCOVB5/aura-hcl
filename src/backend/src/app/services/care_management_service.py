"""Schedule and update patient care appointments within active hospital stays."""
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
  """Manage care appointments and caregiver reference lists within hospital stays."""

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
    """Copy validated form fields and resolved practitioner objects onto `appointment`.

    Assign related `Practitioner` ORM instances (not only foreign-key IDs) because
    `expire_on_commit=False` keeps loaded objects in memory after commit.

    Args:
      appointment (Appointment): Target appointment instance to mutate.
      data (AppointmentUpdate): Validated care appointment fields and practitioner IDs.

    Raises:
      NotFound: If any ID in `performer_ids` or `validated_by_id` does not exist.
    """
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
    """Validate that the appointment time window falls within the stay's actual bounds.

    `expected_discharge_date` is only a forecast and does not constrain care;
    only `admission_date` and `actual_discharge_date` (when set) bound the care.

    Args:
      data (AppointmentUpdate): Appointment payload containing `scheduled_start` and `scheduled_end`.
      encounter (Encounter): Stay to validate the appointment timestamps against.

    Raises:
      AppError: If the appointment starts before `admission_date` or ends after `actual_discharge_date`.
    """
    last = data.scheduled_end or data.scheduled_start
    if data.scheduled_start < encounter.admission_date:
      raise AppError("Care outside its stay")
    if encounter.actual_discharge_date is not None and last > encounter.actual_discharge_date:
      raise AppError("Care outside its stay")

  def create_appointment(self, data: AppointmentCreate) -> Appointment:
    """Create a care appointment attached to the patient's current active stay.

    Args:
      data (AppointmentCreate): Validated care creation payload including `patient_id`.

    Returns:
      Appointment: Persisted `Appointment` with eager-loaded relationships.

    Raises:
      NotFound: If the patient or any referenced practitioner does not exist.
      Conflict: If the patient has no active stay in progress.
      AppError: If the scheduled time falls outside the active stay's dates.
    """
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
    """Replace all editable fields and practitioner assignments on a care appointment.

    Args:
      appointment_id (int): Primary key of the appointment to update.
      data (AppointmentUpdate): Replacement fields and practitioner IDs.

    Returns:
      Appointment: Updated `Appointment` with eager-loaded relationships.

    Raises:
      NotFound: If the appointment or any referenced practitioner does not exist.
      AppError: If the updated schedule falls outside the appointment's bound stay.
    """
    appointment = self.get_appointment(appointment_id)
    self._check_within_stay(data, appointment.encounter)
    self._apply(appointment, data)
    self.session.commit()
    return self.get_appointment(appointment_id)
