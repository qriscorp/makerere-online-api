from datetime import datetime
from pydantic import BaseModel


class SubjectCreate(BaseModel):
    name: str
    description: str = ""


class SubjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class SubjectResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True
