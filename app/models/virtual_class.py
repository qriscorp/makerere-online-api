import uuid
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VirtualClass(Base):
    __tablename__ = "virtual_classes"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    course_unit_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=60)
    platform: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # zoom, jitsi
    meeting_link: Mapped[str] = mapped_column(String(500), default="")
    is_live: Mapped[bool] = mapped_column(Boolean, default=False)
    lecturer_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
