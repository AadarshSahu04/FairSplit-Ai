# FairSplit AI

> Photograph a restaurant bill. Verify the extraction. Assign who ate what. Get an exact, fair split.

## Project Structure

```
FairSplit Ai/
├── backend/     FastAPI + Python (OCR, validation, calculation)
├── frontend/    React + Vite (SPA)
├── docs/        Architecture and API documentation
└── README.md    This file
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Gemini API key

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env: add your GEMINI_API_KEY
uvicorn app.main:app --reload
```

API runs at: http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

App runs at: http://localhost:5173

## Development Phases

See [implementation_plan.md] for the 16-phase development roadmap.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite |
| Backend | FastAPI + Python 3.11 |
| Validation | Pydantic v2 |
| OCR | Google Gemini Vision |
| Financial math | Python `decimal.Decimal` |
| Image preprocessing | Pillow |
