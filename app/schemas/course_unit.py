from datetime import datetime

from pydantic import BaseModel


class CourseUnitCreate(BaseModel):
    title: str
    description: str = ""
    course_id: str | None = None  # Optional — units can be independent
    lecturer_id: str | None = None
    credit_hours: int = 3
    status: str = "active"


class CourseUnitUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    course_id: str | None = None
    lecturer_id: str | None = None
    credit_hours: int | None = None
    status: str | None = None


class CourseUnitResponse(BaseModel):
    id: str
    title: str
    description: str
    course_id: str | None
    lecturer_id: str | None
    credit_hours: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
