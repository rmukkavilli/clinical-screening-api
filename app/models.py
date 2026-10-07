from datetime import date
from sqlalchemy import func

from sqlalchemy import Date, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )


class Screening(Base):
    __tablename__ = "screenings"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="scheduled",
    )

class ScreeningStatusHistory(Base):
    __tablename__ = "screening_status_history"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    screening_id: Mapped[int] = mapped_column(
        ForeignKey("screenings.id"),
        nullable=False,
    )

    from_status: Mapped[str|None] = mapped_column(
        String(50),
        nullable=True,
    )

    to_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,       
    )

    changed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )