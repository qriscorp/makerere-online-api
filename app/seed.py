"""Seed the database with initial users, settings, and sample academic data on startup."""
from datetime import date, datetime

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.school import School
from app.models.course import Course
from app.models.course_unit import CourseUnit
from app.models.course_unit_link import CourseUnitLink
from app.models.intake import Intake
from app.models.enrollment import Enrollment
from app.models.student_unit_enrollment import StudentUnitEnrollment
from app.models.tutor_profile import TutorProfile
from app.models.payment import Payment
from app.models.system_setting import SystemSetting
from app.auth import hash_password


SEED_USERS = [
    {
        "name": "Super Administrator",
        "email": "superadmin@makonline.com",
        "password": "123456789",
        "role": "super_admin",
    },
    {
        "name": "Platform Admin",
        "email": "admin@makonline.com",
        "password": "123456789",
        "role": "admin",
    },
    {
        "name": "Dr. Okello James",
        "email": "firstlecturer@makonline.com",
        "password": "123456789",
        "role": "lecturer",
    },
    {
        "name": "Dr. Grace Nakato",
        "email": "secondlecturer@makonline.com",
        "password": "123456789",
        "role": "lecturer",
    },
    {
        "name": "Aisha Nansubuga",
        "email": "firststudent@makonline.com",
        "password": "123456789",
        "role": "student",
    },
    {
        "name": "Brian Ssemwogerere",
        "email": "secondstudent@makonline.com",
        "password": "123456789",
        "role": "student",
    },
]

DEFAULT_SETTINGS = {
    "platform_name": "Makerere Online",
    "support_email": "support@mak.ac.ug",
    "default_language": "en",
    "zoom_api_key": "",
    "zoom_api_secret": "",
    "jitsi_domain": "meet.jit.si",
    "interswitch_api_key": "",
    "interswitch_merchant_id": "",
    "email_notifications_enabled": "true",
    "sms_notifications_enabled": "false",
}

SEED_SCHOOLS = [
    {
        "name": "School of Computing and Informatics",
        "code": "SCI",
        "description": "Computing, software engineering, and information systems programmes.",
        "head_of_school": "Prof. Josephine Nabukenya",
        "departments_count": 4,
        "status": "active",
    },
    {
        "name": "School of Business and Management",
        "code": "SBM",
        "description": "Business administration, finance, and entrepreneurship programmes.",
        "head_of_school": "Dr. Sarah Kiggundu",
        "departments_count": 3,
        "status": "active",
    },
]

SEED_COURSES = [
    {
        "title": "Bachelor of Science in Computer Science",
        "description": "A four-year programme covering algorithms, systems, and software development.",
        "school_code": "SCI",
        "duration": 48,
        "duration_unit": "months",
        "fee": 3_500_000,
        "pass_mark": 50,
        "status": "active",
    },
    {
        "title": "Bachelor of Business Administration",
        "description": "A four-year programme in management, accounting, and business strategy.",
        "school_code": "SBM",
        "duration": 48,
        "duration_unit": "months",
        "fee": 3_200_000,
        "pass_mark": 50,
        "status": "active",
    },
]

SEED_COURSE_UNITS = [
    {
        "title": "Data Structures and Algorithms",
        "description": "Foundational data structures, complexity analysis, and problem solving.",
        "lecturer_email": "firstlecturer@makonline.com",
        "credit_hours": 4,
        "status": "active",
        "course_title": "Bachelor of Science in Computer Science",
    },
    {
        "title": "Principles of Management",
        "description": "Introduction to management theory, leadership, and organisational behaviour.",
        "lecturer_email": "firstlecturer@makonline.com",
        "credit_hours": 3,
        "status": "active",
        "course_title": "Bachelor of Business Administration",
    },
]

SEED_INTAKES = [
    {
        "name": "August 2026 Intake",
        "year_level": 1,
        "start_date": date(2026, 8, 1),
        "end_date": date(2027, 7, 31),
        "enrollment_deadline": date(2026, 9, 30),
        "capacity": 120,
        "course_titles": ["Bachelor of Science in Computer Science"],
        "status": "active",
    },
    {
        "name": "January 2027 Intake",
        "year_level": 1,
        "start_date": date(2027, 1, 15),
        "end_date": date(2027, 12, 15),
        "enrollment_deadline": date(2027, 2, 28),
        "capacity": 100,
        "course_titles": [
            "Bachelor of Science in Computer Science",
            "Bachelor of Business Administration",
        ],
        "status": "active",
    },
]


SEED_ENROLLMENTS = [
    {
        "student_email": "firststudent@makonline.com",
        "intake_name": "August 2026 Intake",
        "course_title": "Bachelor of Science in Computer Science",
        "status": "active",
        "payment_status": "completed",
    },
    {
        "student_email": "secondstudent@makonline.com",
        "intake_name": "January 2027 Intake",
        "course_title": "Bachelor of Business Administration",
        "status": "payment_pending",
        "payment_status": "pending",
    },
]

SEED_TUTOR_PROFILES = [
    {
        "lecturer_email": "firstlecturer@makonline.com",
        "subjects": "Data Structures,Algorithms,Programming",
        "hourly_rate": 75000,
        "bio": "Experienced lecturer in computing and software engineering.",
        "is_available": True,
        "approval_status": "approved",
    },
    {
        "lecturer_email": "secondlecturer@makonline.com",
        "subjects": "Management,Business Strategy",
        "hourly_rate": 65000,
        "bio": "Business lecturer offering tutoring in management principles.",
        "is_available": True,
        "approval_status": "pending",
    },
]

SEED_PAYMENTS = [
    {
        "student_email": "firststudent@makonline.com",
        "intake_name": "August 2026 Intake",
        "course_title": "Bachelor of Science in Computer Science",
        "amount": 3_500_000,
        "phone_number": "0772123456",
        "carrier": "mtn",
        "status": "completed",
        "request_reference": "mak-seed-001",
        "description": "Enrollment payment — BSc Computer Science",
    },
    {
        "student_email": "secondstudent@makonline.com",
        "intake_name": "January 2027 Intake",
        "course_title": "Bachelor of Business Administration",
        "amount": 3_200_000,
        "phone_number": "0752987654",
        "carrier": "airtel",
        "status": "pending",
        "request_reference": "mak-seed-002",
        "description": "Enrollment payment — BBA (pending)",
    },
]


def _seed_schools(db) -> dict[str, School]:
    schools_by_code: dict[str, School] = {}
    for data in SEED_SCHOOLS:
        existing = db.query(School).filter(School.code == data["code"]).first()
        if existing:
            schools_by_code[existing.code] = existing
            print(f"  School exists: {existing.code}")
            continue
        school = School(**data)
        db.add(school)
        db.flush()
        schools_by_code[school.code] = school
        print(f"  Created school: {school.code} — {school.name}")
    return schools_by_code


def _seed_courses(db, schools_by_code: dict[str, School]) -> dict[str, Course]:
    courses_by_title: dict[str, Course] = {}
    for data in SEED_COURSES:
        school = schools_by_code.get(data["school_code"])
        if not school:
            print(f"  Skipped course (school missing): {data['title']}")
            continue
        existing = (
            db.query(Course)
            .filter(Course.title == data["title"], Course.school_id == school.id)
            .first()
        )
        if existing:
            courses_by_title[existing.title] = existing
            print(f"  Course exists: {existing.title}")
            continue
        course = Course(
            title=data["title"],
            description=data["description"],
            school_id=school.id,
            duration=data["duration"],
            duration_unit=data["duration_unit"],
            fee=data["fee"],
            pass_mark=data["pass_mark"],
            status=data["status"],
        )
        db.add(course)
        db.flush()
        courses_by_title[course.title] = course
        print(f"  Created course: {course.title}")
    return courses_by_title


def _seed_course_units(
    db,
    courses_by_title: dict[str, Course],
) -> dict[str, CourseUnit]:
    units_by_title: dict[str, CourseUnit] = {}
    for data in SEED_COURSE_UNITS:
        existing = db.query(CourseUnit).filter(CourseUnit.title == data["title"]).first()
        if existing:
            units_by_title[existing.title] = existing
            print(f"  Course unit exists: {existing.title}")
            continue

        lecturer = (
            db.query(User).filter(User.email == data["lecturer_email"]).first()
        )
        course = courses_by_title.get(data["course_title"])

        unit = CourseUnit(
            title=data["title"],
            description=data["description"],
            course_id=course.id if course else None,
            lecturer_id=lecturer.id if lecturer else None,
            credit_hours=data["credit_hours"],
            status=data["status"],
        )
        db.add(unit)
        db.flush()
        units_by_title[unit.title] = unit
        print(f"  Created course unit: {unit.title}")

        if course:
            link_exists = (
                db.query(CourseUnitLink)
                .filter(
                    CourseUnitLink.course_id == course.id,
                    CourseUnitLink.course_unit_id == unit.id,
                )
                .first()
            )
            if not link_exists:
                db.add(
                    CourseUnitLink(course_id=course.id, course_unit_id=unit.id)
                )
                print(f"    Linked unit to course: {course.title}")
    return units_by_title


def _seed_intakes(db, courses_by_title: dict[str, Course]) -> None:
    for data in SEED_INTAKES:
        existing = db.query(Intake).filter(Intake.name == data["name"]).first()
        if existing:
            print(f"  Intake exists: {existing.name}")
            continue

        course_ids = [
            courses_by_title[title].id
            for title in data["course_titles"]
            if title in courses_by_title
        ]
        intake = Intake(
            name=data["name"],
            year_level=data["year_level"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            enrollment_deadline=data["enrollment_deadline"],
            capacity=data["capacity"],
            enrolled_count=0,
            course_ids=",".join(course_ids),
            status=data["status"],
        )
        db.add(intake)
        print(f"  Created intake: {intake.name}")


def _seed_enrollments(
    db,
    intakes_by_name: dict[str, Intake],
    courses_by_title: dict[str, Course],
) -> dict[str, Enrollment]:
    enrollments_by_key: dict[str, Enrollment] = {}

    for data in SEED_ENROLLMENTS:
        student = db.query(User).filter(User.email == data["student_email"]).first()
        intake = intakes_by_name.get(data["intake_name"])
        course = courses_by_title.get(data["course_title"])
        if not student or not intake or not course:
            print(f"  Skipped enrollment (missing refs): {data['student_email']}")
            continue

        key = f"{student.id}:{intake.id}:{course.id}"
        existing = (
            db.query(Enrollment)
            .filter(
                Enrollment.student_id == student.id,
                Enrollment.intake_id == intake.id,
                Enrollment.course_id == course.id,
            )
            .first()
        )
        if existing:
            enrollments_by_key[key] = existing
            print(f"  Enrollment exists: {data['student_email']} → {data['course_title']}")
            continue

        enrollment = Enrollment(
            student_id=student.id,
            intake_id=intake.id,
            course_id=course.id,
            status=data["status"],
            payment_status=data["payment_status"],
        )
        db.add(enrollment)
        db.flush()
        enrollments_by_key[key] = enrollment
        print(f"  Created enrollment: {data['student_email']} → {data['course_title']}")

        if data["status"] == "active":
            links = (
                db.query(CourseUnitLink)
                .filter(CourseUnitLink.course_id == course.id)
                .all()
            )
            for link in links:
                db.add(
                    StudentUnitEnrollment(
                        student_id=student.id,
                        enrollment_id=enrollment.id,
                        course_unit_id=link.course_unit_id,
                        course_id=course.id,
                        intake_id=intake.id,
                        status="active",
                    )
                )
            intake.enrolled_count = (intake.enrolled_count or 0) + 1

    return enrollments_by_key


def _seed_tutor_profiles(db) -> None:
    for data in SEED_TUTOR_PROFILES:
        lecturer = db.query(User).filter(User.email == data["lecturer_email"]).first()
        if not lecturer:
            print(f"  Skipped tutor profile (lecturer missing): {data['lecturer_email']}")
            continue

        existing = (
            db.query(TutorProfile)
            .filter(TutorProfile.user_id == lecturer.id)
            .first()
        )
        if existing:
            print(f"  Tutor profile exists: {data['lecturer_email']}")
            continue

        profile = TutorProfile(
            user_id=lecturer.id,
            subjects=data["subjects"],
            hourly_rate=data["hourly_rate"],
            bio=data["bio"],
            is_available=data["is_available"],
            approval_status=data["approval_status"],
        )
        db.add(profile)
        print(f"  Created tutor profile: {data['lecturer_email']} ({data['approval_status']})")


def _seed_payments(
    db,
    enrollments_by_key: dict[str, Enrollment],
) -> None:
    for data in SEED_PAYMENTS:
        student = db.query(User).filter(User.email == data["student_email"]).first()
        intake = db.query(Intake).filter(Intake.name == data["intake_name"]).first()
        course = db.query(Course).filter(Course.title == data["course_title"]).first()
        if not student or not intake or not course:
            print(f"  Skipped payment (missing refs): {data['request_reference']}")
            continue

        key = f"{student.id}:{intake.id}:{course.id}"
        enrollment = enrollments_by_key.get(key)
        if not enrollment:
            enrollment = (
                db.query(Enrollment)
                .filter(
                    Enrollment.student_id == student.id,
                    Enrollment.intake_id == intake.id,
                    Enrollment.course_id == course.id,
                )
                .first()
            )

        existing = (
            db.query(Payment)
            .filter(Payment.request_reference == data["request_reference"])
            .first()
        )
        if existing:
            print(f"  Payment exists: {data['request_reference']}")
            continue

        payment = Payment(
            student_id=student.id,
            enrollment_id=enrollment.id if enrollment else None,
            amount=data["amount"],
            phone_number=data["phone_number"],
            carrier=data["carrier"],
            payment_type="enrollment",
            status=data["status"],
            request_reference=data["request_reference"],
            response_code="00" if data["status"] == "completed" else None,
            response_message="Seeded payment" if data["status"] == "completed" else None,
            description=data["description"],
            completed_at=datetime.utcnow() if data["status"] == "completed" else None,
        )
        db.add(payment)
        print(f"  Created payment: {data['request_reference']}")


def _intakes_by_name(db) -> dict[str, Intake]:
    return {i.name: i for i in db.query(Intake).all()}


def seed_database():
    """Create tables and seed initial users and settings if they don't exist."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Seed users
        for user_data in SEED_USERS:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing:
                user = User(
                    name=user_data["name"],
                    email=user_data["email"],
                    hashed_password=hash_password(user_data["password"]),
                    role=user_data["role"],
                )
                db.add(user)
                print(f"  Created user: {user_data['email']} ({user_data['role']})")
            else:
                print(f"  User exists: {user_data['email']}")

        # Seed default settings
        for key, value in DEFAULT_SETTINGS.items():
            existing = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            if not existing:
                setting = SystemSetting(key=key, value=value)
                db.add(setting)
                print(f"  Created setting: {key}")
            else:
                print(f"  Setting exists: {key}")

        schools_by_code = _seed_schools(db)
        courses_by_title = _seed_courses(db, schools_by_code)
        _seed_course_units(db, courses_by_title)
        _seed_intakes(db, courses_by_title)

        intakes_by_name = _intakes_by_name(db)
        enrollments_by_key = _seed_enrollments(db, intakes_by_name, courses_by_title)
        _seed_tutor_profiles(db)
        _seed_payments(db, enrollments_by_key)

        db.commit()
        print("Database seeded successfully.")
    finally:
        db.close()
