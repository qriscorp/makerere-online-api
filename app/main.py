from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth

app = FastAPI(
    title="Makerere Online University API",
    description="Backend API for the Makerere Online University Management System",
    version="1.0.0",
)

# CORS — allow the frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3535",
        "https://makerereonlineschool.com",
        "https://www.makerereonlineschool.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Makerere Online University API"}
