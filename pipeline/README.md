# FAERS Analysis Pipeline API

A FastAPI-based service for running and managing FAERS (FDA Adverse Event Reporting System) data analysis pipelines. This system provides a robust API for executing pharmaceutical safety analyses with background processing, task management, and result tracking.

## Attribution

This pipeline executes the core FAERS analysis logic developed by **Dr. Boris Gorelik**, with modifications to adapt it for integration into the REMEZ web platform. The majority of the analysis implementation in `mark_data.py`, `report.py`, and `utils.py` files was written by Dr. Gorelik.

**Original Repository:** https://github.com/bgbg/faers_analysis

## Features

- **RESTful API** for triggering FAERS pipeline analysis jobs
- **Background processing** with multiprocessing support for CPU-intensive tasks
- **SQLite rotating buffer** for efficient task management and result storage
- **Comprehensive logging** with per-task log files and rotating handlers
- **Health checks** and readiness monitoring
- **Data availability checking** for FAERS quarters
- **Automatic result cleanup** with configurable retention policies
- **Task status tracking** throughout the analysis lifecycle

## Project Structure

```
pipeline/
├── api/                          # FastAPI application structure
│   └── v1/                       # API version 1
│       ├── router.py             # Main API router
│       └── routes/               # API endpoints definitions
│           ├── health.py         # Health check endpoints
│           └── pipeline.py       # Pipeline management endpoints
├── core/                         # Core application components
│   ├── config.py                 # Configuration management
│   ├── logging.py                # Logging setup and configuration
│   ├── health_checks.py          # Health check implementations
│   └── http_client.py            # HTTP client utilities
├── services/                     # Business logic layer
│   ├── pipeline_service.py       # Main pipeline execution service
│   └── task_repository.py        # Task lifecycle management
├── models/                       # Data models and schemas
│   ├── models.py                 # SQLModel database models
│   └── schemas.py                # Pydantic request/response schemas
├── data/                         # Data storage directories
│   └── external/                 # External FAERS data files
├── pipeline_output/              # Analysis results output
├── logs/                         # Application and task-specific logs
├── tests/                        # Test suite
├── main.py                       # FastAPI application entry point
├── database.py                   # Database setup and session management
├── constants.py                  # Application constants and enums
├── errors.py                     # Custom exception definitions
└── requirements.txt              # Python dependencies
```

## Installation

### Prerequisites

- **Python 3.9+**
- **pip** package manager
- **FAERS data files** - Download and place quarterly FAERS data files in `data/external/faers/` (see [Data Requirements](#data-requirements) below)

### Environment Setup

1. **Clone the repository and navigate to the pipeline directory:**
   ```bash
   cd pipeline
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the pipeline directory with the following variables.
Change the values according to your preferences.

```env
# Application Settings
ENVIRONMENT=development
DEBUG=False
HOST=127.0.0.1
PORT=8001

# Logging Configuration
LOG_LEVEL=INFO

# Pipeline Processing Settings
PIPELINE_THREADS=7
PIPELINE_CLEAN_INTERNAL_DIRS=True
PIPELINE_MAX_WORKERS=20
PIPELINE_MAX_RESULTS=100
PIPELINE_MIN_RESULT_RETENTION_MINUTES=30

# Callback Configuration
PIPELINE_CALLBACK_URL=http://localhost:8000/api/v1/analysis/results/update-by-task

# Data Directories
DATA_EXTERNAL_DIR=data/external/faers
DATA_OUTPUT_DIR=pipeline_output
LOGS_DIR=logs

# Database Settings
SQLITE_FILE_NAME=database.sqlite3
DATABASE_URL=sqlite:///database.sqlite3
```

## Running the Application

### Development Mode

```bash
python main.py
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

### With Custom Configuration

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --log-level info
```

The API will be available at `http://localhost:8001` with interactive documentation at `http://localhost:8001/docs`.

## Data Requirements

The pipeline requires FAERS quarterly data files to be placed in the `data/external/faers/` directory. Each quarter requires four files:

- `demo{YYYYQX}.csv.zip` - Demographic data
- `drug{YYYYQX}.csv.zip` - Drug data  
- `reac{YYYYQX}.csv.zip` - Reaction data
- `outc{YYYYQX}.csv.zip` - Outcome data

Where `{YYYYQX}` represents the year and quarter (e.g., `2020q1` for 2020 Q1).

### Downloading FAERS Data

FAERS data files can be downloaded from NBER (National Bureau of Economic Research):

**For recent years (2018+):**
```
https://data.nber.org/fda/faers/{year}/{filetype}{yearquarter}.csv.zip
```

**For earlier years (2018 and before):**
```
https://data.nber.org/fda/faers/{year}/csv/{filetype}{yearquarter}.csv.zip
```

**Examples:**
- 2018 Q1 Demo data: `https://data.nber.org/fda/faers/2018/demo2018q1.csv.zip`
- 2020 Q1 Demo data: `https://data.nber.org/fda/faers/2020/csv/demo2020q1.csv.zip`

**Example for 2020 Q1:**
```
data/external/faers/
├── demo20q1.csv.zip
├── drug20q1.csv.zip
├── reac20q1.csv.zip
└── outc20q1.csv.zip
```

Use the `/api/v1/pipeline/data/available` endpoint to check which quarters have complete data before running analyses.

## API Endpoints

The API provides the following endpoints. For detailed request/response schemas and examples, see the interactive documentation at `http://localhost:8001/docs` when the service is running.

### Pipeline Management

- **POST /api/v1/pipeline/run** - Start a new FAERS analysis pipeline with specified parameters (year range, quarters, drugs, reactions, control groups)
- **GET /api/v1/pipeline/{task_id}** - Get status and results for a specific task
- **GET /api/v1/pipeline/status/{status}** - List tasks by status (`pending`, `running`, `completed`, `failed`)
- **GET /api/v1/pipeline/data/available** - Check available FAERS data quarters and completeness

### Health Monitoring

- **GET /api/v1/health** - Basic health check (liveness probe) - indicates if the application is running and responsive
- **GET /api/v1/health/ready** - Readiness check - verifies if the service is ready to accept traffic (checks database connectivity, external dependencies, etc.)

## Pipeline Workflow

The FAERS analysis pipeline implements a multiple-stages workflow designed for efficiency and reliability:

### 1. Task Creation and Management

**SQLite Rotating Buffer System:**
- The system maintains a configurable maximum number of task slots (`PIPELINE_MAX_RESULTS`)
- When capacity is reached, the oldest completed task details are overridden with new task data, reusing the same database location and log file
- Tasks must meet minimum retention time (`PIPELINE_MIN_RESULT_RETENTION_MINUTES`) before being eligible for reuse
- Internal data directories are deleted after task completion according to the `PIPELINE_CLEAN_INTERNAL_DIRS` environment variable
- Log files are preserved until overridden by a new task when it becomes the oldest completed task
- External ID are used for notifications when results are ready
- Thread-safe task creation prevents race conditions during high load

**Task Lifecycle:**
```
PENDING → RUNNING → COMPLETED/FAILED
```

### 2. Background Processing

**Multiprocess Execution:**
- Each analysis runs in a separate process via `ProcessPoolExecutor`
- Maximum concurrent workers configurable via `PIPELINE_MAX_WORKERS`
- Process isolation prevents memory leaks and ensures stability
- Independent logging per task prevents log output mixing

**Process Workflow:**
1. **Task Validation:** Verify input parameters and data availability
2. **Data Preparation:** Create directories for internal calculations
3. **Analysis Execution:** Run statistical analysis using Dr. Gorelik's code
4. **Result Processing:** Format and store analysis results in database
5. **Callback Notification:** Send results to external system via `PIPELINE_CALLBACK_URL`
6. **Cleanup:** Remove temporary files and update task status

### 3. Data Management

**FAERS Data Structure:**
- External FAERS data stored in `data/external/faers/`
- Quarterly data files (DEMO, DRUG, REAC, OUTC)
- Automatic validation of data completeness per quarter
- Support for multiple years and quarters in single analysis

**Output Management:**
- Temporary JSON files created in `pipeline_output/{task_id}/` during processing
- Internal directories are usually deleted immediately after processing (controlled by `PIPELINE_CLEAN_INTERNAL_DIRS`)
- Essential results (ROR values, confidence intervals) are extracted and saved in database.
- Database persistence ensures results remain available even if callback sending fails.

### 4. Error Handling and Recovery

**Robust Error Management:**
- Comprehensive exception handling at all levels
- Failed tasks marked with detailed error messages
- Automatic process cleanup on failure

**Monitoring and Observability:**
- Per-task log files for detailed debugging
- Rotating log handlers prevent disk space issues
- Health checks for system monitoring
- Structured logging with correlation IDs

### 5. Integration Points

**External System Integration:**
- Callback URLs for result notifications
- External ID mapping for result correlation
- REST API for seamless integration
- Standardized response formats

**Database Operations:**
- SQLite for lightweight, reliable persistence
- Atomic operations for data consistency
- Connection pooling for performance

## Performance Considerations

- **Concurrent Processing:** Multiple analyses can run simultaneously up to worker limit
- **Memory Management:** Process isolation prevents memory accumulation
- **Disk Usage:** Automatic cleanup and rotating logs manage storage
- **Response Times:** Background processing ensures API responsiveness
- **Scalability:** Configurable limits allow tuning for available resources

## Logging and Monitoring

The application provides comprehensive logging at multiple levels:

- **Application Logs:** General API and service logs in `logs/faers-api.log`
- **Task Logs:** Individual task execution logs in `logs/{task_id}.log`
- **Rotating Handlers:** Automatic log rotation (5MB per file, 3 backups)
- **Structured Logging:** Consistent format with timestamps, levels, and context

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_pipeline_service.py -v
```

## Troubleshooting

### Common Issues

**Pipeline capacity exceeded error:**
- Increase `PIPELINE_MAX_RESULTS` in `.env` file
- Check if old tasks can be cleaned up by reducing `PIPELINE_MIN_RESULT_RETENTION_MINUTES` or increasing `PIPELINE_MAX_RESULTS`

**Missing data files error:**
- Verify FAERS data files are in `data/external/faers/` with correct naming
- Use `/api/v1/pipeline/data/available` endpoint to check file completeness

**Task stuck in running state:**
- Check task-specific logs in `logs/{task_id}.log`
- Verify worker processes haven't exceeded `PIPELINE_MAX_WORKERS` limit
- Check application logs in `logs/faers-api.log`

**Database connection issues:**
- Ensure SQLite file permissions are correct
- Check `DATABASE_URL` configuration in `.env`

## License

This project is part of the REMEZ system. See the main project LICENSE file for details.

## Contributing

Please refer to the main project CONTRIBUTING.md for contribution guidelines and development practices.