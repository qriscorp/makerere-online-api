from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.course_unit import CourseUnit
from app.schemas.course_unit import CourseUnitCreate, CourseUnitUpdate, CourseUnitResponse

router = APIRouter(prefix="/api/course-units", tags=["Course Units"])


@router.get("", response_model=List[CourseUnitResponse])
def list_course_units(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all course units. Any authenticated user can access."""
    units = db.query(CourseUnit).order_by(CourseUnit.created_at.desc()).all()
    return units


@router.post("", response_model=CourseUnitResponse, status_code=status.HTTP_201_CREATED)
def create_course_unit(
    unit_data: CourseUnitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new course unit.
    - admin/super_admin: status defaults to 'active'
    - lecturer: status is forced to 'pending_approval', lecturer_id is set to current user
    """
    if current_user.role not in ("super_admin", "admin", "lecturer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Determine status and lecturer based on role
    if current_user.role == "lecturer":
        unit_status = "pending_approval"
        lecturer_id = current_user.id
    else:
        unit_status = unit_data.status if unit_data.status else "active"
        lecturer_id = unit_data.lecturer_id

    unit = CourseUnit(
        title=unit_data.title,
        description=unit_data.description,
        course_id=unit_data.course_id,
        lecturer_id=lecturer_id,
        credit_hours=unit_data.credit_hours,
        status=unit_status,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


@router.put("/{unit_id}", response_model=CourseUnitResponse)
def update_course_unit(
    unit_id: str,
    unit_data: CourseUnitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a course unit. Only admin and super_admin can update."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    unit = db.query(CourseUnit).filter(CourseUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course unit not found",
        )

    update_data = unit_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(unit, field, value)

    db.commit()
    db.refresh(unit)
    return unit


@router.put("/{unit_id}/approve", response_model=CourseUnitResponse)
def approve_course_unit(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve a course unit. Only admin and super_admin can approve."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    unit = db.query(CourseUnit).filter(CourseUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course unit not found",
        )

    unit.status = "active"
    db.commit()
    db.refresh(unit)
    return unit


@router.put("/{unit_id}/reject", response_model=CourseUnitResponse)
def reject_course_unit(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reject a course unit. Only admin and super_admin can reject."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    unit = db.query(CourseUnit).filter(CourseUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course unit not found",
        )

    unit.status = "rejected"
    db.commit()
    db.refresh(unit)
    return unit


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course_unit(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a course unit. Only super_admin can delete."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admin can delete course units",
        )

    unit = db.query(CourseUnit).filter(CourseUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course unit not found",
        )

    db.delete(unit)
    db.commit()
    return None
