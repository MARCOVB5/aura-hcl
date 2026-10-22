from sqlalchemy.orm import Session
from app.models.pathology import ALLERGY_TYPE_CODE, PathologyType

# reference rows the code relies on (foreign keys point to them).
# temporary: will become an Alembic data migration
PATHOLOGY_TYPES = {
  ALLERGY_TYPE_CODE: "Allergy",
}

def seed_reference_data(session : Session) -> None:
  """Inserts the missing reference rows, safe to run at every startup"""
  for code, label in PATHOLOGY_TYPES.items():
    if session.get(PathologyType, code) is None:
      session.add(PathologyType(code = code, label = label))
  session.commit()
