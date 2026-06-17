from collections import defaultdict
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.assessment import Assessment
from app.models.assessment_submission import AssessmentSubmission
from app.models.certificate import Certificate
from app.models.course import Course
from app.models.course_unit import CourseUnit
from app.models.enrollment import Enrollment
from app.models.intake import Intake
from app.models.payment import Payment
from app.models.school import School
from app.models.student_unit_enrollment import StudentUnitEnrollment
from app.models.study_material import StudyMaterial
from app.models.user import User
from app.models.virtual_class import VirtualClass
from app.schemas.dashboard import (
    DashboardActivityPoint,
    DashboardActivityResponse,
    DashboardKpiItem,
    DashboardOverviewResponse,
    DashboardSecondaryStatItem,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _format_number(value: int) -> str:
    return f"{value:,}"


def _format_ugx(amount: float) -> str:
    if amount >= 1_000_000:
        return f"UGX {amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"UGX {amount / 1_000:.0f}K"
    return f"UGX {int(amount):,}"


def _average_grade_percent(submissions: list[AssessmentSubmission]) -> float | None:
    graded = [s for s in submissions if s.is_graded and s.total_marks > 0]
    if not graded:
        return None
    return sum((s.score / s.total_marks) * 100 for s in graded) / len(graded)


def _parse_class_datetime(class_date: date, start_time: str) -> datetime:
    parts = start_time.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    return datetime.combine(class_date, time(hour, minute))


def _upcoming_classes_count(db: Session, unit_ids: list[str], days: int = 7) -> int:
    if not unit_ids:
        return 0
    today = date.today()
    end = today + timedelta(days=days)
    return (
        db.query(VirtualClass)
        .filter(
            VirtualClass.course_unit_id.in_(unit_ids),
            VirtualClass.date >= today,
            VirtualClass.date <= end,
        )
        .count()
    )


def _next_class_label(db: Session, unit_ids: list[str]) -> str | None:
    if not unit_ids:
        return None
    today = date.today()
    classes = (
        db.query(VirtualClass)
        .filter(
            VirtualClass.course_unit_id.in_(unit_ids),
            VirtualClass.date >= today,
        )
        .order_by(VirtualClass.date.asc(), VirtualClass.start_time.asc())
        .all()
    )
    if not classes:
        return None
    next_class = classes[0]
    return f"Next: {next_class.title} · {next_class.date.strftime('%b %d')} {next_class.start_time}"


def _assessments_due_count(db: Session, student_id: str, unit_ids: list[str]) -> int:
    if not unit_ids:
        return 0
    today = date.today()
    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.course_unit_id.in_(unit_ids),
            Assessment.end_date.isnot(None),
            Assessment.end_date >= today,
        )
        .all()
    )
    if not assessments:
        return 0

    submitted_ids = {
        row.assessment_id
        for row in db.query(AssessmentSubmission.assessment_id)
        .filter(AssessmentSubmission.student_id == student_id)
        .all()
    }
    return sum(1 for assessment in assessments if assessment.id not in submitted_ids)


def _build_activity_points(
    timestamps: list[datetime],
    days: int,
) -> list[DashboardActivityPoint]:
    today = date.today()
    start = today - timedelta(days=days - 1)
    buckets: dict[date, int] = defaultdict(int)

    for current in range(days):
        buckets[start + timedelta(days=current)] = 0

    for timestamp in timestamps:
        day = timestamp.date()
        if start <= day <= today:
            buckets[day] += 1

    points: list[DashboardActivityPoint] = []
    for current in range(days):
        day = start + timedelta(days=current)
        points.append(
            DashboardActivityPoint(
                date=day.strftime("%b %d"),
                value=buckets[day],
            )
        )
    return points


def _admin_overview(db: Session) -> DashboardOverviewResponse:
    total_students = db.query(User).filter(User.role == "student").count()
    total_lecturers = db.query(User).filter(User.role == "lecturer").count()
    active_courses = db.query(Course).filter(Course.status == "active").count()
    tuition_collected = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status == "completed")
        .scalar()
        or 0
    )
    active_intakes = db.query(Intake).filter(Intake.status == "active").count()
    certificates_issued = db.query(Certificate).filter(Certificate.status == "active").count()

    graded_submissions = (
        db.query(AssessmentSubmission)
        .filter(
            AssessmentSubmission.is_graded.is_(True),
            AssessmentSubmission.total_marks > 0,
        )
        .all()
    )
    pass_rate = _average_grade_percent(graded_submissions)

    schools = {school.id: school.code for school in db.query(School).all()}
    courses_by_school: dict[str, int] = defaultdict(int)
    for course in db.query(Course).filter(Course.status == "active").all():
        school_code = schools.get(course.school_id, "Other")
        courses_by_school[school_code] += 1
    school_breakdown = " · ".join(
        f"{code}: {count}" for code, count in sorted(courses_by_school.items())
    ) or "No active courses"

    mobile_payments = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status == "completed", Payment.carrier.in_(["mtn", "airtel"]))
        .scalar()
        or 0
    )
    mobile_pct = int((mobile_payments / tuition_collected) * 100) if tuition_collected else 0

    return DashboardOverviewResponse(
        kpis=[
            DashboardKpiItem(
                key="total_students",
                icon="graduation_cap",
                value=_format_number(total_students),
                label="Total students",
                breakdown=f"Registered student accounts: {total_students}",
                accent="emerald",
            ),
            DashboardKpiItem(
                key="active_lecturers",
                icon="users",
                value=_format_number(total_lecturers),
                label="Active lecturers",
                breakdown=f"Lecturer accounts on the platform: {total_lecturers}",
                accent="violet",
            ),
            DashboardKpiItem(
                key="live_courses",
                icon="book_open",
                value=_format_number(active_courses),
                label="Live courses",
                breakdown=school_breakdown,
                accent="gold",
            ),
            DashboardKpiItem(
                key="tuition_collected",
                icon="dollar_sign",
                value=_format_ugx(float(tuition_collected)),
                label="Tuition collected",
                breakdown=f"Mobile money: {mobile_pct}% of completed payments",
                accent="sky",
            ),
        ],
        secondary_stats=[
            DashboardSecondaryStatItem(
                key="active_intakes",
                icon="calendar",
                label="Active intakes",
                value=_format_number(active_intakes),
            ),
            DashboardSecondaryStatItem(
                key="certificates_issued",
                icon="award",
                label="Certificates issued",
                value=_format_number(certificates_issued),
            ),
            DashboardSecondaryStatItem(
                key="platform_pass_rate",
                icon="trending_up",
                label="Platform pass rate",
                value=f"{pass_rate:.1f}%" if pass_rate is not None else "—",
            ),
        ],
    )


def _lecturer_overview(db: Session, user: User) -> DashboardOverviewResponse:
    units = (
        db.query(CourseUnit)
        .filter(CourseUnit.lecturer_id == user.id)
        .all()
    )
    unit_ids = [unit.id for unit in units]
    assessment_ids = (
        [row.id for row in db.query(Assessment.id).filter(Assessment.created_by == user.id).all()]
        if not unit_ids
        else [
            row.id
            for row in db.query(Assessment.id)
            .filter(Assessment.course_unit_id.in_(unit_ids))
            .all()
        ]
    )

    total_students = (
        db.query(StudentUnitEnrollment.student_id)
        .filter(StudentUnitEnrollment.course_unit_id.in_(unit_ids))
        .distinct()
        .count()
        if unit_ids
        else 0
    )
    upcoming_classes = _upcoming_classes_count(db, unit_ids)
    next_class = _next_class_label(db, unit_ids)
    pending_submissions = (
        db.query(AssessmentSubmission)
        .filter(
            AssessmentSubmission.assessment_id.in_(assessment_ids),
            AssessmentSubmission.is_graded.is_(False),
        )
        .count()
        if assessment_ids
        else 0
    )
    materials_count = (
        db.query(StudyMaterial)
        .filter(StudyMaterial.uploaded_by == user.id)
        .count()
    )
    live_sessions = (
        db.query(VirtualClass)
        .filter(VirtualClass.lecturer_id == user.id)
        .count()
    )
    graded_submissions = (
        db.query(AssessmentSubmission)
        .filter(
            AssessmentSubmission.assessment_id.in_(assessment_ids),
            AssessmentSubmission.is_graded.is_(True),
            AssessmentSubmission.total_marks > 0,
        )
        .all()
        if assessment_ids
        else []
    )
    pass_rate = _average_grade_percent(graded_submissions)

    return DashboardOverviewResponse(
        kpis=[
            DashboardKpiItem(
                key="my_course_units",
                icon="book_open",
                value=_format_number(len(units)),
                label="My course units",
                breakdown=f"Assigned teaching units: {len(units)}",
                accent="crimson",
            ),
            DashboardKpiItem(
                key="total_students",
                icon="graduation_cap",
                value=_format_number(total_students),
                label="Total students",
                breakdown="Across all assigned course units",
                accent="emerald",
            ),
            DashboardKpiItem(
                key="upcoming_classes",
                icon="calendar",
                value=_format_number(upcoming_classes),
                label="Upcoming classes",
                breakdown=next_class or "No upcoming sessions scheduled",
                accent="violet",
            ),
            DashboardKpiItem(
                key="pending_submissions",
                icon="file_text",
                value=_format_number(pending_submissions),
                label="Pending submissions",
                breakdown="Assessments awaiting grading",
                accent="gold",
            ),
        ],
        secondary_stats=[
            DashboardSecondaryStatItem(
                key="materials_uploaded",
                icon="file_text",
                label="Materials uploaded",
                value=_format_number(materials_count),
            ),
            DashboardSecondaryStatItem(
                key="live_sessions",
                icon="calendar",
                label="Live sessions",
                value=_format_number(live_sessions),
            ),
            DashboardSecondaryStatItem(
                key="pass_rate",
                icon="trending_up",
                label="Pass rate",
                value=f"{pass_rate:.1f}%" if pass_rate is not None else "—",
            ),
        ],
    )


def _student_overview(db: Session, user: User) -> DashboardOverviewResponse:
    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == user.id, Enrollment.status != "dropped")
        .all()
    )
    active_enrollments = [e for e in enrollments if e.status == "active"]
    completed_enrollments = [e for e in enrollments if e.status == "completed"]
    unit_ids = [
        row.course_unit_id
        for row in db.query(StudentUnitEnrollment)
        .filter(StudentUnitEnrollment.student_id == user.id)
        .all()
    ]

    upcoming_classes = _upcoming_classes_count(db, unit_ids)
    pending_payments = (
        db.query(Payment)
        .filter(
            Payment.student_id == user.id,
            Payment.status.in_(["pending", "processing"]),
        )
        .count()
    )
    submissions = (
        db.query(AssessmentSubmission)
        .filter(AssessmentSubmission.student_id == user.id)
        .all()
    )
    average_grade = _average_grade_percent(submissions)
    certificates_count = (
        db.query(Certificate)
        .filter(Certificate.student_id == user.id, Certificate.status == "active")
        .count()
    )
    assessments_due = _assessments_due_count(db, user.id, unit_ids)

    pending_label = (
        f"{pending_payments} payment{'s' if pending_payments != 1 else ''} pending"
        if pending_payments
        else "No pending payments"
    )

    return DashboardOverviewResponse(
        kpis=[
            DashboardKpiItem(
                key="enrolled_courses",
                icon="book_open",
                value=_format_number(len(enrollments)),
                label="Enrolled courses",
                breakdown=f"{len(active_enrollments)} active · {len(completed_enrollments)} completed",
                accent="crimson",
            ),
            DashboardKpiItem(
                key="upcoming_classes",
                icon="calendar",
                value=_format_number(upcoming_classes),
                label="Upcoming classes",
                breakdown="Virtual learning sessions in the next 7 days",
                accent="violet",
            ),
            DashboardKpiItem(
                key="pending_payments",
                icon="credit_card",
                value=_format_number(pending_payments),
                label="Pending payments",
                breakdown=pending_label,
                accent="gold",
            ),
            DashboardKpiItem(
                key="average_grade",
                icon="trending_up",
                value=f"{average_grade:.0f}%" if average_grade is not None else "—",
                label="Average grade",
                breakdown="Based on graded assessment submissions",
                accent="emerald",
            ),
        ],
        secondary_stats=[
            DashboardSecondaryStatItem(
                key="certificates_earned",
                icon="award",
                label="Certificates earned",
                value=_format_number(certificates_count),
            ),
            DashboardSecondaryStatItem(
                key="assessments_due",
                icon="clipboard_check",
                label="Assessments due",
                value=_format_number(assessments_due),
            ),
            DashboardSecondaryStatItem(
                key="submissions_made",
                icon="file_text",
                label="Submissions made",
                value=_format_number(len(submissions)),
            ),
        ],
    )


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Role-scoped dashboard KPIs and secondary stats."""
    if current_user.role in ("super_admin", "admin"):
        return _admin_overview(db)
    if current_user.role == "lecturer":
        return _lecturer_overview(db, current_user)
    return _student_overview(db, current_user)


@router.get("/activity", response_model=DashboardActivityResponse)
def get_dashboard_activity(
    metric: str = Query("enrollments", pattern="^(enrollments|completions|assessments)$"),
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Daily activity series for dashboard charts."""
    since = datetime.utcnow() - timedelta(days=days)

    if metric == "enrollments":
        if current_user.role in ("super_admin", "admin"):
            rows = db.query(Enrollment.created_at).filter(Enrollment.created_at >= since).all()
        elif current_user.role == "lecturer":
            unit_ids = [
                unit.id
                for unit in db.query(CourseUnit)
                .filter(CourseUnit.lecturer_id == current_user.id)
                .all()
            ]
            enrollment_ids = (
                [
                    row.enrollment_id
                    for row in db.query(StudentUnitEnrollment.enrollment_id)
                    .filter(StudentUnitEnrollment.course_unit_id.in_(unit_ids))
                    .distinct()
                    .all()
                ]
                if unit_ids
                else []
            )
            rows = (
                db.query(Enrollment.created_at)
                .filter(
                    Enrollment.id.in_(enrollment_ids),
                    Enrollment.created_at >= since,
                )
                .all()
                if enrollment_ids
                else []
            )
        else:
            rows = (
                db.query(Enrollment.created_at)
                .filter(
                    Enrollment.student_id == current_user.id,
                    Enrollment.created_at >= since,
                )
                .all()
            )
        timestamps = [row.created_at for row in rows]
    elif metric == "completions":
        if current_user.role in ("super_admin", "admin"):
            query = db.query(Enrollment.created_at).filter(
                Enrollment.status == "completed",
                Enrollment.created_at >= since,
            )
        elif current_user.role == "lecturer":
            unit_ids = [
                unit.id
                for unit in db.query(CourseUnit)
                .filter(CourseUnit.lecturer_id == current_user.id)
                .all()
            ]
            enrollment_ids = (
                [
                    row.enrollment_id
                    for row in db.query(StudentUnitEnrollment.enrollment_id)
                    .filter(
                        StudentUnitEnrollment.course_unit_id.in_(unit_ids),
                        StudentUnitEnrollment.status == "completed",
                    )
                    .distinct()
                    .all()
                ]
                if unit_ids
                else []
            )
            query = db.query(Enrollment.created_at).filter(
                Enrollment.id.in_(enrollment_ids),
                Enrollment.status == "completed",
                Enrollment.created_at >= since,
            ) if enrollment_ids else None
        else:
            query = db.query(Enrollment.created_at).filter(
                Enrollment.student_id == current_user.id,
                Enrollment.status == "completed",
                Enrollment.created_at >= since,
            )
        rows = query.all() if query is not None else []
        timestamps = [row.created_at for row in rows]
    else:
        if current_user.role in ("super_admin", "admin"):
            rows = (
                db.query(AssessmentSubmission.submitted_at)
                .filter(AssessmentSubmission.submitted_at >= since)
                .all()
            )
        elif current_user.role == "lecturer":
            unit_ids = [
                unit.id
                for unit in db.query(CourseUnit)
                .filter(CourseUnit.lecturer_id == current_user.id)
                .all()
            ]
            assessment_ids = (
                [
                    row.id
                    for row in db.query(Assessment.id)
                    .filter(Assessment.course_unit_id.in_(unit_ids))
                    .all()
                ]
                if unit_ids
                else []
            )
            rows = (
                db.query(AssessmentSubmission.submitted_at)
                .filter(
                    AssessmentSubmission.assessment_id.in_(assessment_ids),
                    AssessmentSubmission.submitted_at >= since,
                )
                .all()
                if assessment_ids
                else []
            )
        else:
            rows = (
                db.query(AssessmentSubmission.submitted_at)
                .filter(
                    AssessmentSubmission.student_id == current_user.id,
                    AssessmentSubmission.submitted_at >= since,
                )
                .all()
            )
        timestamps = [row.submitted_at for row in rows]

    return DashboardActivityResponse(
        metric=metric,  # type: ignore[arg-type]
        days=days,
        points=_build_activity_points(timestamps, days),
    )
