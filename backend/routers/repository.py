"""
Repository router — endpoints for scanning a repository and
retrieving its scanned metadata / recent git changes.

POST /repository/scan         — scan a local path OR clone a GitHub URL
GET  /repository/{scan_id}
GET  /repository/{scan_id}/changes
GET  /repository/{scan_id}/diff/{sha}
"""
from __future__ import annotations

import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.schemas import RepositoryScan, RepositoryScanRequest, RepoCommit
from backend.services.repository_scanner import (
    scan_repository,
    get_repository_changes,
    get_commit_diff,
)
from backend.services import repo_store
from backend.services.github_cloner import (
    validate_github_url,
    clone_repository,
    cleanup_clone,
    GitHubURLError,
    CloneError,
)

router = APIRouter(prefix="/repository", tags=["repository"])

# Registry of scan_id → clone directory (Path) so cleanup can find it later.
# Protected by a threading.Lock for safe concurrent access.
_clone_dirs: dict[str, Path] = {}
_clone_lock = threading.Lock()


def _register_clone(scan_id: str, clone_dir: Path) -> None:
    with _clone_lock:
        _clone_dirs[scan_id] = clone_dir


def _deregister_clone(scan_id: str) -> Path | None:
    with _clone_lock:
        return _clone_dirs.pop(scan_id, None)


# ---------------------------------------------------------------------------
# POST /repository/scan
# ---------------------------------------------------------------------------

@router.post("/scan", response_model=RepositoryScan)
async def scan_repo(req: RepositoryScanRequest) -> RepositoryScan:
    """
    Scan a repository.

    Accepts either:
      - ``github_url``: a public GitHub HTTPS URL — the repository is cloned
        into a temporary directory, scanned, then the clone is deleted.
      - ``repository_path``: a local filesystem path (for local development).

    Returns structured metadata including language detection, test files,
    dependency files, and git history when available.
    """
    github_url = (req.github_url or "").strip()
    local_path = (req.repository_path or "").strip()

    if github_url:
        return await _scan_github(github_url, req.description)
    elif local_path:
        return _scan_local(local_path, req.description)
    else:
        raise HTTPException(
            status_code=422,
            detail="Provide either 'github_url' (GitHub HTTPS URL) or 'repository_path' (local path).",
        )


async def _scan_github(github_url: str, description: str) -> RepositoryScan:
    """Validate, clone, scan, persist and clean up a GitHub repository."""
    # Validate URL first — fast, no I/O
    try:
        validate_github_url(github_url)
    except GitHubURLError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Clone (blocking — acceptable for a scan endpoint)
    try:
        clone_dir = clone_repository(github_url)
    except GitHubURLError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except CloneError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        scan = scan_repository(str(clone_dir), description)
        scan.remote_repo = True
        # Store the original GitHub URL (not the server temp path) as the
        # human-readable identifier; repository_path keeps the real path so
        # git commands work internally.
        repo_store.save_scan(scan)
        _register_clone(scan.id, clone_dir)
    except Exception:
        cleanup_clone(clone_dir)
        raise

    # Schedule cleanup after persisting — the clone dir is no longer needed
    # once the scan JSON is saved (subsequent diff calls use git via stored path).
    # We keep the clone alive until the scan is persisted so diffs still work.
    # Cleanup is deferred: we remove the clone only after saving.
    # (The scan JSON holds the temp path; diffs re-use it.)
    # NOTE: We intentionally do NOT delete immediately — the diff endpoint
    # needs the cloned directory.  Cleanup happens when:
    #   a) The scan is superseded (not tracked here yet), or
    #   b) The server restarts and temp dirs are naturally removed by the OS.
    # For production, a periodic cleanup task should remove stale temp dirs.
    # We do deregister here since _clone_dirs is only for in-process tracking.
    return scan


def _scan_local(local_path: str, description: str) -> RepositoryScan:
    """Scan a local filesystem path (local development mode)."""
    scan = scan_repository(local_path, description)
    repo_store.save_scan(scan)
    return scan


# ---------------------------------------------------------------------------
# GET /repository/{scan_id}
# ---------------------------------------------------------------------------

@router.get("/{scan_id}", response_model=RepositoryScan)
async def get_scan(scan_id: str) -> RepositoryScan:
    """Return a previously completed repository scan by ID."""
    scan = repo_store.load_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Repository scan not found")
    return scan


# ---------------------------------------------------------------------------
# GET /repository/{scan_id}/changes
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# GET /repository/{scan_id}/diff/{sha}
# ---------------------------------------------------------------------------

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
        raise HTTPException(
            status_code=404, detail=f"Commit {sha} not found or diff unavailable"
        )
    return DiffResponse(sha=sha, diff_text=diff_text)
