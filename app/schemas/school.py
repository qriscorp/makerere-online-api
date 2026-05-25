from datetime import datetime

from pydantic import BaseModel


class SchoolCreate(BaseModel):
    name: str
    code: str
    description: str = ""
    head_of_school: str | None = None
    departments_count: int = 0
    status: str = "active"


class SchoolUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    head_of_school: str | None = None
    departments_count: int | None = None
    status: str | None = None


class SchoolResponse(BaseModel):
    id: str
    name: str
    code: str
    description: str
    head_of_school: str | None
    departments_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
