from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel

NotificationCategory = Literal["enrollment", "payment", "class", "exam"]


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    category: NotificationCategory
    is_read: bool
    link_to: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    count: int


class ExamDeadlineAlert(BaseModel):
    id: str
    title: str
    hours_left: int
    course_unit_id: str


class UpcomingClassAlert(BaseModel):
    id: str
    title: str
    minutes_left: int
    course_unit_id: str


class UpcomingAlertsResponse(BaseModel):
    exam_deadlines: List[ExamDeadlineAlert]
    upcoming_classes: List[UpcomingClassAlert]
