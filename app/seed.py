"""Seed the database with initial users on startup."""
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.school import School  # noqa: F401 — ensures schools table is created
from app.models.course import Course  # noqa: F401 — ensures courses table is created
from app.models.course_unit import CourseUnit  # noqa: F401 — ensures course_units table is created
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
        "name": "Aisha Nansubuga",
        "email": "firststudent@makonline.com",
        "password": "123456789",
        "role": "student",
    },
]


def seed_database():
    """Create tables and seed initial users if they don't exist."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
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
        db.commit()
        print("Database seeded successfully.")
    finally:
        db.close()
