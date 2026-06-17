from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.virtual_class import VirtualClass
from app.schemas.virtual_class import VirtualClassCreate, VirtualClassResponse

router = APIRouter(prefix="/api/virtual-classes", tags=["Virtual Classes"])


@router.get("", response_model=List[VirtualClassResponse])
def list_virtual_classes(
    course_unit_id: str | None = Query(None, description="Filter by course unit ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List virtual classes. Filter by unit, or return role-scoped lists when omitted."""
    from app.models.course_unit import CourseUnit
    from app.models.student_unit_enrollment import StudentUnitEnrollment

    query = db.query(VirtualClass)

    if course_unit_id:
        query = query.filter(VirtualClass.course_unit_id == course_unit_id)
    elif current_user.role == "lecturer":
        query = query.filter(VirtualClass.lecturer_id == current_user.id)
    elif current_user.role == "student":
        unit_ids = [
            ue.course_unit_id
            for ue in db.query(StudentUnitEnrollment)
            .filter(StudentUnitEnrollment.student_id == current_user.id)
            .all()
        ]
        if not unit_ids:
            return []
        query = query.filter(VirtualClass.course_unit_id.in_(unit_ids))

    return query.order_by(VirtualClass.date.desc(), VirtualClass.start_time.desc()).all()


@router.post("", response_model=VirtualClassResponse, status_code=status.HTTP_201_CREATED)
def create_virtual_class(
    data: VirtualClassCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Schedule a virtual class. Only lecturer, admin, or super_admin can create."""
    if current_user.role not in ("super_admin", "admin", "lecturer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    virtual_class = VirtualClass(
        course_unit_id=data.course_unit_id,
        title=data.title,
        date=data.date,
        start_time=data.start_time,
        duration=data.duration,
        platform=data.platform,
        meeting_link=data.meeting_link,
        lecturer_id=current_user.id,
    )
    db.add(virtual_class)
    db.commit()
    db.refresh(virtual_class)
    return virtual_class


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_virtual_class(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a virtual class. Creator or admin can delete."""
    virtual_class = db.query(VirtualClass).filter(VirtualClass.id == class_id).first()
    if not virtual_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Virtual class not found",
        )

    if current_user.role not in ("super_admin", "admin") and virtual_class.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    db.delete(virtual_class)
    db.commit()
    return None
