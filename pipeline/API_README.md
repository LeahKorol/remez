# FAERS Pipeline API

A FastAPI service for running and managing FAERS data analysis pipelines.

## Features

- REST API for triggering FAERS pipeline jobs
- Background task processing
- Status tracking for pipeline runs
- JSON-based results

## Getting Started

### Prerequisites

- Python 3.9+
- FastAPI dependencies (see `requirements-api.txt`)
- Docker and Docker Compose (optional, for containerized deployment)

### Installation

1. Install the required dependencies:

```bash
pip install -r requirements-api.txt
```

2. Make sure the pipeline directory is in your Python path:

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/remez
```

### Running the API Service

#### Directly with Python

```bash
cd /path/to/remez
python pipeline/run_api.py
```

Options:
- `--host`: Host to bind the server to (default: 0.0.0.0)
- `--port`: Port to bind the server to (default: 8000)
- `--reload`: Enable hot reload for development
- `--log-level`: Log level (choices: debug, info, warning, error, critical)

#### Using Docker

```bash
cd /path/to/remez
docker-compose -f pipeline/docker-compose.api.yml up
```

## API Endpoints

### Run a Pipeline

Trigger a new pipeline run.

```
POST /pipeline/run
```

Request body:
```json
{
  "year_start": 2020,
  "year_end": 2021,
  "quarter_start": 1,
  "quarter_end": 4,
  "query_id": 123
}
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "started_at": "2025-09-16T12:34:56.789Z"
}
```

### Check Pipeline Status

Get the status of a specific pipeline run.

```
GET /pipeline/status/{task_id}
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "started_at": "2025-09-16T12:34:56.789Z",
  "completed_at": "2025-09-16T12:45:12.345Z",
  "results_file": "/path/to/results.json",
  "error": null
}
```

### List All Pipelines

Get a list of all pipeline runs.

```
GET /pipeline/list
```

Response:
```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "started_at": "2025-09-16T12:34:56.789Z",
      "completed_at": "2025-09-16T12:45:12.345Z",
      "results_file": "/path/to/results.json",
      "error": null
    }
  ]
}
```

## Status Values

- `pending`: The task has been created but not yet started
- `running`: The task is currently running
- `completed`: The task has completed successfully
- `failed`: The task failed with an error