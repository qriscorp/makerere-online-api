from datetime import datetime, date

from pydantic import BaseModel


class VirtualClassCreate(BaseModel):
    course_unit_id: str
    title: str
    date: date
    start_time: str
    duration: int = 60
    platform: str
    meeting_link: str = ""


class VirtualClassResponse(BaseModel):
    id: str
    course_unit_id: str
    title: str
    date: date
    start_time: str
    duration: int
    platform: str
    meeting_link: str
    is_live: bool
    lecturer_id: str
    created_at: datetime

    class Config:
        from_attributes = True
