from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate, AssessmentResponse

router = APIRouter(prefix="/api/assessments", tags=["Assessments"])


@router.get("", response_model=List[AssessmentResponse])
def list_assessments(
    course_unit_id: str = Query(..., description="Filter by course unit ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List assessments for a course unit. Any authenticated user can access."""
    assessments = (
        db.query(Assessment)
        .filter(Assessment.course_unit_id == course_unit_id)
        .order_by(Assessment.created_at.desc())
        .all()
    )
    return assessments


@router.post("", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    data: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create an assessment. Only lecturer, admin, or super_admin can create."""
    if current_user.role not in ("super_admin", "admin", "lecturer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    assessment = Assessment(
        course_unit_id=data.course_unit_id,
        title=data.title,
        type=data.type,
        pass_mark=data.pass_mark,
        time_limit=data.time_limit,
        max_attempts=data.max_attempts,
        start_date=data.start_date,
        end_date=data.end_date,
        instructions=data.instructions,
        created_by=current_user.id,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an assessment. Creator or admin can delete."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    if current_user.role not in ("super_admin", "admin") and assessment.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    db.delete(assessment)
    db.commit()
    return None
