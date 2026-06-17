"""
Payments router — handles mobile money payment initiation and status checks.
Integrates with Interswitch/QuickTeller for MTN and Airtel Mobile Money (Uganda).
"""
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.payment import Payment
from app.models.enrollment import Enrollment
from app.models.course import Course
from app.interswitch.config import (
    detect_carrier,
    normalize_phone,
    MTN_PAYMENT_CODE,
    AIRTEL_PAYMENT_CODE,
)
from app.interswitch.client import (
    make_payment_request,
    generate_request_reference,
    is_payment_successful,
)

router = APIRouter(prefix="/api/payments", tags=["Payments"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class InitiatePaymentRequest(BaseModel):
    enrollment_id: str
    phone_number: str


class PaymentResponse(BaseModel):
    id: str
    student_id: str
    enrollment_id: str | None
    amount: float
    currency: str
    phone_number: str
    carrier: str
    payment_type: str
    status: str
    request_reference: str | None
    response_code: str | None
    response_message: str | None
    description: str
    created_at: str
    completed_at: str | None


class PaymentStatusResponse(BaseModel):
    id: str
    status: str
    response_code: str | None
    response_message: str | None


class PaymentUpdate(BaseModel):
    status: str | None = None
    description: str | None = None


class SystemWalletResponse(BaseModel):
    balance: float
    currency: str
    total_received: float
    total_withdrawn: float


class LecturerWalletResponse(BaseModel):
    balance: float
    currency: str
    total_earned: float


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get("", response_model=List[PaymentResponse])
def list_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List payments. Students see their own; admins see all."""
    if current_user.role in ("super_admin", "admin"):
        payments = db.query(Payment).order_by(Payment.created_at.desc()).all()
    else:
        payments = (
            db.query(Payment)
            .filter(Payment.student_id == current_user.id)
            .order_by(Payment.created_at.desc())
            .all()
        )

    return [
        PaymentResponse(
            id=p.id,
            student_id=p.student_id,
            enrollment_id=p.enrollment_id,
            amount=p.amount,
            currency=p.currency,
            phone_number=p.phone_number,
            carrier=p.carrier,
            payment_type=p.payment_type,
            status=p.status,
            request_reference=p.request_reference,
            response_code=p.response_code,
            response_message=p.response_message,
            description=p.description,
            created_at=str(p.created_at),
            completed_at=str(p.completed_at) if p.completed_at else None,
        )
        for p in payments
    ]


@router.get("/system-wallet", response_model=SystemWalletResponse)
def get_system_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """System wallet summary derived from completed payments."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admin can view the system wallet",
        )

    completed = (
        db.query(Payment)
        .filter(Payment.status == "completed")
        .all()
    )
    total_received = sum(p.amount for p in completed)
    return SystemWalletResponse(
        balance=total_received,
        currency="UGX",
        total_received=total_received,
        total_withdrawn=0.0,
    )


@router.get("/lecturer-wallet", response_model=LecturerWalletResponse)
def get_lecturer_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lecturer wallet summary from completed tutoring bookings."""
    if current_user.role not in ("lecturer", "super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only lecturers can view their wallet",
        )

    from app.models.tutor_profile import TutorProfile
    from app.models.tutoring_booking import TutoringBooking

    profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
    if not profile:
        return LecturerWalletResponse(balance=0.0, currency="UGX", total_earned=0.0)

    bookings = (
        db.query(TutoringBooking)
        .filter(
            TutoringBooking.tutor_profile_id == profile.id,
            TutoringBooking.status == "completed",
        )
        .all()
    )
    total_earned = sum(b.total_cost for b in bookings)
    return LecturerWalletResponse(
        balance=total_earned,
        currency="UGX",
        total_earned=total_earned,
    )


def _payment_to_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        student_id=payment.student_id,
        enrollment_id=payment.enrollment_id,
        amount=payment.amount,
        currency=payment.currency,
        phone_number=payment.phone_number,
        carrier=payment.carrier,
        payment_type=payment.payment_type,
        status=payment.status,
        request_reference=payment.request_reference,
        response_code=payment.response_code,
        response_message=payment.response_message,
        description=payment.description,
        created_at=str(payment.created_at),
        completed_at=str(payment.completed_at) if payment.completed_at else None,
    )


@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(
    data: InitiatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate a mobile money payment for course enrollment.
    Student provides their phone number — the system charges it via Interswitch.
    """
    if current_user.role not in ("student", "super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can make payments",
        )

    # Validate enrollment
    enrollment = db.query(Enrollment).filter(Enrollment.id == data.enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    if enrollment.student_id != current_user.id and current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your enrollment")

    if enrollment.payment_status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment already completed")

    # Get course fee
    course = db.query(Course).filter(Course.id == enrollment.course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    amount = course.fee
    if amount <= 0:
        # Free course — just activate
        enrollment.status = "active"
        enrollment.payment_status = "completed"
        db.commit()
        db.refresh(enrollment)
        return PaymentResponse(
            id="free",
            student_id=current_user.id,
            enrollment_id=enrollment.id,
            amount=0,
            currency="UGX",
            phone_number=data.phone_number,
            carrier="none",
            payment_type="enrollment",
            status="completed",
            request_reference=None,
            response_code="00",
            response_message="Free course - auto-activated",
            description=f"Enrollment in {course.title} (Free)",
            created_at=str(datetime.utcnow()),
            completed_at=str(datetime.utcnow()),
        )

    # Detect carrier
    phone = normalize_phone(data.phone_number)
    carrier = detect_carrier(phone)
    if carrier == "unknown":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must be MTN (077/078/076/079) or Airtel (075/074/070)",
        )

    # Get payment code for carrier
    payment_code = MTN_PAYMENT_CODE if carrier == "mtn" else AIRTEL_PAYMENT_CODE
    if not payment_code:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Payment code for {carrier.upper()} not configured. Contact admin.",
        )

    # Create payment record
    request_reference = generate_request_reference(prefix="mak-enroll-")
    payment = Payment(
        student_id=current_user.id,
        enrollment_id=enrollment.id,
        amount=amount,
        phone_number=phone,
        carrier=carrier,
        payment_type="enrollment",
        status="processing",
        request_reference=request_reference,
        description=f"Payment for {course.title}",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Call Interswitch
    response = await make_payment_request(
        payment_code=payment_code,
        customer_id=phone,
        amount=str(int(amount)),
        request_reference=request_reference,
    )

    # Update payment record with response
    payment.response_code = response.get("responseCode", "")
    payment.response_message = response.get("responseMessage", "")

    if is_payment_successful(response):
        payment.status = "completed"
        payment.completed_at = datetime.utcnow()
        payment.vendor_reference = response.get("response", {}).get("retrievalReference", "")

        # Activate enrollment
        enrollment.status = "active"
        enrollment.payment_status = "completed"

        from app.models.intake import Intake
        intake = db.query(Intake).filter(Intake.id == enrollment.intake_id).first()
        if intake:
            intake.enrolled_count = intake.enrolled_count + 1
    else:
        payment.status = "failed"

    db.commit()
    db.refresh(payment)

    return PaymentResponse(
        id=payment.id,
        student_id=payment.student_id,
        enrollment_id=payment.enrollment_id,
        amount=payment.amount,
        currency=payment.currency,
        phone_number=payment.phone_number,
        carrier=payment.carrier,
        payment_type=payment.payment_type,
        status=payment.status,
        request_reference=payment.request_reference,
        response_code=payment.response_code,
        response_message=payment.response_message,
        description=payment.description,
        created_at=str(payment.created_at),
        completed_at=str(payment.completed_at) if payment.completed_at else None,
    )


@router.get("/{payment_id}/status", response_model=PaymentStatusResponse)
def get_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check the status of a payment."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if payment.student_id != current_user.id and current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return PaymentStatusResponse(
        id=payment.id,
        status=payment.status,
        response_code=payment.response_code,
        response_message=payment.response_message,
    )


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: str,
    data: PaymentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update payment status or description. Admins only."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if data.status is None and data.description is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    old_status = payment.status
    if data.status is not None:
        payment.status = data.status
        if data.status == "completed" and not payment.completed_at:
            payment.completed_at = datetime.utcnow()
    if data.description is not None:
        payment.description = data.description

    # Activate linked enrollment when payment marked completed
    if (
        payment.enrollment_id
        and old_status != "completed"
        and payment.status == "completed"
    ):
        enrollment = (
            db.query(Enrollment)
            .filter(Enrollment.id == payment.enrollment_id)
            .first()
        )
        if enrollment and enrollment.payment_status != "completed":
            enrollment.status = "active"
            enrollment.payment_status = "completed"
            from app.models.intake import Intake
            intake = db.query(Intake).filter(Intake.id == enrollment.intake_id).first()
            if intake:
                intake.enrolled_count += 1

    db.commit()
    db.refresh(payment)
    return _payment_to_response(payment)


@router.put("/{payment_id}/complete", response_model=PaymentResponse)
def complete_payment_record(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a payment as completed (admin manual completion)."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return update_payment(
        payment_id,
        PaymentUpdate(status="completed"),
        current_user,
        db,
    )


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a payment record. Only super_admin can delete."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admin can delete payments",
        )

    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    db.delete(payment)
    db.commit()
    return None
