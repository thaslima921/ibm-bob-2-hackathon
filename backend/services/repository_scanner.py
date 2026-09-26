"""
Repository scanner — static inspection of a local project directory.

Safety rules:
  - Never executes repository code.
  - Never reads .env secret values.
  - Skips known large/generated directories.
  - Caps file lists to avoid processing enormous repos.
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

from backend.models.schemas import RepoCommit, RepositoryScan

# Directories to skip entirely during any walk
_SKIP_DIRS: set[str] = {
    ".git", "node_modules", "venv", ".venv", "__pycache__",
    "dist", "build", "coverage", ".tox", ".eggs", ".mypy_cache",
    ".pytest_cache", "target",  # Java/Maven
}

# Maximum source files to include in the returned list (keeps payload small)
_MAX_SOURCE_FILES = 200
_MAX_TEST_FILES = 100
_MAX_RECENT_COMMITS = 10

# File-extension → language
_LANG_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".go": "Go",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".php": "PHP",
}

# Well-known dependency / config files
_DEPENDENCY_FILES: set[str] = {
    "requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py",
    "setup.cfg", "Pipfile", "Pipfile.lock",
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "pom.xml", "build.gradle", "build.gradle.kts", "gradle.properties",
    "Gemfile", "Gemfile.lock", "go.mod", "go.sum",
    "Cargo.toml", "Cargo.lock",
}

# Framework indicator files/patterns → framework name
_FRAMEWORK_INDICATORS: list[tuple[str, str]] = [
    ("manage.py", "Django"),
    ("wsgi.py", "Django/WSGI"),
    ("asgi.py", "Django/ASGI"),
    ("fastapi", "FastAPI"),   # checked inside pyproject/requirements
    ("flask", "Flask"),
    ("express", "Express.js"),
    ("next.config.js", "Next.js"),
    ("next.config.ts", "Next.js"),
    ("nuxt.config.js", "Nuxt.js"),
    ("vite.config.js", "Vite"),
    ("vite.config.ts", "Vite"),
    ("angular.json", "Angular"),
    ("vue.config.js", "Vue.js"),
    ("spring", "Spring"),     # checked inside pom/build.gradle
    ("pom.xml", "Maven"),
    ("build.gradle", "Gradle"),
]

# Config file names (not secret-bearing)
_CONFIG_FILE_NAMES: set[str] = {
    ".env.example", ".env.sample",
    "docker-compose.yml", "docker-compose.yaml",
    "Dockerfile",
    ".github",  # directory marker
    "jest.config.js", "jest.config.ts",
    "pytest.ini", "conftest.py", "tox.ini",
    "tsconfig.json", "jsconfig.json",
    ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml",
    ".prettierrc", ".prettierrc.json",
    ".babelrc", "babel.config.js",
    "README.md", "README.rst", "CHANGELOG.md",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_repository(path_str: str, description: str = "") -> RepositoryScan:
    """
    Scan *path_str* and return a populated RepositoryScan.
    Never raises — errors are stored in scan.error instead.
    """
    scan = RepositoryScan(repository_path=path_str, description=description)

    root = Path(path_str)
    if not root.exists():
        scan.error = f"Path does not exist: {path_str}"
        return scan
    if not root.is_dir():
        scan.error = f"Path is not a directory: {path_str}"
        return scan
    if not os.access(root, os.R_OK):
        scan.error = f"Permission denied reading: {path_str}"
        return scan

    scan.project_name = root.name

    # Walk once, collecting everything
    lang_counts: dict[str, int] = {}
    source_files: list[str] = []
    test_files: list[str] = []
    config_files: list[str] = []
    dep_files: list[str] = []
    root_entries: list[str] = []
    framework_hits: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skipped directories in-place so os.walk doesn't descend
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]

        rel_dir = Path(dirpath).relative_to(root)
        depth = len(rel_dir.parts)

        # Collect top-level directory names for important_dirs
        if depth == 0:
            root_entries = list(dirnames)

        for fname in filenames:
            fpath = Path(dirpath) / fname
            rel_str = str(Path(dirpath).relative_to(root) / fname)

            suffix = fpath.suffix.lower()
            name_lower = fname.lower()

            # Language detection
            lang = _LANG_MAP.get(suffix)
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1

            # Framework hints from filename
            for indicator, fw_name in _FRAMEWORK_INDICATORS:
                if indicator == name_lower:
                    framework_hits.add(fw_name)

            # Dependency files
            if fname in _DEPENDENCY_FILES:
                dep_files.append(rel_str)
                # Check content for framework hints (safe: only text scanning, no exec)
                _sniff_dep_file(fpath, framework_hits)

            # Config files (safe, non-secret)
            if fname in _CONFIG_FILE_NAMES:
                config_files.append(rel_str)

            # Test files — heuristic: starts with test_ or ends with _test, or in tests/ dir
            is_test = (
                name_lower.startswith("test_")
                or name_lower.endswith("_test.py")
                or name_lower.endswith(".spec.js")
                or name_lower.endswith(".spec.ts")
                or name_lower.endswith(".test.js")
                or name_lower.endswith(".test.ts")
                or "tests" in rel_str.lower().split(os.sep)
                or "test" in rel_str.lower().split(os.sep)
            )
            if is_test and lang and len(test_files) < _MAX_TEST_FILES:
                test_files.append(rel_str)
            elif lang and not is_test and len(source_files) < _MAX_SOURCE_FILES:
                source_files.append(rel_str)

    # Populate scan fields
    scan.detected_languages = sorted(
        lang_counts, key=lambda l: lang_counts[l], reverse=True
    )
    scan.framework_indicators = sorted(framework_hits)
    scan.source_file_count = sum(
        v for k, v in lang_counts.items()
        if k not in ("", )
    )
    scan.test_file_count = len(test_files)
    scan.config_file_count = len(config_files)
    scan.source_files = source_files
    scan.test_files = test_files
    scan.config_files = config_files
    scan.dependency_files = dep_files
    scan.important_dirs = [d for d in root_entries if d not in _SKIP_DIRS]

    # Git information
    _populate_git_info(root, scan)

    return scan


def get_repository_changes(scan: RepositoryScan) -> list[RepoCommit]:
    """
    Return a fresh list of recent commits for an already-scanned repository.
    Returns empty list if not a Git repo or git is unavailable.
    """
    if not scan.is_git_repo:
        return []
    return _get_git_commits(Path(scan.repository_path))


def get_commit_diff(repository_path: str, sha: str) -> str | None:
    """
    Return the unified diff for a single commit as a string.
    Returns None if git is unavailable or the sha is invalid.
    """
    root = Path(repository_path)
    diff_out, rc = _run_git(["show", "--format=", sha], root)
    if rc != 0 or not diff_out.strip():
        return None
    return diff_out


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sniff_dep_file(fpath: Path, framework_hits: set[str]) -> None:
    """Read a dependency file as plain text and look for framework keywords."""
    try:
        text = fpath.read_text(encoding="utf-8", errors="ignore").lower()
        keyword_map = {
            "fastapi": "FastAPI",
            "flask": "Flask",
            "django": "Django",
            "express": "Express.js",
            "react": "React",
            "vue": "Vue.js",
            "angular": "Angular",
            "spring-boot": "Spring Boot",
            "spring-core": "Spring",
            "nextjs": "Next.js",
            "next\": ": "Next.js",
            "pytest": "pytest",
            "jest": "Jest",
        }
        for kw, fw in keyword_map.items():
            if kw in text:
                framework_hits.add(fw)
    except OSError:
        pass


def _run_git(args: list[str], cwd: Path) -> tuple[str, int]:
    """Run a git command and return (stdout, returncode). Never raises."""
    flags = (
        subprocess.CREATE_NEW_PROCESS_GROUP
        if sys.platform == "win32" and hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP")
        else 0
    )
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=10,
            creationflags=flags,
        )
        return result.stdout.strip(), result.returncode
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return "", 1


def _populate_git_info(root: Path, scan: RepositoryScan) -> None:
    """Populate git fields on the scan object in-place."""
    # Check if this is a git repo
    _, rc = _run_git(["rev-parse", "--is-inside-work-tree"], root)
    if rc != 0:
        return

    scan.is_git_repo = True

    # Current branch
    branch, _ = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    scan.current_branch = branch or "HEAD"

    # Latest commit message
    latest, _ = _run_git(["log", "-1", "--pretty=%s"], root)
    scan.latest_commit = latest

    # Recent commits
    scan.recent_commits = _get_git_commits(root)


def _get_git_commits(root: Path) -> list[RepoCommit]:
    """Return up to _MAX_RECENT_COMMITS parsed RepoCommit objects."""
    # Format: sha|message|author|date
    sep = "|||"
    fmt = f"%H{sep}%s{sep}%an{sep}%ai"
    log_out, rc = _run_git(
        ["log", f"--pretty=format:{fmt}", f"-{_MAX_RECENT_COMMITS}"],
        root,
    )
    if rc != 0 or not log_out:
        return []

    commits: list[RepoCommit] = []
    for line in log_out.splitlines():
        parts = line.split(sep, 3)
        if len(parts) < 4:
            continue
        sha, msg, author, date = parts
        sha = sha.strip()
        # Get stat for this commit
        stat_out, _ = _run_git(
            ["show", "--stat", "--format=", sha],
            root,
        )
        files_changed, insertions, deletions = _parse_stat(stat_out)
        commits.append(RepoCommit(
            sha=sha,
            short_sha=sha[:7],
            message=msg.strip(),
            author=author.strip(),
            date=date.strip(),
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
        ))
    return commits


def _parse_stat(stat_output: str) -> tuple[int, int, int]:
    """Parse 'git show --stat' summary line → (files, insertions, deletions)."""
    import re
    if not stat_output:
        return 0, 0, 0
    # Last non-empty line has the summary
    for line in reversed(stat_output.splitlines()):
        line = line.strip()
        if not line:
            continue
        files = 0
        ins = 0
        dels = 0
        m = re.search(r"(\d+) file", line)
        if m:
            files = int(m.group(1))
        m = re.search(r"(\d+) insertion", line)
        if m:
            ins = int(m.group(1))
        m = re.search(r"(\d+) deletion", line)
        if m:
            dels = int(m.group(1))
        if files or ins or dels:
            return files, ins, dels
    return 0, 0, 0
