from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

# --- Patient Schemas ---
class PatientBase(BaseModel):
    name: str = Field(..., description="Name of the patient")
    city: str = Field(..., description="City of the patient")
    age: int = Field(..., gt=0, lt=120, description="Age of the patient")
    gender: Literal['male', 'female', 'other'] = Field(..., description="Gender of the patient")
    height: float = Field(..., gt=0, description="Height in Meters")
    weight: float = Field(..., gt=0, description="Weight in Kgs")
    medical_notes: Optional[str] = "No notes recorded."

class PatientCreate(PatientBase):
    id: str = Field(..., description="Unique ID for the patient", examples=['P001'])

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    age: Optional[int] = Field(None, gt=0, lt=120)
    gender: Optional[Literal['male', 'female', 'other']] = None
    height: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    medical_notes: Optional[str] = None

class PatientResponse(PatientBase):
    id: str
    bmi: float
    verdict: str
    updated_at: datetime

    class Config:
        from_attributes = True

    @staticmethod
    def calculate_bmi(weight: float, height: float) -> float:
        return round(weight / (height ** 2), 2)

    @staticmethod
    def get_verdict(bmi: float) -> str:
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"
