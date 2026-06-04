import uuid
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    intake_id: Mapped[str] = mapped_column(String, nullable=False)
    course_id: Mapped[str] = mapped_column(String, nullable=False)
    enrollment_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(
        String(30), default="payment_pending"
    )  # payment_pending, active, completed, dropped
    payment_status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, completed, failed
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
