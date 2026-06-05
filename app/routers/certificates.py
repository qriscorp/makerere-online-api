from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.certificate import Certificate
from app.schemas.certificate import (
    CertificateCreate,
    CertificateResponse,
    CertificateVerifyResponse,
)

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


@router.get("", response_model=List[CertificateResponse])
def list_certificates(
    student_id: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    certificate_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List certificates. Students see their own; admins see all with filters."""
    query = db.query(Certificate)

    if current_user.role in ("super_admin", "admin"):
        # Admin filters
        if student_id:
            query = query.filter(Certificate.student_id == student_id)
        if course_id:
            query = query.filter(Certificate.course_id == course_id)
        if certificate_type:
            query = query.filter(Certificate.certificate_type == certificate_type)
        if status_filter:
            query = query.filter(Certificate.status == status_filter)
    else:
        # Students only see their own
        query = query.filter(Certificate.student_id == current_user.id)

    certificates = query.order_by(Certificate.created_at.desc()).all()
    return certificates


@router.post("/issue", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
def issue_certificate(
    data: CertificateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin issues a certificate for a student who completed a course/unit."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can issue certificates",
        )

    # Validate certificate_type
    if data.certificate_type not in ("course", "course_unit"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="certificate_type must be 'course' or 'course_unit'",
        )

    if data.certificate_type == "course" and not data.course_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="course_id is required for course certificates",
        )

    if data.certificate_type == "course_unit" and not data.course_unit_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="course_unit_id is required for course_unit certificates",
        )

    certificate = Certificate(
        student_id=data.student_id,
        certificate_type=data.certificate_type,
        course_id=data.course_id,
        course_unit_id=data.course_unit_id,
        student_name=data.student_name,
        title=data.title,
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return certificate


@router.get("/verify/{certificate_number}", response_model=CertificateVerifyResponse)
def verify_certificate(
    certificate_number: str,
    db: Session = Depends(get_db),
):
    """PUBLIC endpoint — verify a certificate by its unique number. No auth required."""
    certificate = (
        db.query(Certificate)
        .filter(Certificate.certificate_number == certificate_number)
        .first()
    )

    if not certificate:
        return CertificateVerifyResponse(
            valid=False,
            certificate_number=certificate_number,
        )

    return CertificateVerifyResponse(
        valid=certificate.status == "active",
        certificate_number=certificate.certificate_number,
        student_name=certificate.student_name,
        title=certificate.title,
        certificate_type=certificate.certificate_type,
        issue_date=certificate.issue_date,
        status=certificate.status,
    )


@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate(
    certificate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single certificate by ID."""
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )

    # Students can only view their own
    if current_user.role not in ("super_admin", "admin") and certificate.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this certificate",
        )

    return certificate
