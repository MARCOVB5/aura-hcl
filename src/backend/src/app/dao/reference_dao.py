from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.practitioner import Practitioner


class ReferenceDAO:
  """Read-only list used by the forms: caregivers"""

  def __init__(self, session: Session):
    self.session = session

  def list_practitioners(self) -> list[Practitioner]:
    stmt = (
      select(Practitioner)
      .options(selectinload(Practitioner.person))
      .where(Practitioner.active.is_(True))
      .order_by(Practitioner.id)
    )
    return list(self.session.scalars(stmt))

  def get_practitioners(self, ids: list[int]) -> list[Practitioner]:
    if not ids:
      return []
    stmt = select(Practitioner).where(Practitioner.id.in_(ids)).order_by(Practitioner.id)
    return list(self.session.scalars(stmt))
