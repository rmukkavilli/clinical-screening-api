from datetime import date
from typing import Literal
from pydantic import BaseModel, EmailStr, ConfigDict

class PatientCreate(BaseModel):
    full_name: str
    date_of_birth: date
    email: EmailStr

class PatientResponse(PatientCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ScreeningCreate(BaseModel):
    patient_id: int


class ScreeningResponse(ScreeningCreate):
    id: int
    status: str

    model_config = ConfigDict(from_attributes=True)

class ScreeningStatusUpdate(BaseModel):
    status: Literal[
        "scheduled",
        "in_progress",
        "completed",
        "failed",
    ]