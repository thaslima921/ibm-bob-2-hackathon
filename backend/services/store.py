"""
Simple JSON file-based job store.
Jobs are stored as individual JSON files in backend/data/results/.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from backend.models.schemas import AnalysisJob, ReleaseReport

STORE_DIR = Path(__file__).resolve().parent.parent / "data" / "results"
STORE_DIR.mkdir(parents=True, exist_ok=True)


def _job_path(job_id: str) -> Path:
    return STORE_DIR / f"job_{job_id}.json"


def _report_path(report_id: str) -> Path:
    return STORE_DIR / f"report_{report_id}.json"


def save_job(job: AnalysisJob) -> None:
    with open(_job_path(job.id), "w") as f:
        json.dump(job.model_dump(), f, indent=2)


def load_job(job_id: str) -> AnalysisJob | None:
    p = _job_path(job_id)
    if not p.exists():
        return None
    with open(p) as f:
        return AnalysisJob(**json.load(f))


def save_report(report: ReleaseReport) -> None:
    with open(_report_path(report.id), "w") as f:
        json.dump(report.model_dump(), f, indent=2)


def load_report(report_id: str) -> ReleaseReport | None:
    p = _report_path(report_id)
    if not p.exists():
        return None
    with open(p) as f:
        return ReleaseReport(**json.load(f))


def list_reports() -> list[dict]:
    reports = []
    for p in sorted(STORE_DIR.glob("report_*.json"), key=os.path.getmtime, reverse=True):
        with open(p) as f:
            data = json.load(f)
        reports.append({
            "id": data["id"],
            "job_id": data["job_id"],
            "diff_id": data["diff_id"],
            "label": data.get("label", ""),
            "created_at": data["created_at"],
            "release_verdict": data["release_verdict"],
        })
    return reports
