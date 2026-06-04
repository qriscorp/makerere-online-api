from datetime import datetime

from pydantic import BaseModel


class StudyMaterialCreate(BaseModel):
    course_unit_id: str
    title: str
    description: str = ""
    type: str
    file_url: str = ""
    file_size: int = 0


class StudyMaterialResponse(BaseModel):
    id: str
    course_unit_id: str
    title: str
    description: str
    type: str
    file_url: str
    file_size: int
    uploaded_by: str
    created_at: datetime

    class Config:
        from_attributes = True
