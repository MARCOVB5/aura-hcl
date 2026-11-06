"""Provide shared column types and enum persistence helpers for ORM models.

`ID` standardizes primary and foreign keys as MySQL `BIGINT UNSIGNED` (`0` to
`2**64 - 1`, matching `security.decode_user_id` bounds). `enum_values` configures
SQLAlchemy `Enum` columns to persist each member's string `.value` rather than
its Python identifier.
"""
import enum

from sqlalchemy.dialects.mysql import BIGINT

ID = BIGINT(unsigned = True)

def enum_values(e : type[enum.Enum]) -> list[str]:
  """Extract the string values of an enumeration for database storage.

  Args:
    e (type[enum.Enum]): Enumeration class mapped to a database column.

  Returns:
    list[str]: Underlying member values persisted by SQLAlchemy.
  """
  return [m.value for m in e]
