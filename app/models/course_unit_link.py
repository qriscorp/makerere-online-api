"""
CourseUnitLink — many-to-many junction between courses and course units.
A course unit can belong to multiple courses, and a course can have multiple units.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CourseUnitLink(Base):
    __tablename__ = "course_unit_links"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    course_id: Mapped[str] = mapped_column(String, nullable=False)
    course_unit_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
