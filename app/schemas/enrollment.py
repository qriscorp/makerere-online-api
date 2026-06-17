from datetime import date, datetime

from pydantic import BaseModel


class EnrollmentCreate(BaseModel):
    intake_id: str
    course_id: str


class EnrollmentResponse(BaseModel):
    id: str
    student_id: str
    intake_id: str
    course_id: str
    enrollment_date: date
    status: str
    payment_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class EnrollmentUpdate(BaseModel):
    status: str | None = None
    payment_status: str | None = None
