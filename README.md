# CampusLedger (EdTech Analytics Platform)

Production-style student analytics dashboard with Django REST APIs + React UI.

## Tech
- Backend: Django + Django REST Framework
- DB: PostgreSQL (with SQLite fallback for quick local smoke tests)
- Frontend: React (Vite) + Tailwind + Recharts

## Backend setup (Windows PowerShell)
From the repo root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Configure PostgreSQL (recommended)
Set env vars (example):

```powershell
$env:DB_ENGINE="postgres"
$env:DB_NAME="hackathon"
$env:DB_USER="postgres"
$env:DB_PASSWORD="YOUR_PASSWORD"
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
```

Then run:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py generate_mock_data --students 200 --wipe
.\.venv\Scripts\python.exe manage.py runserver 8000
```

### SQLite fallback (no Postgres needed)

```powershell
$env:DB_ENGINE="sqlite"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py generate_mock_data --students 200 --wipe
.\.venv\Scripts\python.exe manage.py runserver 8000
```

Backend runs at `http://127.0.0.1:8000/` and APIs at `http://127.0.0.1:8000/api/`.

## Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at `http://127.0.0.1:5173/`.

If your backend runs on a different host/port, set:

```powershell
$env:VITE_API_BASE="http://127.0.0.1:8000/api"
```

## Key API routes
- `GET /api/students/`
- `GET /api/students/{id}/`
- `GET /api/students/{id}/grades/trend/`
- `GET /api/students/{id}/attendance/heatmap/?days=120`
- `GET /api/students/{id}/activities/timeline/`
- `GET /api/students/{id}/alerts/`
- `GET /api/students/{id}/health-score/`
- `GET /api/students/{id}/predict/`
- `GET /api/students/{id}/report.pdf`
- `GET /api/admin/analytics/?branch=CS&semester=3&subject=DBMS`
- `POST /api/admin/chat-query/` with JSON `{ "query": "Show students with attendance below 60% in Sem 3" }`

