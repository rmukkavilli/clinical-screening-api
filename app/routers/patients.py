from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient
from app.schemas import PatientCreate, PatientResponse


router = APIRouter(
    prefix="/patients",
    tags=["patients"],
)


@router.post(
    "",
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


@router.get(
    "",
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
       
@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient_by_id(patient_id: int, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail=f"{patient_id} not found")
    return patient

@router.get("/by-name/{patient_name}", response_model=PatientResponse)
def get_patient_by_name(patient_name: str, db: Session = Depends(get_db)):
    query = select(Patient).where(Patient.full_name.ilike(patient_name))
    patient = db.scalars(query).first()

    if patient is None:
        raise HTTPException(status_code=404, detail=f"{patient_name} not found")
    return patient