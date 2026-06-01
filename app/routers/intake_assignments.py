"""
Router for managing lecturer assignments to course units within specific intakes.
This allows the same course unit to have different lecturers in different intakes.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.intake_unit_assignment import IntakeUnitAssignment
from app.schemas.intake_unit_assignment import (
    IntakeUnitAssignmentCreate,
    IntakeUnitAssignmentResponse,
)

router = APIRouter(prefix="/api/intake-assignments", tags=["Intake Assignments"])


@router.get("", response_model=List[IntakeUnitAssignmentResponse])
def list_assignments(
    intake_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List assignments. Optionally filter by intake_id query param."""
    query = db.query(IntakeUnitAssignment)
    if intake_id:
        query = query.filter(IntakeUnitAssignment.intake_id == intake_id)
    return query.order_by(IntakeUnitAssignment.created_at.desc()).all()


@router.post("", response_model=IntakeUnitAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    data: IntakeUnitAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assign a lecturer to a course unit for a specific intake. Admin/super_admin only."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Check if this exact assignment already exists
    existing = (
        db.query(IntakeUnitAssignment)
        .filter(
            IntakeUnitAssignment.intake_id == data.intake_id,
            IntakeUnitAssignment.course_unit_id == data.course_unit_id,
        )
        .first()
    )
    if existing:
        # Update the lecturer instead of creating duplicate
        existing.lecturer_id = data.lecturer_id
        db.commit()
        db.refresh(existing)
        return existing

    assignment = IntakeUnitAssignment(
        intake_id=data.intake_id,
        course_unit_id=data.course_unit_id,
        lecturer_id=data.lecturer_id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a lecturer assignment. Admin/super_admin only."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    assignment = (
        db.query(IntakeUnitAssignment)
        .filter(IntakeUnitAssignment.id == assignment_id)
        .first()
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    db.delete(assignment)
    db.commit()
    return None
