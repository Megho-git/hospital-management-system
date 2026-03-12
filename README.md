# MedFlow HMS - Hospital Management System

A professional, market-ready Hospital Management System with Flask (backend), Vue 3 + Vite + Tailwind CSS 4 (frontend), SQLite/Postgres, Redis, and Celery.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, Vite, Tailwind CSS 4, Lucide Icons, Vue Router, Axios |
| Backend | Flask 3, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Caching, Flask-Limiter |
| Database | SQLite (dev) / PostgreSQL (production) |
| Async | Celery 5 + Redis (exports, reminders, reports) |
| Email | SMTP via stdlib (configurable; mock-logs when unconfigured) |
| Deployment | Docker Compose (frontend, backend, redis, celery worker, celery beat) |

---

## Quick Start (Local Dev)

**1. Backend**

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac
cp .env.example .env        # Edit with your values
pip install -r requirements.txt
python app.py
```

Runs at http://localhost:5000

**2. Frontend**

```bash
cd frontend
npm install
npm run dev
```

Runs at http://localhost:5173 (proxies `/api` to backend)

**3. Redis** (optional for caching/async)

```bash
redis-server
```

**4. Celery** (optional)

```bash
cd backend
celery -A tasks worker -l info            # worker
celery -A tasks beat -l info              # scheduler
```

---

## Docker Compose (Production)

```bash
cp backend/.env.example backend/.env      # Fill in values
docker compose up --build -d
```

Services: frontend (:80), backend (:5000), redis, celery-worker, celery-beat.

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

| Variable | Purpose | Required |
|---|---|---|
| `SECRET_KEY` | Flask secret key | Yes |
| `JWT_SECRET_KEY` | JWT signing key | Yes |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | Yes |
| `REDIS_URL` | Redis for cache | For caching |
| `CELERY_BROKER_URL` | Celery broker | For async tasks |
| `CELERY_RESULT_BACKEND` | Celery results backend | For async tasks |
| `MAIL_SERVER` | SMTP server host | For real emails |
| `MAIL_PORT` | SMTP port | For real emails |
| `MAIL_USERNAME` | SMTP username | For real emails |
| `MAIL_PASSWORD` | SMTP password / app password | For real emails |
| `MAIL_DEFAULT_SENDER` | Default sender email | For real emails |
| `ADMIN_USERNAME` | Initial admin username | First deploy only |
| `ADMIN_EMAIL` | Initial admin email | First deploy only |
| `ADMIN_PASSWORD` | Initial admin password | First deploy only |

---

## Features by Role

### Admin
- Dashboard with KPI stats (doctors, patients, appointments, departments)
- Full CRUD for doctors (add, edit, delete, activate/block)
- View and filter all patients (search, block/unblock)
- View all appointments with status filtering
- **Medication Catalog**: manage standardized medication list used in prescriptions
- CSV data export (via Celery)
- Profile management with password change

### Doctor
- Dashboard: upcoming appointments, history, assigned patients
- Appointment lifecycle: **Confirm**, **Complete** (with treatment notes), **Cancel**, **No-show**
- Treatment management: diagnosis, prescription, medicines, visit type, notes
- **Structured prescribing**: search catalog, add dose/frequency/duration/instructions per medicine
- 7-day availability scheduler with time slot management
- Patient treatment history viewer with edit capability
- Profile management

### Patient
- Self-registration with medical info (phone, gender, DOB, blood group)
- Department browser with doctor listings
- Doctor profile viewer with availability
- **Visual slot picker**: see available 30-min slots, click to book
- Appointment management: reschedule, cancel
- **Printable appointment summary** with treatment record
- Treatment history with search and medicine tags
- Treatment history shows **structured prescriptions** when available
- Export own treatment history (via Celery)
- Profile management

---

## Architecture

### Frontend (`frontend/src/`)
- `layouts/AppLayout.vue` - Sidebar + topbar shell, role-aware navigation
- `components/` - Reusable UI: PageHeader, SectionCard, StatCard, DataTable (pagination/search), StatusChip, EmptyState, SkeletonLoader, ConfirmDialog, ToastContainer
- `composables/` - useToast, useApi
- `views/` - Role-specific pages (admin/, doctor/, patient/)

### Backend (`backend/`)
- `application/` - App factory, config, models, extensions (SQLAlchemy, JWT, CORS, Cache, Limiter)
- `api/` - Blueprints: auth, admin, doctor, patient
- `utils/` - Helpers (serializers, role decorator), email utility
- `tasks/` - Celery jobs (daily reminders, monthly reports, CSV exports)
- `tests/` - Pytest test suite

### Pharma Module (Medication Catalog + Prescriptions)
- **Models**: `Medication`, `TreatmentMedication` (structured prescription items linked to a treatment)
- **Admin APIs**:
  - `GET/POST /api/admin/medications`
  - `PUT/DELETE /api/admin/medications/:id`
- **Doctor APIs**:
  - `GET /api/doctor/medications?q=...` (search active catalog)
  - `PUT /api/doctor/appointments/:id/complete` accepts `prescribed_medicines: []`
  - `PUT /api/doctor/treatments/:id` accepts `prescribed_medicines: []`

### Production Features
- Rate limiting (15/min login, 10/min register, 200/min global)
- Structured logging with timestamps
- Global error handlers (HTTP errors, 429, 500)
- Docker Compose with health checks
- SMTP email integration (with mock fallback)
- Print-friendly appointment summaries

---

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

---

## Notes

- Without Redis/Celery the app runs fine; caching and exports won't work.
- Without SMTP credentials, emails are logged to console (mock mode).
- SQLite DB is auto-created at `backend/instance/hms.db` on first run.
