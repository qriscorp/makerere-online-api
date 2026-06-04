import uuid
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TutoringBooking(Base):
    __tablename__ = "tutoring_bookings"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    tutor_profile_id: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time_slot: Mapped[str] = mapped_column(String(10), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=1)
    total_cost: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(
        String(20), default="upcoming"
    )  # upcoming, completed, cancelled
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
