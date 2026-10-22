from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.encounter import Encounter


class EncounterDAO:

  def __init__(self, session: Session):
    self.session = session

  def get(self, id: int) -> Encounter | None:
    return self.session.get(Encounter, id)

  def get_by_stay_number(self, stay_number: str) -> Encounter | None:
    stmt = select(Encounter).where(Encounter.stay_number == stay_number)
    return self.session.scalar(stmt)

  def create(self, encounter: Encounter) -> Encounter:
    self.session.add(encounter)
    self.session.flush()
    return encounter
