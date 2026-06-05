from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.intake import Intake
from app.schemas.intake import IntakeCreate, IntakeUpdate, IntakeResponse

router = APIRouter(prefix="/api/intakes", tags=["Intakes"])


def _intake_to_response(intake: Intake) -> dict:
    """Convert an Intake ORM object to a response dict with course_ids as list."""
    data = {
        "id": intake.id,
        "name": intake.name,
        "year_level": intake.year_level,
        "start_date": intake.start_date,
        "end_date": intake.end_date,
        "enrollment_deadline": intake.enrollment_deadline,
        "capacity": intake.capacity,
        "enrolled_count": intake.enrolled_count,
        "course_ids": [cid.strip() for cid in intake.course_ids.split(",") if cid.strip()] if intake.course_ids else [],
        "status": intake.status,
        "created_at": intake.created_at,
    }
    return data


@router.get("", response_model=List[IntakeResponse])
def list_intakes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all intakes. Any authenticated user can access."""
    intakes = db.query(Intake).order_by(Intake.created_at.desc()).all()
    return [_intake_to_response(i) for i in intakes]


@router.get("/public", response_model=List[IntakeResponse])
def list_public_intakes(db: Session = Depends(get_db)):
    """Public endpoint — list active intakes with open enrollment."""
    from datetime import date as date_type
    today = date_type.today()
    intakes = (
        db.query(Intake)
        .filter(Intake.status == "active")
        .filter(Intake.enrollment_deadline >= today)
        .order_by(Intake.start_date.asc())
        .all()
    )
    return [_intake_to_response(i) for i in intakes]


@router.post("", response_model=IntakeResponse, status_code=status.HTTP_201_CREATED)
def create_intake(
    intake_data: IntakeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new intake. Only admin and super_admin can create."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    intake = Intake(
        name=intake_data.name,
        year_level=intake_data.year_level,
        start_date=intake_data.start_date,
        end_date=intake_data.end_date,
        enrollment_deadline=intake_data.enrollment_deadline,
        capacity=intake_data.capacity,
        course_ids=",".join(intake_data.course_ids),
        status=intake_data.status,
    )
    db.add(intake)
    db.commit()
    db.refresh(intake)
    return _intake_to_response(intake)


@router.put("/{intake_id}", response_model=IntakeResponse)
def update_intake(
    intake_id: str,
    intake_data: IntakeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an intake. Only admin and super_admin can update."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    intake = db.query(Intake).filter(Intake.id == intake_id).first()
    if not intake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake not found",
        )

    update_data = intake_data.model_dump(exclude_unset=True)

    # Convert course_ids list to comma-separated string if provided
    if "course_ids" in update_data and update_data["course_ids"] is not None:
        update_data["course_ids"] = ",".join(update_data["course_ids"])

    for field, value in update_data.items():
        setattr(intake, field, value)

    db.commit()
    db.refresh(intake)
    return _intake_to_response(intake)


@router.delete("/{intake_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_intake(
    intake_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an intake. Only super_admin can delete."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admin can delete intakes",
        )

    intake = db.query(Intake).filter(Intake.id == intake_id).first()
    if not intake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake not found",
        )

    db.delete(intake)
    db.commit()
    return None
