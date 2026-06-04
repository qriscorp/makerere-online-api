import uuid
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    course_unit_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # quiz, assignment, final_exam
    pass_mark: Mapped[int] = mapped_column(Integer, default=50)
    time_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    instructions: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
