from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    patients = relationship("Patient", back_populates="doctor")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    city = Column(String)
    age = Column(Integer)
    gender = Column(String)
    height = Column(Float)
    weight = Column(Float)
    bmi = Column(Float)
    verdict = Column(String)
    medical_notes = Column(String, default="No notes recorded.")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())

    doctor = relationship("User", back_populates="patients")
