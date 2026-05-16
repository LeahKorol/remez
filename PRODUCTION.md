# PRODUCTION DEPLOYMENT GUIDE

This document describes how to deploy and configure **REMEZ** in a production environment using Docker Compose and Nginx.

---

## 1. System Overview

REMEZ consists of four services:

* **Frontend** (React UI)
* **Backend** (Django REST API)
* **Pipeline** (FastAPI FAERS processing service)
* **PostgreSQL** (database)

All services are managed via a single root `docker-compose.yml`.

---

## 2. Environment Configuration

### 2.1 Root `.env` (Docker Compose)

The root `.env` file contains shared infrastructure configuration:

* Database credentials
* Shared service URLs
* Global runtime variables

---

### 2.2 Service Environment Files

Each service has:

* `backend/env.prof`
* `pipeline/env.prof`
* `frontend/env.prof`

These contain:

* Service-specific configuration
* API keys
* Runtime flags

---

### 2.3 Required Variables

Each service defines required environment variables in:

* `backend/.env.prod.example`
* `pipeline/.env.prod.example`
* `frontend/.env.prod.example`

These files are the **source of truth for production configuration**.

---

### 2.4 Load Order

1. Root `.env`
2. Service `env.prof`

---

## 3. Docker Deployment

Single compose file:

```text
docker-compose.yml
```

Includes:

* Backend
* Pipeline
* Frontend
* Postgres

---

## 4. FAERS Data Initialization

### 4.1 Auto Sync

```text
FAERS_AUTO_SYNC=True
```

When enabled:

* Pipeline deletes all FAERS raw files
* Pipeline re-downloads FAERS datasets
* Backend ingests new data into DB

---

### 4.2 Database Behavior

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
