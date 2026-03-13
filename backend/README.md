# AccessLens Backend Repository

Welcome to the backend orchestrator for AccessLens. We combine deterministic headless engines with advanced Vision and Language models to conduct comprehensive accessibility audits.

## Local Setup

### 1. Requirements
Ensure you have Python 3.10+ installed and Docker/Docker Compose ready.

### 2. Environment
Copy `.env.example` to `.env` and fill in necessary database configurations and threshold variables.

### 3. Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 4. Database Setup
```bash
python scripts/setup_db.py --host localhost --user accesslens
```

### 5. Running
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Running Tests
Tests are orchestrated via Pytest over a headless asynchronous client.
```bash
pytest backend/tests/ -v --capture=no
```

## Production Docker Deployment
Simply use the included compose wrapper to spin up the API and Postgres together:
```bash
docker-compose up -d --build
```
