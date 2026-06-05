from datetime import date, datetime

from pydantic import BaseModel
from typing import List, Optional


class TutorProfileCreate(BaseModel):
    subjects: List[str] = []
    hourly_rate: float = 50000
    bio: str = ""
    is_available: bool = True


class TutorProfileResponse(BaseModel):
    id: str
    user_id: str
    subjects: List[str]
    hourly_rate: float
    bio: str
    is_available: bool
    approval_status: str = "pending"

    class Config:
        from_attributes = True


class TutorPublicResponse(BaseModel):
    id: str
    name: str  # from user
    subjects: List[str]
    hourly_rate: float
    bio: str
    is_available: bool


class TutorAdminResponse(BaseModel):
    """Response for admin view — includes user name and approval status."""
    id: str
    user_id: str
    name: str
    subjects: List[str]
    hourly_rate: float
    bio: str
    is_available: bool
    approval_status: str
    created_at: Optional[str] = None


class TutoringBookingCreate(BaseModel):
    tutor_profile_id: str
    subject: str
    date: date
    time_slot: str
    duration: int = 1


class TutoringBookingResponse(BaseModel):
    id: str
    student_id: str
    tutor_profile_id: str
    subject: str
    date: date
    time_slot: str
    duration: int
    total_cost: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
