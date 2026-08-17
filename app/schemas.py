from datetime import date

from pydantic import BaseModel, EmailStr, ConfigDict

class PatientCreate(BaseModel):
    full_name: str
    date_of_birth: date
    email: EmailStr

class PatientResponse(PatientCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)