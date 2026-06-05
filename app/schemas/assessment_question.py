from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class QuestionCreate(BaseModel):
    assessment_id: str
    question_text: str
    question_type: str = "mcq"  # mcq or essay
    options: List[str] = []  # for MCQ
    correct_answer: str = ""  # for MCQ
    marks: int = 1
    order: int = 0


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    marks: Optional[int] = None
    order: Optional[int] = None


class QuestionResponse(BaseModel):
    id: str
    assessment_id: str
    question_text: str
    question_type: str
    options: List[str]
    correct_answer: str
    marks: int
    order: int
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionStudentResponse(BaseModel):
    """Response for students — hides correct_answer."""
    id: str
    assessment_id: str
    question_text: str
    question_type: str
    options: List[str]
    marks: int
    order: int
