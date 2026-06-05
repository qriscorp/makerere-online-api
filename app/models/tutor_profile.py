import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Float, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TutorProfile(Base):
    __tablename__ = "tutor_profiles"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    subjects: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    hourly_rate: Mapped[float] = mapped_column(Float, default=50000)
    bio: Mapped[str] = mapped_column(Text, default="")
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    # approval_status: "pending", "approved", "rejected"
    approval_status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
