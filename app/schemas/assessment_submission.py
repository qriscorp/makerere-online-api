from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AnswerItem(BaseModel):
    question_id: str
    answer: str


class SubmissionCreate(BaseModel):
    assessment_id: str
    answers: List[AnswerItem]


class GradeSubmission(BaseModel):
    score: float
    feedback: str = ""


class SubmissionResponse(BaseModel):
    id: str
    assessment_id: str
    student_id: str
    answers: List[AnswerItem]
    score: float
    total_marks: int
    is_graded: bool
    graded_by: Optional[str] = None
    feedback: str
    submitted_at: datetime
    graded_at: Optional[datetime] = None

    class Config:
        from_attributes = True
