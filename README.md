# Makerere Online University API

FastAPI backend for the Makerere Online University Management System.

## Quick Start

### With Docker (recommended)

```bash
cp .env.example .env
docker compose up --build -d
```

API available at `http://localhost:8000`
Docs at `http://localhost:8000/docs`

### Local Development

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /` — Health check
- `POST /api/auth/register` — Register a new user
- `POST /api/auth/login` — Login and get JWT token
- `GET /api/auth/me` — Get current user (requires auth)

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 (ORM)
- PostgreSQL
- JWT Authentication (python-jose)
- Pydantic v2 (validation)
- Alembic (migrations)
