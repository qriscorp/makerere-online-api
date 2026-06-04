from datetime import datetime, date

from pydantic import BaseModel


class AssessmentCreate(BaseModel):
    course_unit_id: str
    title: str
    type: str
    pass_mark: int = 50
    time_limit: int | None = None
    max_attempts: int = 1
    start_date: date | None = None
    end_date: date | None = None
    instructions: str = ""


class AssessmentResponse(BaseModel):
    id: str
    course_unit_id: str
    title: str
    type: str
    pass_mark: int
    time_limit: int | None
    max_attempts: int
    start_date: date | None
    end_date: date | None
    instructions: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True
