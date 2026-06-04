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
    course_unit_id: str = Query(..., description="Filter by course unit ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List virtual classes for a course unit. Any authenticated user can access."""
    classes = (
        db.query(VirtualClass)
        .filter(VirtualClass.course_unit_id == course_unit_id)
        .order_by(VirtualClass.date.desc(), VirtualClass.start_time.desc())
        .all()
    )
    return classes


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
