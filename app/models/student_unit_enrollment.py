"""
StudentUnitEnrollment — tracks which course units a student is enrolled in.
Created automatically when a student enrolls in a course.
"""
import uuid
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StudentUnitEnrollment(Base):
    __tablename__ = "student_unit_enrollments"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    enrollment_id: Mapped[str] = mapped_column(String, nullable=False)  # links to parent enrollment
    course_unit_id: Mapped[str] = mapped_column(String, nullable=False)
    course_id: Mapped[str] = mapped_column(String, nullable=False)
    intake_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="active"
    )  # active, completed, dropped
    enrolled_date: Mapped[date] = mapped_column(Date, default=date.today)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
