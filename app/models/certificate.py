import uuid
import random
import string
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def generate_certificate_number() -> str:
    """Generate a unique certificate number like MAK-2026-X7K9P."""
    year = datetime.utcnow().year
    chars = string.ascii_uppercase + string.digits
    random_part = "".join(random.choices(chars, k=5))
    return f"MAK-{year}-{random_part}"


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    certificate_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "course" or "course_unit"
    course_id: Mapped[str | None] = mapped_column(String, nullable=True)
    course_unit_id: Mapped[str | None] = mapped_column(String, nullable=True)
    certificate_number: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, default=generate_certificate_number
    )
    student_name: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # "active" or "revoked"
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
