# PRODUCTION DEPLOYMENT GUIDE

This document describes how to deploy and configure **REMEZ** in a production environment using Docker Compose and environment files.

---

## 1. System Overview

REMEZ consists of four services orchestrated by Docker Compose:

* **Frontend** (React UI)
* **Backend** (Django REST API)
* **Pipeline** (FastAPI FAERS processing service)
* **PostgreSQL** (database)

---

## 2. Compose Files Strategy

### 2.1 Core Principle

All configuration is **environment-file-driven** using two compose files:

- `docker-compose.yml` for local development
- `docker-compose.prod.yml` for production

The production compose file already references `backend/.env.prod`, `frontend/.env.prod`, and `pipeline/.env.prod` directly, so no runtime patching is required.

```bash
# Local
docker compose up --build

# Production
docker compose -f docker-compose.prod.yml up --build -d
```

### 2.2 Environment File Organization

Each service has two environment file variants:

| Service | Local | Production |
|---------|-------|------------|
| Backend | `backend/.env` | `backend/.env.prod` |
| Frontend | `frontend/.env` | `frontend/.env.prod` |
| Pipeline | `pipeline/.env` | `pipeline/.env.prod` |

### 2.3 Configuration Sources (by service)

**Backend Environment Variables:**
- `backend/.env.prod.example` — template with all required variables
- Includes: database config, API URLs (FRONTEND_URL, BACKEND_URL, PIPELINE_BASE_URL), JWT settings, email config, FAERS bounds
- **Local**: DEBUG=True, FAERS_AUTO_SYNC=True, localhost URLs
- **Production**: DEBUG=False, FAERS_AUTO_SYNC=False, production URLs (https://remez.jce.ac)

**Frontend Environment Variables:**
- `frontend/.env.prod.example` — template with required variables
- Includes: REACT_APP_API_BASE, REACT_APP_GOOGLE_CLIENT_ID, REACT_APP_GOOGLE_REDIRECT_URI
- **Local**: http://localhost:3000 callback URI
- **Production**: https://remez.jce.ac callback URI

**Pipeline Environment Variables:**
- `pipeline/.env.prod.example` — template with required variables
- Includes: PIPELINE_CALLBACK_URL (for results posting), FAERS bounds, FAERS_AUTO_SYNC flag
- **Local**: Points to Docker service names (backend:8000, pipeline-api:8000)
- **Production**: Points to deployed origin or internal service names

---

## 3. Deployment Steps

### 3.1 Prepare Production Environment Files

1. **Copy templates to production files:**
   ```bash
   cp backend/.env.prod.example backend/.env.prod
   cp frontend/.env.prod.example frontend/.env.prod
   cp pipeline/.env.prod.example pipeline/.env.prod
   ```

2. **Update values in each `.env.prod` file:**
   - Backend: Update `BACKEND_URL`, `FRONTEND_URL`, `PIPELINE_BASE_URL`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`
   - Frontend: Update `REACT_APP_GOOGLE_REDIRECT_URI` to match your deployment domain
   - Pipeline: Ensure `PIPELINE_CALLBACK_URL` points to your deployed backend

3. **Verify Google OAuth:**
   - Add your production domain to [Google Cloud Console](https://console.cloud.google.com/apis/credentials) authorized redirect URIs
   - Ensure `frontend/.env.prod` has the correct `REACT_APP_GOOGLE_REDIRECT_URI`

### 3.2 Deploy with Docker Compose

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Notes:
- Only Nginx is exposed publicly on port `8600`.
- Backend, frontend, pipeline-api, and PostgreSQL remain internal-only.
- Production resource limits are defined in `docker-compose.prod.yml`.

### 3.3 Initialize Database

The Django entrypoint automatically runs migrations on startup. Verify with:

```bash
docker compose logs backend | grep -i migration
```

---

## 4. FAERS Data Initialization

### 4.1 Auto Sync Configuration

- **Local development** (`backend/.env`): `FAERS_AUTO_SYNC=True`
  - Downloads FAERS data automatically on startup
  - Pipeline processes data in background

- **Production** (`backend/.env.prod`): `FAERS_AUTO_SYNC=False`
  - Prevents automatic downloads in production
  - Configure FAERS sync during off-peak hours via management commands

### 4.2 Manual FAERS Data Refresh

If needed during production:

```bash
docker compose exec backend python manage.py download_faers_data --quarters 2020q1 2020q2 2020q3
```

---

## 5. Monitoring & Observability

### 5.1 Backend Entrypoint Logging

The backend entrypoint now provides observable startup phases:

```
[backend-entrypoint] START: Running database migrations
[backend-entrypoint] OK: Database migrations completed
[backend-entrypoint] START: Starting Django development server
[backend-entrypoint] OK: Server ready on port 8000
```

Check logs with:
```bash
docker compose logs -f backend
```

### 5.2 Log Levels

Control verbosity via `ROOT_LOG_LEVEL` in backend `.env`/`.env.prod`:
- Local: `DEBUG`
- Production: `INFO` or `WARNING`

---

## 6. Database Behavior

* Backend is **append-only**
* No DB reset or deletion occurs

---

## 5. Required FAERS Range

```text
FAERS_FROM=<start>
FAERS_TO=<end>
```

Both are required.

If missing:

* Backend fails startup
* Pipeline fails startup

---

## 6. Data Flow Architecture

### 6.1 Pipeline Service

`pipeline/entrypoint.sh`

* Handles full re-download on auto sync
* Does NOT access DB

---

### 6.2 Backend Service

`backend/entrypoint.sh`

Executed on backend container startup.

#### Flow:

1. `cd /app`

2. Run migrations:

* `python manage.py migrate --noinput`
* Applies DB schema updates before startup

3. FAERS sync (conditional):

Runs only if:

* `FAERS_AUTO_SYNC=True`
* `FAERS_FROM` is set
* `FAERS_TO` is set

Then:

* `download_faers_data FAERS_FROM FAERS_TO --force` → downloads FAERS dataset
* `load_faers_terms FAERS_FROM FAERS_TO` → processes and loads data into DB

If not set:

* FAERS sync is skipped

4. Start server:

* `python manage.py runserver 0.0.0.0:8000`

---

## 7. Startup Flow

1. Docker Compose starts all services
2. `.env` + `env.prof` loaded
3. Pipeline downloads FAERS data
4. Backend ingests data
5. System is ready

---

## 8. Deployment Hardening (from Issue #182)

### 8.1 Nginx Entry Point

Single entry point:

```text
http://localhost:8600 → https://remez.jce.ac
```

Routes:

| Path      | Service         |
| --------- | --------------- |
| `/`       | Frontend (3000) |
| `/api/`   | Backend (8000)  |
| `/admin/` | Backend         |
| Pipeline  | Internal only   |

---

### 8.2 Frontend Routing Rules

Frontend MUST:

* Use `/api/v1` only
* NOT use `localhost:8000`
* NOT use `127.0.0.1:8000`
* Rely on Nginx proxy (`/api → backend`)

---

### 8.3 `/admin/` Access Restriction

Must be restricted in Nginx:

```nginx
location /admin/ {
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 127.0.0.1;
    deny all;

    proxy_pass http://backend:8000;
}
```

---

### 8.4 Pipeline Exposure Rules

* Pipeline must NOT be exposed externally
* Only backend can access it internally

---

### 8.5 Backend → Pipeline Communication

Must use:

```text
PIPELINE_BASE_URL=http://pipeline-api:8000
```

Not localhost.

---

### 8.6 Security Defaults

Must be set:

* `JWT_AUTH_SECURE=True`
* `JWT_AUTH_HTTPONLY=True`

---

### 8.7 Pipeline Callback Access Control

* If `PIPELINE_SERVICE_IPS` is missing:

  * Production MUST deny all requests
  * No fallback to open access

---

### 8.8 Nginx Production Configuration Requirements

Nginx must:

* Listen on port `8600`
* Serve as **single entry point**
* Proxy frontend + backend
* Keep pipeline internal only
* Set:

  * `client_max_body_size 10m`
  * `proxy_read_timeout 120s`

---

## 9. Health Endpoint

Required:

```text
/api/v1/health/
```

Used for:

* Deployment verification
* Service monitoring
* Nginx checks
