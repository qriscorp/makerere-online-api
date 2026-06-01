"""
IntakeUnitAssignment — maps a course unit to a specific intake with a specific lecturer.
This is the central scoping entity: all content (materials, classes, exams) for a course
unit within a specific intake is linked through this assignment.

Example:
- "Data Structures" in "Jan 2026 Intake (Year 1)" taught by Dr. Okello
  → has its own materials, virtual classes, and exams
- "Data Structures" in "Sep 2026 Intake (Year 2)" taught by Prof. Mugisha
  → has completely different materials, classes, and exams
"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IntakeUnitAssignment(Base):
    __tablename__ = "intake_unit_assignments"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    intake_id: Mapped[str] = mapped_column(String, nullable=False)
    course_unit_id: Mapped[str] = mapped_column(String, nullable=False)
    lecturer_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
