"""Provide read-only queries for practitioner reference lists and ID resolution."""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.practitioner import Practitioner


class ReferenceDAO:
  """Load active practitioners for UI reference lists and resolve practitioner IDs.

  `list_practitioners` filters for `active=True` and eager-loads `person`, while
  `get_practitioners` resolves arbitrary ID lists regardless of `active` status.
  """

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
