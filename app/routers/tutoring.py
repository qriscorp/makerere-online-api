from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.tutor_profile import TutorProfile
from app.models.tutoring_booking import TutoringBooking
from app.schemas.tutoring import (
    TutorProfileCreate,
    TutorProfileResponse,
    TutorPublicResponse,
    TutorAdminResponse,
    TutorAdminUpdate,
    TutoringBookingCreate,
    TutoringBookingResponse,
)

router = APIRouter(prefix="/api/tutoring", tags=["Tutoring"])


@router.get("/public", response_model=List[TutorPublicResponse])
def list_public_tutors(db: Session = Depends(get_db)):
    """Public endpoint — list only APPROVED and available tutor profiles."""
    profiles = (
        db.query(TutorProfile, User.name)
        .join(User, User.id == TutorProfile.user_id)
        .filter(TutorProfile.is_available == True)  # noqa: E712
        .filter(TutorProfile.approval_status == "approved")
        .order_by(TutorProfile.created_at.desc())
        .all()
    )

    results = []
    for profile, name in profiles:
        subjects = [s.strip() for s in profile.subjects.split(",") if s.strip()]
        results.append(
            TutorPublicResponse(
                id=profile.id,
                name=name,
                subjects=subjects,
                hourly_rate=profile.hourly_rate,
                bio=profile.bio,
                is_available=profile.is_available,
            )
        )
    return results


@router.get("/tutors", response_model=List[TutorPublicResponse])
def list_all_tutors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Authenticated endpoint — list all tutor profiles for dashboard use."""
    profiles = (
        db.query(TutorProfile, User.name)
        .join(User, User.id == TutorProfile.user_id)
        .order_by(TutorProfile.created_at.desc())
        .all()
    )

    results = []
    for profile, name in profiles:
        subjects = [s.strip() for s in profile.subjects.split(",") if s.strip()]
        results.append(
            TutorPublicResponse(
                id=profile.id,
                name=name,
                subjects=subjects,
                hourly_rate=profile.hourly_rate,
                bio=profile.bio,
                is_available=profile.is_available,
            )
        )
    return results


# ─── Admin Tutor Management ─────────────────────────────────────────────────────


@router.get("/admin/all", response_model=List[TutorAdminResponse])
def admin_list_all_tutors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin endpoint — list ALL tutor profiles with approval status."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all tutor profiles",
        )

    profiles = (
        db.query(TutorProfile, User.name)
        .join(User, User.id == TutorProfile.user_id)
        .order_by(TutorProfile.created_at.desc())
        .all()
    )

    results = []
    for profile, name in profiles:
        subjects = [s.strip() for s in profile.subjects.split(",") if s.strip()]
        results.append(
            TutorAdminResponse(
                id=profile.id,
                user_id=profile.user_id,
                name=name,
                subjects=subjects,
                hourly_rate=profile.hourly_rate,
                bio=profile.bio,
                is_available=profile.is_available,
                approval_status=profile.approval_status,
                created_at=str(profile.created_at) if profile.created_at else None,
            )
        )
    return results


def _profile_to_admin_response(profile: TutorProfile, name: str) -> TutorAdminResponse:
    subjects = [s.strip() for s in profile.subjects.split(",") if s.strip()]
    return TutorAdminResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=name,
        subjects=subjects,
        hourly_rate=profile.hourly_rate,
        bio=profile.bio,
        is_available=profile.is_available,
        approval_status=profile.approval_status,
        created_at=str(profile.created_at) if profile.created_at else None,
    )


@router.put("/admin/{profile_id}", response_model=TutorAdminResponse)
def admin_update_tutor(
    profile_id: str,
    data: TutorAdminUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin updates a tutor profile."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update tutor profiles",
        )

    profile = db.query(TutorProfile).filter(TutorProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor profile not found")

    user = db.query(User).filter(User.id == profile.user_id).first()
    if data.subjects is not None:
        profile.subjects = ",".join(data.subjects)
    if data.hourly_rate is not None:
        profile.hourly_rate = data.hourly_rate
    if data.bio is not None:
        profile.bio = data.bio
    if data.is_available is not None:
        profile.is_available = data.is_available
    if data.approval_status is not None:
        profile.approval_status = data.approval_status

    db.commit()
    db.refresh(profile)
    return _profile_to_admin_response(profile, user.name if user else "Unknown")


@router.delete("/admin/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_tutor(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a tutor profile. Only super_admin can delete."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admin can delete tutor profiles",
        )

    profile = db.query(TutorProfile).filter(TutorProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor profile not found")

    db.query(TutoringBooking).filter(
        TutoringBooking.tutor_profile_id == profile_id
    ).delete()
    db.delete(profile)
    db.commit()
    return None


@router.put("/admin/{profile_id}/approve")
def admin_approve_tutor(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin approves a tutor profile — makes it visible publicly."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can approve tutor profiles",
        )

    profile = db.query(TutorProfile).filter(TutorProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor profile not found")

    profile.approval_status = "approved"
    db.commit()
    return {"message": "Tutor profile approved", "id": profile_id}


@router.put("/admin/{profile_id}/reject")
def admin_reject_tutor(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin rejects a tutor profile — hides it from public/student view."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reject tutor profiles",
        )

    profile = db.query(TutorProfile).filter(TutorProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor profile not found")

    profile.approval_status = "rejected"
    db.commit()
    return {"message": "Tutor profile rejected", "id": profile_id}


@router.get("/my-profile", response_model=TutorProfileResponse)
def get_my_tutor_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current lecturer's tutor profile."""
    if current_user.role not in ("lecturer", "super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only lecturers can have tutor profiles",
        )

    profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found. Create one first.",
        )

    subjects = [s.strip() for s in profile.subjects.split(",") if s.strip()]
    return TutorProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        subjects=subjects,
        hourly_rate=profile.hourly_rate,
        bio=profile.bio,
        is_available=profile.is_available,
        approval_status=profile.approval_status,
    )


@router.post("/my-profile", response_model=TutorProfileResponse)
def create_or_update_tutor_profile(
    data: TutorProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update the lecturer's tutor profile."""
    if current_user.role not in ("lecturer", "super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only lecturers can manage tutor profiles",
        )

    profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()

    subjects_str = ",".join(data.subjects)

    if profile:
        profile.subjects = subjects_str
        profile.hourly_rate = data.hourly_rate
        profile.bio = data.bio
        profile.is_available = data.is_available
        # Reset to pending if previously rejected so admin can re-review
        if profile.approval_status == "rejected":
            profile.approval_status = "pending"
    else:
        profile = TutorProfile(
            user_id=current_user.id,
            subjects=subjects_str,
            hourly_rate=data.hourly_rate,
            bio=data.bio,
            is_available=data.is_available,
            approval_status="pending",
        )
        db.add(profile)

    db.commit()
    db.refresh(profile)

    subjects = [s.strip() for s in profile.subjects.split(",") if s.strip()]
    return TutorProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        subjects=subjects,
        hourly_rate=profile.hourly_rate,
        bio=profile.bio,
        is_available=profile.is_available,
        approval_status=profile.approval_status,
    )


# ─── Tutoring Bookings ──────────────────────────────────────────────────────────


@router.get("/bookings", response_model=List[TutoringBookingResponse])
def list_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get bookings. Student sees their own, lecturer sees bookings for their profile."""
    if current_user.role == "student":
        bookings = (
            db.query(TutoringBooking)
            .filter(TutoringBooking.student_id == current_user.id)
            .order_by(TutoringBooking.created_at.desc())
            .all()
        )
    elif current_user.role == "lecturer":
        # Find the lecturer's tutor profile
        profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
        if not profile:
            return []
        bookings = (
            db.query(TutoringBooking)
            .filter(TutoringBooking.tutor_profile_id == profile.id)
            .order_by(TutoringBooking.created_at.desc())
            .all()
        )
    else:
        # Admin sees all
        bookings = db.query(TutoringBooking).order_by(TutoringBooking.created_at.desc()).all()

    return bookings


@router.post("/bookings", response_model=TutoringBookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    data: TutoringBookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Student books a tutoring session. Calculates total_cost from tutor's hourly_rate."""
    if current_user.role not in ("student", "super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can book tutoring sessions",
        )

    # Validate tutor profile exists
    profile = db.query(TutorProfile).filter(TutorProfile.id == data.tutor_profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found",
        )

    if not profile.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tutor is not currently available",
        )

    if profile.approval_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tutor has not been approved for tutoring yet",
        )

    # Calculate total cost
    total_cost = profile.hourly_rate * data.duration

    booking = TutoringBooking(
        student_id=current_user.id,
        tutor_profile_id=data.tutor_profile_id,
        subject=data.subject,
        date=data.date,
        time_slot=data.time_slot,
        duration=data.duration,
        total_cost=total_cost,
        status="upcoming",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
