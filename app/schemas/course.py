from datetime import datetime
from typing import List

from pydantic import BaseModel, field_validator


class CourseCreate(BaseModel):
    title: str
    description: str = ""
    school_id: str
    duration: int = 12
    duration_unit: str = "months"
    fee: float = 0
    pass_mark: int = 50
    status: str = "active"
    unit_ids: List[str] = []  # Must have at least one course unit

    @field_validator("unit_ids")
    @classmethod
    def must_have_units(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError("A course must have at least one course unit")
        return v


class CourseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    school_id: str | None = None
    duration: int | None = None
    duration_unit: str | None = None
    fee: float | None = None
    pass_mark: int | None = None
    status: str | None = None
    unit_ids: List[str] | None = None


class CourseResponse(BaseModel):
    id: str
    title: str
    description: str
    school_id: str
    duration: int
    duration_unit: str
    fee: float
    pass_mark: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
