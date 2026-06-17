# Makerere Online University API

FastAPI backend for the Makerere Online University Management System.

## Quick Start

### Full stack (API + DB + Dashboard)

From the project root (`makerere project/`):

```bash
docker compose up --build -d
```

| Service    | URL                          |
|------------|------------------------------|
| Dashboard  | http://localhost:3535        |
| API        | http://localhost:3434        |
| API docs   | http://localhost:3434/docs   |
| Postgres   | localhost:3435               |

### API only

```bash
cd makerere-online-api
cp .env.example .env
docker compose up --build -d
```

API available at `http://localhost:3434`
Docs at `http://localhost:3434/docs`

On startup, the API seeds sample data (if not already present):

| Entity | Count | Examples |
|--------|-------|----------|
| Schools | 2 | School of Computing and Informatics (SCI), School of Business and Management (SBM) |
| Courses | 2 | BSc Computer Science, BBA |
| Course units | 2 | Data Structures and Algorithms, Principles of Management |
| Intakes | 2 | August 2026 Intake, January 2027 Intake |

Seed logic lives in `app/seed.py` and is idempotent (safe to restart).

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
