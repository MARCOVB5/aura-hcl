from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dao.encounter_dao import EncounterDAO
from app.dao.hospitalization_dao import HospitalizationDAO
from app.dao.patient_dao import PatientDAO
from app.errors import Conflict
from app.models.encounter import Encounter
from app.models.hospitalization import Hospitalization
from app.schemas.Hospitalization import HospitalizationCreate
from app.services.patient_management_service import build_patient


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
    patient_data = data.encounter.patient

    try:
      patient = self.patients.create(build_patient(patient_data))
      encounter = self.encounters.create(Encounter(
        patient=patient,
        **data.encounter.model_dump(exclude={"patient"}),
      ))
      hospitalization = self.hospitalizations.create(Hospitalization(
        encounter=encounter,
      ))
      self.session.commit()
    except IntegrityError:
      self.session.rollback()
      if patient_data.ipp is not None and self.patients.get_by_ipp(patient_data.ipp):
        raise Conflict("IPP already registered")
      if self.encounters.get_by_stay_number(data.encounter.stay_number):
        raise Conflict("Stay number already registered")
      raise
    except Exception:
      self.session.rollback()
      raise

    # The filtered allergies relationship is view-only; reload it after insertion.
    self.session.refresh(patient, ["allergies"])
    return hospitalization
