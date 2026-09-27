"""Analysis router — POST /analysis, GET /analysis/{id}"""
from __future__ import annotations
import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException
from backend.models.schemas import AnalysisJob, AnalysisRequest
from backend.services import store
from backend.services.orchestrator import run_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("", response_model=AnalysisJob)
async def start_analysis(req: AnalysisRequest, background_tasks: BackgroundTasks):
    job = AnalysisJob(diff_id=req.diff_id, label=req.label)
    store.save_job(job)
    background_tasks.add_task(
        run_analysis, job, req.diff_text, req.repository_id
    )
    return job


@router.get("/{job_id}", response_model=AnalysisJob)
async def get_analysis(job_id: str):
    job = store.load_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
