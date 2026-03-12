## MedFlow HMS – Production Deployment & Hardening Guide

This guide assumes you are deploying the **existing, fully working app** to a staging/production environment. It focuses on security, reliability, and performance, not on changing core behaviour.

---

## 1. Core production checklist

- **Database**
  - Use **PostgreSQL** instead of SQLite.
  - Set `SQLALCHEMY_DATABASE_URI` to a managed Postgres instance (with TLS if available).
  - Configure daily backups (e.g. cloud snapshots or pg_dump to object storage).

- **Secrets**
  - Set strong random values for `SECRET_KEY` and `JWT_SECRET_KEY`.
  - Never commit `.env` files; manage secrets via your orchestrator (Docker secrets, Kubernetes secrets, etc.).

- **TLS / Reverse proxy**
  - Place Nginx, Caddy, or a cloud load balancer in front of the app.
  - Terminate HTTPS at the proxy and forward traffic to the backend container.
  - Enforce HTTPS redirects and HSTS at the edge.

- **Celery & Redis**
  - Run Redis as a dedicated service (or managed cache).
  - Run at least:
    - 1 Celery worker (for exports, notifications, future background jobs).
    - 1 Celery beat scheduler (for scheduled jobs).

- **Rate limiting & CORS**
  - The app already enables **Flask-Limiter** with sane defaults.
  - For a single-origin frontend, lock CORS down to your production domain in `Config` or via env.

---

## 2. Environment configuration (backend)

Copy `backend/.env.example` to `backend/.env` and set at minimum:

- **Core**
  - `SECRET_KEY`, `JWT_SECRET_KEY`
  - `SQLALCHEMY_DATABASE_URI` (Postgres)
  - `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`

- **Admin bootstrap**
  - `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` (only used on first run)

- **Email**
  - `MAIL_*` variables for real SMTP

- **Telemedicine (optional)**
  - `TWILIO_ACCOUNT_SID`, `TWILIO_API_KEY`, `TWILIO_API_SECRET`

- **AI (optional)**
  - `AI_FEATURES_ENABLED=true`
  - `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT_CHAT`

- **Object storage (EHR documents, lab result files)**
  - `OBJECT_STORE_PROVIDER` = `local` (default), `minio`, or `s3`
  - When using MinIO/S3, set endpoint, bucket, access/secret keys, and (optionally) a public base URL.

---

## 3. Frontend build & hosting

- Build once, serve statically:
  - `cd frontend && npm install && npm run build`
  - Host `frontend/dist` behind the same reverse proxy as the backend (or a CDN).
  - Configure the proxy so that:
    - `/` → frontend static files
    - `/api` → Flask backend service

- For better perceived performance:
  - Enable HTTP/2 or HTTP/3 on your TLS terminator.
  - Set long-lived cache headers for versioned static assets (Vite fingerprints filenames).

---

## 4. Logging, monitoring, and alerts

- **Backend logs**
  - By default, the app logs structured messages to stdout with timestamps.
  - In Docker/Kubernetes, ship stdout/stderr to a central log system (CloudWatch, Loki, ELK, etc.).

- **Access logs**
  - Enable access logging at the reverse proxy.
  - Monitor 4xx/5xx rates, request latency, and rate-limit hits (429s).

- **Health checks**
  - Use a simple HTTP health endpoint (e.g. `/api/auth/ping` or `/api/auth/login` with a synthetic account) for container health checks.
  - Configure container/orchestrator health checks with sensible timeouts and retries.

---

## 5. Security hardening

- **Authentication**
  - Encourage enabling MFA (already built-in) for admin/doctor accounts.
  - Rotate JWT secrets on a schedule (with downtime-free rotation strategy if required).

- **Network**
  - Restrict database and Redis to internal network only.
  - Only expose the reverse proxy to the public internet.

- **Data protection**
  - Ensure database and object storage volumes are encrypted at rest.
  - Use TLS for all external service connections where supported (Postgres, Redis, object storage, SMTP).

---

## 6. Performance tuning (optional)

The current bundle is acceptable for many deployments, but for very large installations:

- Consider **code-splitting heavy views** (e.g. admin analytics, telemedicine room) into lazy-loaded routes.
- Scale horizontally by:
  - Running multiple backend instances behind the proxy.
  - Running multiple Celery workers for background tasks.

These optimisations are not required to run the system, but can be applied as usage grows.

