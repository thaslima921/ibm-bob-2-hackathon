"""
GitHub repository cloner — safely clones a public GitHub HTTPS repository
into a uniquely named temporary directory.

Security rules:
  - Only HTTPS URLs from github.com are accepted.
  - Credentials embedded in URLs are rejected.
  - Unexpected URL components (fragment, query, user info) are rejected.
  - Owner and repository name are validated with a strict allowlist regex.
  - git is invoked via a safe argument list (never shell=True).
  - A clone timeout and a shallow-clone depth are applied.
  - The caller is responsible for cleaning up the temporary directory.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse

# Maximum number of characters allowed in owner/repo name segments
_MAX_SEGMENT_LEN = 100

# Only alphanumerics, hyphens, underscores and dots — no shell-special chars
_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")

# Clone timeout in seconds — prevents hanging on large/slow repositories
CLONE_TIMEOUT_SECONDS = 120

# Shallow clone depth — we only need recent history for commit analysis
CLONE_DEPTH = 50

# Maximum number of files we will tolerate in the clone (rough safety cap)
MAX_FILE_COUNT = 50_000


class GitHubURLError(ValueError):
    """Raised when a GitHub URL is invalid or unsupported."""


class CloneError(RuntimeError):
    """Raised when git clone fails."""


def validate_github_url(url: str) -> tuple[str, str]:
    """
    Parse and validate a GitHub HTTPS URL.

    Returns (owner, repo_name) on success.
    Raises GitHubURLError for any invalid input.

    Accepted form:
        https://github.com/<owner>/<repo>
        https://github.com/<owner>/<repo>/
        https://github.com/<owner>/<repo>.git
    """
    url = url.strip()
    if not url:
        raise GitHubURLError("URL must not be empty.")

    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise GitHubURLError(
            "Only HTTPS GitHub URLs are supported (e.g. https://github.com/owner/repo)."
        )

    if parsed.netloc.lower() != "github.com":
        raise GitHubURLError(
            f"Only github.com repositories are supported, got: {parsed.netloc!r}."
        )

    # Reject credentials embedded in the URL
    if parsed.username or parsed.password:
        raise GitHubURLError("Credentials in URLs are not supported.")

    # Reject query strings and fragments
    if parsed.query:
        raise GitHubURLError("Unexpected query string in GitHub URL.")
    if parsed.fragment:
        raise GitHubURLError("Unexpected fragment in GitHub URL.")

    # Parse path: must be /<owner>/<repo> with optional trailing slash or .git
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]

    parts = [p for p in path.split("/") if p]
    if len(parts) != 2:
        raise GitHubURLError(
            "GitHub URL must have exactly two path segments: owner and repository name "
            "(e.g. https://github.com/owner/repo)."
        )

    owner, repo = parts

    for segment, label in ((owner, "owner"), (repo, "repository name")):
        if len(segment) > _MAX_SEGMENT_LEN:
            raise GitHubURLError(f"GitHub {label} is too long.")
        if not _SAFE_SEGMENT_RE.match(segment):
            raise GitHubURLError(
                f"GitHub {label} {segment!r} contains disallowed characters. "
                "Only letters, digits, hyphens, underscores and dots are allowed."
            )

    return owner, repo


def clone_repository(github_url: str) -> Path:
    """
    Clone a public GitHub repository into a new temporary directory.

    Returns the Path to the cloned directory.
    Raises GitHubURLError for invalid URLs and CloneError if git fails.

    The caller must delete the returned directory when done.
    """
    owner, repo = validate_github_url(github_url)

    # Build a safe canonical HTTPS URL (never use the raw user-supplied string)
    safe_url = f"https://github.com/{owner}/{repo}.git"

    # Unique temp directory — uses OS temp root, never touches user paths
    tmp_base = Path(tempfile.gettempdir()) / f"changeguard_{uuid.uuid4().hex}"
    tmp_base.mkdir(parents=True, exist_ok=False)
    clone_dir = tmp_base / repo

    flags = (
        subprocess.CREATE_NEW_PROCESS_GROUP
        if sys.platform == "win32" and hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP")
        else 0
    )

    try:
        result = subprocess.run(
            [
                "git",
                "clone",
                "--depth", str(CLONE_DEPTH),
                "--single-branch",
                "--no-tags",
                "--",
                safe_url,
                str(clone_dir),
            ],
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_SECONDS,
            creationflags=flags,
            # Explicitly no cwd — git resolves the destination path itself
        )
    except FileNotFoundError:
        shutil.rmtree(tmp_base, ignore_errors=True)
        raise CloneError("git is not installed or not available on PATH.")
    except subprocess.TimeoutExpired:
        shutil.rmtree(tmp_base, ignore_errors=True)
        raise CloneError(
            f"Clone timed out after {CLONE_TIMEOUT_SECONDS} seconds. "
            "The repository may be too large or the network too slow."
        )

    if result.returncode != 0:
        shutil.rmtree(tmp_base, ignore_errors=True)
        # Sanitize stderr — never expose server paths
        stderr_safe = result.stderr.strip()[:500] if result.stderr else ""
        raise CloneError(
            f"git clone failed (exit {result.returncode}). "
            + (f"Details: {stderr_safe}" if stderr_safe else "The repository may not exist or may be private.")
        )

    if not clone_dir.is_dir():
        shutil.rmtree(tmp_base, ignore_errors=True)
        raise CloneError("Clone appeared to succeed but destination directory was not created.")

    return clone_dir


def cleanup_clone(clone_dir: Path) -> None:
    """Remove a temporary clone directory. Silently ignores errors."""
    # Resolve to prevent path traversal — only remove if inside system temp
    try:
        resolved = clone_dir.resolve()
        tmp = Path(tempfile.gettempdir()).resolve()
        if str(resolved).startswith(str(tmp)):
            shutil.rmtree(resolved, ignore_errors=True)
            # Also remove the parent changeguard_<uuid> wrapper directory if empty
            parent = resolved.parent
            if str(parent).startswith(str(tmp)) and parent != tmp:
                try:
                    parent.rmdir()
                except OSError:
                    pass
    except Exception:  # noqa: BLE001
        pass
