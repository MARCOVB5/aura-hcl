import enum

from sqlalchemy.dialects.mysql import BIGINT

'''
Common types / helpers shared by the models
'''

ID = BIGINT(unsigned = True)

def enum_values(e : type[enum.Enum]) -> list[str]:
  """Store the enum's valeus in the DB"""
  return [m.value for m in e]
