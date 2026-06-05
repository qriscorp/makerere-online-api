import uuid
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Intake(Base):
    __tablename__ = "intakes"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    year_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    enrollment_deadline: Mapped[date] = mapped_column(Date, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=100)
    enrolled_count: Mapped[int] = mapped_column(Integer, default=0)
    fee: Mapped[float] = mapped_column(Float, default=0)  # kept for backward compat, not used
    course_ids: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
