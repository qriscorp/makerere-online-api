from datetime import datetime
from typing import List

from pydantic import BaseModel


class IntakeUnitAssignmentCreate(BaseModel):
    intake_id: str
    course_unit_id: str
    lecturer_id: str


class IntakeUnitAssignmentBulk(BaseModel):
    """Assign multiple units to an intake at once."""
    intake_id: str
    assignments: List[IntakeUnitAssignmentCreate]


class IntakeUnitAssignmentResponse(BaseModel):
    id: str
    intake_id: str
    course_unit_id: str
    lecturer_id: str
    created_at: datetime

    class Config:
        from_attributes = True
