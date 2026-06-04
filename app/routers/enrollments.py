from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.enrollment import Enrollment
from app.models.intake import Intake
from app.schemas.enrollment import EnrollmentCreate, EnrollmentResponse

router = APIRouter(prefix="/api/enrollments", tags=["Enrollments"])


@router.get("", response_model=List[EnrollmentResponse])
def list_enrollments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List enrollments. Students see only their own; admins see all."""
    if current_user.role in ("super_admin", "admin"):
        enrollments = db.query(Enrollment).order_by(Enrollment.created_at.desc()).all()
    else:
        enrollments = (
            db.query(Enrollment)
            .filter(Enrollment.student_id == current_user.id)
            .order_by(Enrollment.created_at.desc())
            .all()
        )
    return enrollments


@router.post("", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    data: EnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Student enrolls in an intake. Creates enrollment with status=payment_pending."""
    if current_user.role not in ("student", "super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can enroll in intakes",
        )

    # Check intake exists
    intake = db.query(Intake).filter(Intake.id == data.intake_id).first()
    if not intake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake not found",
        )

    # Check capacity
    if intake.enrolled_count >= intake.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Intake is at full capacity",
        )

    # Check not already enrolled in same course within this intake
    existing = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == current_user.id,
            Enrollment.intake_id == data.intake_id,
            Enrollment.course_id == data.course_id,
            Enrollment.status != "dropped",
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course for this intake",
        )

    enrollment = Enrollment(
        student_id=current_user.id,
        intake_id=data.intake_id,
        course_id=data.course_id,
        status="payment_pending",
        payment_status="pending",
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.put("/{enrollment_id}/complete-payment", response_model=EnrollmentResponse)
def complete_payment(
    enrollment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark enrollment as paid — status → active, payment_status → completed. Increments intake enrolled_count."""
    enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )

    # Only the student who owns it or admin can complete payment
    if current_user.role not in ("super_admin", "admin") and enrollment.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    if enrollment.payment_status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already completed",
        )

    enrollment.status = "active"
    enrollment.payment_status = "completed"

    # Increment intake enrolled_count
    intake = db.query(Intake).filter(Intake.id == enrollment.intake_id).first()
    if intake:
        intake.enrolled_count = intake.enrolled_count + 1

    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enrollment(
    enrollment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel/drop enrollment. Admin or the student who owns it."""
    enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )

    if current_user.role not in ("super_admin", "admin") and enrollment.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    # If was active, decrement enrolled_count
    if enrollment.status == "active":
        intake = db.query(Intake).filter(Intake.id == enrollment.intake_id).first()
        if intake and intake.enrolled_count > 0:
            intake.enrolled_count = intake.enrolled_count - 1

    db.delete(enrollment)
    db.commit()
