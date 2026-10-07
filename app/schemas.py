from datetime import date
from typing import Literal
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from pydantic import BaseModel, ConfigDict

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

class ScreeningStatusHistoryResponse(BaseModel):
    id: int
    screening_id: int
    from_status: str | None
    to_status: str
    changed_at: datetime
    # convert the database objects returned by your query into the API’s response format.
   # model_config = ConfigDict(from_attributes=True)