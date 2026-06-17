from datetime import datetime, time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.assessment import Assessment
from app.models.notification import Notification
from app.models.student_unit_enrollment import StudentUnitEnrollment
from app.models.user import User
from app.models.virtual_class import VirtualClass
from app.schemas.notification import (
    NotificationResponse,
    UnreadCountResponse,
    UpcomingAlertsResponse,
    ExamDeadlineAlert,
    UpcomingClassAlert,
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


def _student_unit_ids(db: Session, student_id: str) -> list[str]:
    return [
        row.course_unit_id
        for row in db.query(StudentUnitEnrollment)
        .filter(StudentUnitEnrollment.student_id == student_id)
        .all()
    ]


def _parse_class_datetime(class_date, start_time: str) -> datetime:
    parts = start_time.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    return datetime.combine(class_date, time(hour, minute))


@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    category: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List notifications for the current user."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if category:
        query = query.filter(Notification.category == category)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    return query.order_by(Notification.created_at.desc()).all()


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return unread notification count for the current user."""
    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .count()
    )
    return UnreadCountResponse(count=count)


@router.get("/upcoming-alerts", response_model=UpcomingAlertsResponse)
def upcoming_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exam deadlines within 24 hours and live classes within 15 minutes (students)."""
    if current_user.role != "student":
        return UpcomingAlertsResponse(exam_deadlines=[], upcoming_classes=[])

    unit_ids = _student_unit_ids(db, current_user.id)
    if not unit_ids:
        return UpcomingAlertsResponse(exam_deadlines=[], upcoming_classes=[])

    now = datetime.utcnow()
    exam_deadlines: list[ExamDeadlineAlert] = []
    upcoming_classes: list[UpcomingClassAlert] = []

    assessments = (
        db.query(Assessment)
        .filter(Assessment.course_unit_id.in_(unit_ids))
        .filter(Assessment.end_date.isnot(None))
        .all()
    )
    for assessment in assessments:
        end_at = datetime.combine(assessment.end_date, time(23, 59, 59))
        hours_left = int((end_at - now).total_seconds() // 3600)
        if 0 < hours_left <= 24:
            exam_deadlines.append(
                ExamDeadlineAlert(
                    id=assessment.id,
                    title=assessment.title,
                    hours_left=hours_left,
                    course_unit_id=assessment.course_unit_id,
                )
            )

    classes = (
        db.query(VirtualClass)
        .filter(VirtualClass.course_unit_id.in_(unit_ids))
        .all()
    )
    for virtual_class in classes:
        class_at = _parse_class_datetime(virtual_class.date, virtual_class.start_time)
        minutes_left = int((class_at - now).total_seconds() // 60)
        if 0 < minutes_left <= 15:
            upcoming_classes.append(
                UpcomingClassAlert(
                    id=virtual_class.id,
                    title=virtual_class.title,
                    minutes_left=minutes_left,
                    course_unit_id=virtual_class.course_unit_id,
                )
            )

    return UpcomingAlertsResponse(
        exam_deadlines=exam_deadlines,
        upcoming_classes=upcoming_classes,
    )


@router.patch("/read-all", response_model=UnreadCountResponse)
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications for the current user as read."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return UnreadCountResponse(count=0)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a single notification as read."""
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
