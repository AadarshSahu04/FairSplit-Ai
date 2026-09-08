"""
FairSplit AI — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_bill import router as bill_router
from app.api.routes_split import router as split_router

app = FastAPI(
    title="FairSplit AI",
    description="Photograph-based intelligent restaurant bill splitting.",
    version="0.1.0",
)

# Allow requests from Vite dev server and production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bill_router, prefix="/api/bill", tags=["bill"])
app.include_router(split_router, prefix="/api/bill", tags=["split"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "FairSplit AI"}
