"""Reports router — GET /reports, GET /reports/{id}"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from backend.models.schemas import ReleaseReport
from backend.services import store

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
async def list_reports():
    return store.list_reports()


@router.get("/{report_id}", response_model=ReleaseReport)
async def get_report(report_id: str):
    report = store.load_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
