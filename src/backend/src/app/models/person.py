from __future__ import annotations

import datetime
from app.models import Base
from app.models.common import ID, enum_values

from sqlalchemy import String, Enum, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

import enum

'''
Enumeration / DataType classes for the Person group
'''

class ContactPointSystem(enum.Enum):
  PHONE = "PHONE"
  FAX = "FAX"
  EMAIL = "EMAIL"
  PAGER = "PAGER" #IS THIS ONE NECESSARY???
  URL = "URL"
  SMS = "SMS"
  OTHER = "OTHER"

class AdministrativeGender(enum.Enum):
  MALE = "male"
  FEMALE = "female"
  OTHER = "other"
  UNKNOWN = "unknown" #dont cancel me

class ContactPoint(Base):
  __tablename__ = "contact_point"

  id : Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
  system : Mapped[ContactPointSystem] = mapped_column(Enum(ContactPointSystem, values_callable = enum_values))
  value : Mapped[str] = mapped_column(String(128))
  person_id : Mapped[int] = mapped_column(ID, ForeignKey("person.id"))
  person : Mapped[Person] = relationship(back_populates="telecom")

class Person(Base):
  __tablename__ = "person"

  id : Mapped[int] = mapped_column(ID, primary_key=True, autoincrement = True)
  name_family : Mapped[str | None] = mapped_column(String(128))
  name_given : Mapped[str | None] = mapped_column(String(128))
  birthDate : Mapped[datetime.date | None] = mapped_column(Date)
  gender : Mapped[AdministrativeGender | None] = mapped_column(Enum(AdministrativeGender, values_callable = enum_values))
  address_line : Mapped[str | None] = mapped_column(String(255)) #check if it's necessary to put the whole address obj

  telecom : Mapped[list[ContactPoint]] = relationship(
    back_populates="person",
    cascade="all, delete-orphan",
  )
