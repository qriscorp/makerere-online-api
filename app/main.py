from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.routers import auth, users, schools, courses, course_units, intakes, intake_assignments
from app.routers import settings as settings_router
from app.routers import materials, assessments, virtual_classes, tutoring, subjects, enrollments, uploads, assessment_questions, payments
from app.routers import payments as payments_router
from app.seed import seed_database

app = FastAPI(
    title="Makerere Online University API",
    description="Backend API for the Makerere Online University Management System",
    version="1.0.0",
)

# Build CORS origins from config + defaults
cors_origins = [
    "http://localhost:5173",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:3535",
    "https://makerereonlineschool.com",
    "https://www.makerereonlineschool.com",
]
if settings.cors_origins:
    cors_origins.extend([o.strip() for o in settings.cors_origins.split(",") if o.strip()])
if settings.frontend_url:
    cors_origins.append(settings.frontend_url)
cors_origins = list(set(cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(schools.router)
app.include_router(courses.router)
app.include_router(course_units.router)
app.include_router(intakes.router)
app.include_router(intake_assignments.router)
app.include_router(settings_router.router)
app.include_router(materials.router)
app.include_router(assessments.router)
app.include_router(virtual_classes.router)
app.include_router(tutoring.router)
app.include_router(subjects.router)
app.include_router(enrollments.router)
app.include_router(uploads.router)
app.include_router(assessment_questions.router)
app.include_router(payments.router)
app.include_router(payments_router.router)

# Mount static files for uploaded images
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.on_event("startup")
def on_startup():
    """Create tables and seed initial users."""
    seed_database()


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Makerere Online University API"}
