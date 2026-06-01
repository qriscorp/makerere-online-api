import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CourseUnit(Base):
    __tablename__ = "course_units"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True, default="")
    course_id: Mapped[str | None] = mapped_column(String, nullable=True)  # Deprecated: use course_unit_links table instead
    lecturer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    credit_hours: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[str] = mapped_column(
        String(30), default="active"
    )  # active, pending_approval, rejected
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
