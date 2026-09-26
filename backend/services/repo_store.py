"""
Repository scan store — persists RepositoryScan objects to JSON files
alongside jobs and reports, reusing the same STORE_DIR.
"""
from __future__ import annotations
import json
from pathlib import Path
from backend.models.schemas import RepositoryScan
from backend.services.store import STORE_DIR


def _scan_path(scan_id: str) -> Path:
    return STORE_DIR / f"repo_{scan_id}.json"


def save_scan(scan: RepositoryScan) -> None:
    with open(_scan_path(scan.id), "w") as f:
        json.dump(scan.model_dump(), f, indent=2)


def load_scan(scan_id: str) -> RepositoryScan | None:
    p = _scan_path(scan_id)
    if not p.exists():
        return None
    with open(p) as f:
        return RepositoryScan(**json.load(f))
