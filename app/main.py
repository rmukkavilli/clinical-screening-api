from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import Patient, Screening
from fastapi import FastAPI,status, HTTPException
from sqlalchemy.exc import IntegrityError
from app.schemas import (
    PatientCreate,
    PatientResponse,
    ScreeningCreate,
    ScreeningResponse,
)
app = FastAPI()
patients = []
default_patinets =  [
  {
    "full_name": "not patient",
    "date_of_birth": "2026-08-16",
    "email": "not a email",
    "id": -1
  }
]

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post(
    "/patients",
    status_code=status.HTTP_201_CREATED,
    response_model=PatientResponse,
)
def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
):
    db_patient = Patient(
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        email=patient.email,
    )

    try:
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient with this email already exists",
        )

    return db_patient


@app.get(
    "/patients",
    response_model=list[PatientResponse],
)
def get_patients(
    name: str | None = None,
    email: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Patient)

    if name:
        query = query.where(
            Patient.full_name.ilike(name)
        )

    if email:
        query = query.where(
            Patient.email.ilike(email)
        )

    return db.scalars(query).all()
       
@app.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient_by_id(patient_id: int, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail=f"{patient_id} not found")
    return patient

@app.get("/patients/by-name/{patient_name}", response_model=PatientResponse)
def get_patient_by_name(patient_name: str, db: Session = Depends(get_db)):
    query = select(Patient).where(Patient.full_name.ilike(patient_name))
    patient = db.scalars(query).first()

    if patient is None:
        raise HTTPException(status_code=404, detail=f"{patient_name} not found")
    return patient

@app.post(
    "/screenings",
    status_code=status.HTTP_201_CREATED,
    response_model=ScreeningResponse,
)
def create_screening(
    screening: ScreeningCreate,
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, screening.patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    db_screening = Screening(
        patient_id=screening.patient_id,
    )

    db.add(db_screening)
    db.commit()
    db.refresh(db_screening)

    return db_screening

@app.get(
    "/screenings/{screening_id}",
    response_model=ScreeningResponse,
)
def get_screening_by_id(
    screening_id: int,
    db: Session = Depends(get_db),
):
    screening = db.get(Screening, screening_id)

    if screening is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{screening_id} not found",
        )

    return screening