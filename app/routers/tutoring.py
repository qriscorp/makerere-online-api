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
    TutoringBookingCreate,
    TutoringBookingResponse,
)

router = APIRouter(prefix="/api/tutoring", tags=["Tutoring"])


@router.get("/public", response_model=List[TutorPublicResponse])
def list_public_tutors(db: Session = Depends(get_db)):
    """Public endpoint — list all available tutor profiles with user name."""
    profiles = (
        db.query(TutorProfile, User.name)
        .join(User, User.id == TutorProfile.user_id)
        .filter(TutorProfile.is_available == True)  # noqa: E712
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
    else:
        profile = TutorProfile(
            user_id=current_user.id,
            subjects=subjects_str,
            hourly_rate=data.hourly_rate,
            bio=data.bio,
            is_available=data.is_available,
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
