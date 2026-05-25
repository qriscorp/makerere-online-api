from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.school import School
from app.schemas.school import SchoolCreate, SchoolUpdate, SchoolResponse

router = APIRouter(prefix="/api/schools", tags=["Schools"])


@router.get("", response_model=List[SchoolResponse])
def list_schools(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all schools. Only admin and super_admin can access."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    schools = db.query(School).order_by(School.created_at.desc()).all()
    return schools


@router.post("", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
def create_school(
    school_data: SchoolCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new school. Only admin and super_admin can create."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Check if code already exists
    existing = db.query(School).filter(School.code == school_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School code already exists",
        )

    school = School(
        name=school_data.name,
        code=school_data.code,
        description=school_data.description,
        head_of_school=school_data.head_of_school,
        departments_count=school_data.departments_count,
        status=school_data.status,
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


@router.put("/{school_id}", response_model=SchoolResponse)
def update_school(
    school_id: str,
    school_data: SchoolUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a school. Only admin and super_admin can update."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    # Check code uniqueness if code is being changed
    if school_data.code is not None and school_data.code != school.code:
        existing = db.query(School).filter(School.code == school_data.code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="School code already exists",
            )

    update_data = school_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(school, field, value)

    db.commit()
    db.refresh(school)
    return school


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(
    school_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a school. Only super_admin can delete."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admin can delete schools",
        )

    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    db.delete(school)
    db.commit()
    return None
