# Backend - Django REST API

A Django REST Framework-based backend service for the REMEZ project, providing comprehensive API endpoints for user authentication, FAERS (FDA Adverse Event Reporting System) data analysis, and data management capabilities.

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Environment Setup](#environment-setup)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Key Features](#key-features)

## Overview

This Django backend serves as the core API service for the REMEZ project, handling:
- **User Management**: Registration, authentication, and authorization using JWT tokens
- **FAERS Analysis**: FDA Adverse Event Reporting System data processing and analysis coordination
- **Pipeline Service Integration**: Acts as a coordinator that communicates with an external pipeline service that performs the actual statistical calculations and data processing
- **Query & Result Management**: Manages analysis queries, tracks computation progress, and stores results
- **API Documentation**: Automated OpenAPI/Swagger documentation

## Project Structure

```
backend/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── pytest.ini                  # Pytest configuration
├── dockerfile                  # Docker configuration
├── logs/                        # Application logs (auto-generated)
├── templates/                   # HTML templates
│   ├── account/                 # Authentication templates
│   └── errors/                  # Error page templates
├── backend/                     # Core Django configuration
│   ├── __init__.py
│   ├── settings.py              # Main Django settings
│   ├── test_settings.py         # Test-specific settings
│   ├── urls.py                  # Root URL configuration
│   ├── wsgi.py                  # WSGI application entry point
│   ├── asgi.py                  # ASGI application entry point
│   └── logging_formatters.py    # Custom logging formatters
├── users/                       # User management app
│   ├── models.py                # User model definitions
│   ├── views.py                 # Authentication views
│   ├── serializers.py           # API serializers
│   ├── urls.py                  # User-related URLs
│   ├── adapters.py              # Custom auth adapters
│   ├── google_auth.py           # Google OAuth integration
│   ├── middleware.py            # Custom middleware
│   ├── forms.py                 # Django forms
│   ├── admin.py                 # Django admin configuration
│   ├── apps.py                  # App configuration
│   ├── migrations/              # Database migrations
│   └── tests/                   # User app tests
└── analysis/                    # FAERS analysis app
    ├── models.py                # Analysis data models
    ├── views.py                 # Analysis API views
    ├── serializers.py           # Analysis serializers
    ├── urls.py                  # Analysis URLs
    ├── constants.py             # Application constants
    ├── permissions.py           # Custom permissions
    ├── utils.py                 # Utility functions
    ├── email_service.py         # Email notification service
    ├── django_setup.py          # Django configuration helper
    ├── admin.py                 # Admin interface
    ├── apps.py                  # App configuration
    ├── faers_analysis/          # FAERS-specific analysis modules
    ├── management/              # Django management commands
    ├── services/                # Business logic services
    ├── migrations/              # Database migrations
    └── tests/                   # Analysis app tests
```

## Environment Setup

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
# Django Core Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration (Supabase PostgreSQL)
# For local PostgreSQL, use the same values for both pooled and direct settings
DB_NAME=your_database_name
DB_USER_POOLED=your_pooled_user
DB_PASSWORD=your_database_password
DB_HOST_POOLED=your_pooled_host
DB_PORT_POOLED=6543
DB_USER_DIRECT=your_direct_user
DB_HOST_DIRECT=your_direct_host
DB_PORT_DIRECT=5432

# JWT Authentication
SIGNING_KEY=your-jwt-signing-key
JWT_AUTH_COOKIE=jwt-access
JWT_AUTH_REFRESH_COOKIE=jwt-refresh
JWT_AUTH_SECURE=False
JWT_AUTH_HTTPONLY=False
ACCESS_TOKEN_LIFETIME_HOURS=1
REFRESH_TOKEN_LIFETIME_DAYS=7

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Email Configuration (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Frontend Integration
# Password reset emails will include links that redirect to the frontend URL
FRONTEND_URL=http://localhost:3000
PASSWORD_RESET_CONFIRM_REDIRECT_BASE_URL=http://localhost:3000/reset-password/

# Logging
ROOT_LOG_LEVEL=DEBUG

# Analysis Configuration

# Num of quarters of demo data to use for the analysis pipeline
# defaults is -1 , i.e. use real data
# For testing, use a number between 0 and 4
NUM_DEMO_QUARTERS=-1

# Pipeline Service

# IP address of the pipeline service allowed to access certain endpoints
# Can be a comma-separated list of IPs for multiple allowed services
PIPELINE_SERVICE_IPS=127.0.0.1,localhost
PIPELINE_BASE_URL=http://localhost:8001
PIPELINE_TIMEOUT=30 # timeout (minutes) for sending a request to the pipeline
```

### Prerequisites

- Python 3.9+
- PostgreSQL database (recommended: Supabase)
- Virtual environment (venv or conda)

## Installation & Setup

1. **Create and activate virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Copy the example `.env` above and fill in your actual values
   - Ensure your PostgreSQL database is accessible

4. **Run database migrations:**
   ```powershell
   python manage.py migrate
   ```

5. **Create superuser (optional):**
   ```powershell
   python manage.py createsuperuser
   ```

## Running the Application

### Development Server

```powershell
# Standard run
python manage.py runserver

# Run on specific port
python manage.py runserver 8000

# Run with no-reload (recommended for Windows to avoid file locking issues)
python manage.py runserver --noreload
```

The API will be available at `http://localhost:8000/`

### Docker (Alternative)

```powershell
docker build -t remez-backend .
docker run -p 8000:8000 --env-file .env remez-backend
```

## Testing

### Running Unit Tests

The project uses **pytest** with Django integration for testing.

```powershell
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest users/tests/test_models.py

# Run specific test class
pytest users/tests/test_models.py::TestUserModel

# Run specific test method
pytest users/tests/test_models.py::TestUserModel::test_user_creation
```

### Test Configuration

- Test settings: `backend/test_settings.py`
- Pytest configuration: `pytest.ini`
- Tests are located in `*/tests/` directories within each app 

### Coverage Reports

When you run tests, coverage reports are generated automatically according to configuration in pytests.ini file. To view the detailed HTML coverage report:

1. Run the tests:
   ```powershell
   pytest
   ```

2. Open the generated coverage report:
   - Navigate to the `htmlcov/` directory in your file explorer
   - Open `index.html` in your web browser

## API Documentation

### Interactive API Documentation

Once the server is running, you can access the API documentation:

- **Swagger UI**: http://localhost:8000/api/v1/docs/
- **OpenAPI Schema**: http://localhost:8000/api/v1/schema/ (downloads YAML file)

### Key API Endpoints

#### Authentication (`/api/v1/auth/`)
- `POST /api/v1/auth/registration/` - User registration
- `POST /api/v1/auth/login/` - User login
- `POST /api/v1/auth/logout/` - User logout
- `POST /api/v1/auth/password/reset/` - Password reset (sends reset link to frontend URL)
- `GET /api/v1/auth/user/` - Get current user details

#### Analysis (`/api/v1/analysis/`)

**Query Management:**
- `GET /api/v1/analysis/queries/` - List all analysis queries for the authenticated user
- `POST /api/v1/analysis/queries/` - Create a new FAERS analysis query
- `GET /api/v1/analysis/queries/{id}/` - Retrieve specific query details
- `PUT /api/v1/analysis/queries/{id}/` - Update an existing query
- `PATCH /api/v1/analysis/queries/{id}/` - Partially update a query
- `DELETE /api/v1/analysis/queries/{id}/` - Delete a query

**Results Management:**
- `GET /api/v1/analysis/results/` - List all analysis results for the authenticated user 
- `GET /api/v1/analysis/results/{id}/` - Retrieve specific result details
- `PUT /api/v1/analysis/results/{id}/` - Update result status (accessed bypipeline service only)

**Drug and Reaction Name Search:**
- `GET /api/v1/analysis/drug-names/search/{prefix}` - Search for drug names in the FAERS database (minimum 3 characters)
- `GET /api/v1/analysis/reaction-names/search/{prefix}` - Search for adverse reaction names in the FAERS database (minimum 3 characters)

> **Search Usage**: These endpoints are used by the frontend to provide autocomplete functionality when users are building Query objects. The search prefix must be at least 3 characters long to return results.

> **Note**: The backend acts as a **coordinator** - when a query is created or updated, it sends requests to the external **Pipeline Service** which performs the actual statistical calculations. The backend then receives and stores the final results.

### Authentication

The API uses **JWT (JSON Web Tokens)** for authentication:
- Access tokens are valid for 1 hour (configurable)
- Refresh tokens are valid for 7 days (configurable)
- Tokens are stored as HTTP-only cookies for security

### Pipeline Service Integration

The backend integrates with an external **Pipeline Service** that handles the computational heavy lifting:

#### Architecture Flow:
1. **User creates/updates** an analysis query via the Django backend API
2. **Backend validates** the query parameters and stores it in the database
3. **Backend triggers** the Pipeline Service (running by default on `http://localhost:8001`) with the query parameters
4. **Pipeline Service** performs the actual FAERS data analysis:
   - Downloads and processes FAERS quarterly data
   - Calculates Reporting Odds Ratios (ROR)
   - Performs statistical analysis
   - Generates visualizations and reports
5. **Pipeline Service** sends results back to the backend
6. **Backend stores** the results and updates the query status
7. **User receives** notification when analysis is complete

#### Configuration:
```env
PIPELINE_BASE_URL=http://localhost:8001
PIPELINE_TIMEOUT=30
PIPELINE_SERVICE_IPS=127.0.0.1,localhost
```

#### Key Integration Points:
- **Async Processing**: Analysis runs asynchronously - users can track progress via result status
- **Security**: Pipeline service IP validation for secure communication
- **Error Handling**: Comprehensive error handling
- **Result Storage**: Final results are stored in the backend database for fast retrieval

## Development

### Key Django Apps

1. **users** - User authentication and management
2. **analysis** - FAERS data analysis and processing

### Database

The application uses PostgreSQL, configured for:
- **Supabase (recommended)**: Uses different connections for pooled (port 6543) and direct (port 5432) access
- **Local PostgreSQL**: If not using Supabase, set the same values for both pooled and direct settings (typically `localhost:5432`)

### Logging

Logs are configured with:
- Console output with colors for development
- File rotation (10MB max, 3 backups)
- Custom formatters showing relative file paths

### Code Quality

- Use **pytest** and **pytest-mock** for testing
- Follow Django best practices
- Use environment variables for configuration
- Implement proper error handling and logging

## Key Features

- **JWT Authentication** with refresh token rotation
- **Email verification** and password reset
- **PostgreSQL integration** with connection pooling
- **API documentation** with Swagger/OpenAPI
- **CORS support** for frontend integration
- **Comprehensive logging** with rotation
- **Docker support** for containerized deployment
- **Test coverage** with pytest and coverage reporting
- **Pipeline service integration** - Communicates with external calculation service
- **Real-time result tracking** and status monitoring
- **Drug/Reaction name search** with autocomplete functionality

---

For more information about specific components, refer to the individual app directories and their respective documentation.