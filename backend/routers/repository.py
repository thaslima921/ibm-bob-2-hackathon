"""
Repository router — endpoints for scanning a local repository and
retrieving its scanned metadata / recent git changes.

POST /repository/scan
GET  /repository/{scan_id}
GET  /repository/{scan_id}/changes
GET  /repository/{scan_id}/diff/{sha}
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.schemas import RepositoryScan, RepositoryScanRequest, RepoCommit
from backend.services.repository_scanner import (
    scan_repository,
    get_repository_changes,
    get_commit_diff,
)
from backend.services import repo_store

router = APIRouter(prefix="/repository", tags=["repository"])


@router.post("/scan", response_model=RepositoryScan)
async def scan_repo(req: RepositoryScanRequest) -> RepositoryScan:
    """
    Scan a local repository directory.

    The backend reads the filesystem path directly — no file upload needed.
    Returns structured metadata including language detection, test files,
    dependency files, and git history when available.
    """
    scan = scan_repository(req.repository_path, req.description)
    repo_store.save_scan(scan)
    return scan


@router.get("/{scan_id}", response_model=RepositoryScan)
async def get_scan(scan_id: str) -> RepositoryScan:
    """Return a previously completed repository scan by ID."""
    scan = repo_store.load_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Repository scan not found")
    return scan


@router.get("/{scan_id}/changes", response_model=list[RepoCommit])
async def get_changes(scan_id: str) -> list[RepoCommit]:
    """
    Return recent git commits for a scanned repository.

    Returns an empty list if the repository is not a git repo or git is
    unavailable.  Never raises 500 — returns 404 only when the scan_id is
    unknown.
    """
    scan = repo_store.load_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Repository scan not found")
    return get_repository_changes(scan)


class DiffResponse(BaseModel):
    sha: str
    diff_text: str


@router.get("/{scan_id}/diff/{sha}", response_model=DiffResponse)
async def get_commit_diff_endpoint(scan_id: str, sha: str) -> DiffResponse:
    """
    Return the unified diff for a single git commit.

    Used by the frontend to retrieve the diff text when the user selects a
    commit to analyze.
    """
    scan = repo_store.load_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Repository scan not found")
    if not scan.is_git_repo:
        raise HTTPException(status_code=400, detail="Repository is not a git repository")
    diff_text = get_commit_diff(scan.repository_path, sha)
    if diff_text is None:
        raise HTTPException(status_code=404, detail=f"Commit {sha} not found or diff unavailable")
    return DiffResponse(sha=sha, diff_text=diff_text)
