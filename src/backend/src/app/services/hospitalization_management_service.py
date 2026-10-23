from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dao.encounter_dao import EncounterDAO
from app.dao.hospitalization_dao import HospitalizationDAO
from app.dao.patient_dao import PatientDAO
from app.errors import Conflict, NotFound
from app.models.encounter import Encounter
from app.models.hospitalization import Hospitalization
from app.schemas.Hospitalization import HospitalizationCreate


class HospitalizationManagementService:

  def __init__(
    self,
    session: Session,
    patients: PatientDAO,
    encounters: EncounterDAO,
    hospitalizations: HospitalizationDAO,
  ):
    self.session = session
    self.patients = patients
    self.encounters = encounters
    self.hospitalizations = hospitalizations

  def create_hospitalization(self, data: HospitalizationCreate) -> Hospitalization:
    patient = self.patients.get(data.encounter.patient_id)
    if patient is None:
      raise NotFound("Patient not found")

    try:
      encounter = self.encounters.create(Encounter(
        patient=patient,
        **data.encounter.model_dump(exclude={"patient_id"}),
      ))
      hospitalization = self.hospitalizations.create(Hospitalization(
        encounter=encounter,
      ))
      self.session.commit()
    except IntegrityError:
      self.session.rollback()
      if self.encounters.get_by_stay_number(data.encounter.stay_number):
        raise Conflict("Stay number already registered")
      raise
    except Exception:
      self.session.rollback()
      raise

    return hospitalization

  def list_hospitalizations(self, limit: int) -> list[Hospitalization]:
    return self.hospitalizations.list_all(limit)

  def get_hospitalization(self, encounter_id: int) -> Hospitalization:
    hospitalization = self.hospitalizations.get(encounter_id)
    if hospitalization is None:
      raise NotFound("Hospitalization not found")
    return hospitalization

  def get_hospitalization_by_patient(self, patient_id: int) -> list[Hospitalization]:
    if self.patients.get(patient_id) is None:
      raise NotFound("Patient not found")
    return self.hospitalizations.get_by_patient(patient_id)
