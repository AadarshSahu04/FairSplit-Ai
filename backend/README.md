# FairSplit AI — Backend

FastAPI backend for the FairSplit AI bill-splitting application.

## Prerequisites

- Python 3.11+
- pip

## Setup

### 1. Create virtual environment

```powershell
cd backend
python -m venv venv
```

### 2. Activate virtual environment

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment

```powershell
copy .env.example .env
```

Edit `.env` and fill in your `GEMINI_API_KEY`.

### 5. Run the server

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs available at: http://127.0.0.1:8000/docs

## Run Tests

```powershell
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /api/bill/extract | Upload image, extract bill |
| POST | /api/bill/validate | Validate/confirm edited bill |
| POST | /api/bill/split | Calculate fair split |
