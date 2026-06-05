"""
AssessmentSubmission — a student's attempt at an assessment.
Contains answers as JSON and the score (auto-graded for quiz, manual for essay).
"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Text, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AssessmentSubmission(Base):
    __tablename__ = "assessment_submissions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    assessment_id: Mapped[str] = mapped_column(String, nullable=False)
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    # answers stored as JSON: [{"question_id": "...", "answer": "A"}, ...]
    answers: Mapped[str] = mapped_column(Text, default="[]")
    score: Mapped[float] = mapped_column(Float, default=0)
    total_marks: Mapped[int] = mapped_column(Integer, default=0)
    is_graded: Mapped[bool] = mapped_column(Boolean, default=False)
    # For auto-graded quizzes, graded_by is "system"; for essays, it's the lecturer ID
    graded_by: Mapped[str | None] = mapped_column(String, nullable=True)
    feedback: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    graded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
