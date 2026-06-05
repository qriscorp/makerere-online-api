"""Payment model — tracks all payment transactions in the system."""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Float, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    enrollment_id: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="UGX")
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    carrier: Mapped[str] = mapped_column(String(20), nullable=False)  # mtn, airtel
    payment_type: Mapped[str] = mapped_column(
        String(30), default="enrollment"
    )  # enrollment, tuition, tutoring
    status: Mapped[str] = mapped_column(
        String(30), default="pending"
    )  # pending, processing, completed, failed
    request_reference: Mapped[str] = mapped_column(String(128), nullable=True)
    vendor_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    response_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    response_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
