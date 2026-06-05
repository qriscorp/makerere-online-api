"""
AssessmentQuestion — stores questions for an assessment.
For quiz type: has options (JSON array) and correct_answer.
For essay type: just the question text.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    assessment_id: Mapped[str] = mapped_column(String, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="mcq"
    )  # mcq, essay
    options: Mapped[str] = mapped_column(
        Text, default="[]"
    )  # JSON array of options for MCQ e.g. ["A", "B", "C", "D"]
    correct_answer: Mapped[str] = mapped_column(
        Text, default=""
    )  # correct option for MCQ (e.g. "A")
    marks: Mapped[int] = mapped_column(Integer, default=1)  # marks for this question
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
