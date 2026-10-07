from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient, Screening
from app.models import Patient, Screening, ScreeningStatusHistory

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.schemas import (
    ScreeningCreate,
    ScreeningResponse,
    ScreeningStatusUpdate,
    ScreeningStatusHistoryResponse,
)

router = APIRouter(
    prefix="/screenings",
    tags=["screenings"],
)

ALLOWED_STATUS_TRANSITIONS = {
    "scheduled": {"in_progress"},
    "in_progress": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
}

@router.post(
    "",
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

    try:
        db.add(db_screening)
        db.flush()
        # We will add the history entry here, before the commit.
        db_history = ScreeningStatusHistory(
        screening_id=db_screening.id,
        from_status=None,
        to_status=db_screening.status,
        )

        db.add(db_history)
        db.commit()
        
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to create screening")

    db.refresh(db_screening)
    return db_screening

@router.get(
    "/{screening_id}",
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

@router.patch(
    "/{screening_id}/status",
    response_model=ScreeningResponse,
)
def update_screening_status(
    screening_id: int,
    status_update: ScreeningStatusUpdate,
    db: Session = Depends(get_db),
):
    screening = db.get(Screening, screening_id)

    if screening is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{screening_id} not found",
        )

    allowed_next_statuses = ALLOWED_STATUS_TRANSITIONS[
        screening.status
    ]

    if status_update.status not in allowed_next_statuses:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot change status from "
                    f"{screening.status} to {status_update.status}"
                ),
            )
    previous_status = screening.status       # Remember "scheduled".
    try:
        screening.status = status_update.status  # Change to "in_progress".
        db_history = ScreeningStatusHistory(
        screening_id=screening.id,  # Which screening changed?
        from_status=previous_status,  # What was its status before?
        to_status=screening.status,   # What is its status now?
        )

        db.add(db_history)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to update screening status",
        )

    db.refresh(screening)
    return screening
    
@router.get(
    "",
    response_model=list[ScreeningResponse],
)
def get_screenings(
    patient_id: int | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Screening)

    if patient_id is not None:
        query = query.where(
            Screening.patient_id == patient_id
        )

    if status_filter is not None:
        query = query.where(
            Screening.status == status_filter
        )

    return db.scalars(query).all()


@router.get(
"/{screening_id}/history",
response_model=list[ScreeningStatusHistoryResponse],
)
def get_history_screening(
    screening_id: int,
    db: Session = Depends(get_db),
):
    
    screening = db.get(Screening, screening_id)

    if screening is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{screening_id} not found",
        )
    statement = (select(ScreeningStatusHistory)
    .where(ScreeningStatusHistory.screening_id == screening_id)
    .order_by(ScreeningStatusHistory.changed_at, 
            ScreeningStatusHistory.id
        )
    )
    
    screening_history = db.scalars(statement).all()
    return screening_history