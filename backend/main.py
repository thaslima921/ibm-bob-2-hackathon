"""ChangeGuard FastAPI backend entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.analysis import router as analysis_router
from backend.routers.reports import router as reports_router
from backend.routers.repository import router as repository_router

app = FastAPI(
    title="ChangeGuard API",
    description="Code change risk analysis and test-readiness service.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repository_router)
app.include_router(analysis_router)
app.include_router(reports_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ChangeGuard"}
