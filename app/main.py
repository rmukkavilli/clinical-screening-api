from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import Patient, Screening
from fastapi import FastAPI,status, HTTPException
from sqlalchemy.exc import IntegrityError
from app.routers import patients, screenings
 
from app.schemas import (
    PatientCreate,
    PatientResponse,
    ScreeningCreate,
    ScreeningResponse,
    ScreeningStatusUpdate,
)
app = FastAPI()

app.include_router(patients.router)
app.include_router(screenings.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}