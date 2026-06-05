from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class CertificateCreate(BaseModel):
    student_id: str
    certificate_type: str  # "course" or "course_unit"
    course_id: Optional[str] = None
    course_unit_id: Optional[str] = None
    student_name: str
    title: str


class CertificateResponse(BaseModel):
    id: str
    student_id: str
    certificate_type: str
    course_id: Optional[str] = None
    course_unit_id: Optional[str] = None
    certificate_number: str
    student_name: str
    title: str
    issue_date: date
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CertificateVerifyResponse(BaseModel):
    valid: bool
    certificate_number: str
    student_name: Optional[str] = None
    title: Optional[str] = None
    certificate_type: Optional[str] = None
    issue_date: Optional[date] = None
    status: Optional[str] = None
