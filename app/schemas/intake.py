from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator


class IntakeCreate(BaseModel):
    name: str
    year_level: int = 1
    start_date: date
    end_date: date
    enrollment_deadline: date
    capacity: int = 100
    course_ids: List[str]
    status: str = "active"

    @field_validator("course_ids")
    @classmethod
    def must_have_courses(cls, v):
        if not v or len(v) == 0:
            raise ValueError("An intake must have at least one course")
        return v

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("End date must be after start date")
        return v

    @field_validator("enrollment_deadline")
    @classmethod
    def deadline_before_end(cls, v, info):
        if "end_date" in info.data and v > info.data["end_date"]:
            raise ValueError("Enrollment deadline must be before or on the end date")
        return v


class IntakeUpdate(BaseModel):
    name: Optional[str] = None
    year_level: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    enrollment_deadline: Optional[date] = None
    capacity: Optional[int] = None
    course_ids: Optional[List[str]] = None
    status: Optional[str] = None


class IntakeResponse(BaseModel):
    id: str
    name: str
    year_level: int
    start_date: date
    end_date: date
    enrollment_deadline: date
    capacity: int
    enrolled_count: int
    course_ids: List[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
