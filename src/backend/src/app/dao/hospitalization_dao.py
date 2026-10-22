from sqlalchemy.orm import Session

from app.models.hospitalization import Hospitalization


class HospitalizationDAO:

  def __init__(self, session: Session):
    self.session = session

  def get(self, encounter_id: int) -> Hospitalization | None:
    return self.session.get(Hospitalization, encounter_id)

  def create(self, hospitalization: Hospitalization) -> Hospitalization:
    self.session.add(hospitalization)
    self.session.flush()
    return hospitalization
