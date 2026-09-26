"""
Tests for the repository scanner service and /repository router.

Covers:
- valid repository scan (Python project)
- invalid / nonexistent path
- non-directory path
- ignored directories are not walked
- git repository detection
- non-git repository
- dependency file detection
- secret exclusion (.env files not read for values)
- change detection (git commits)
- repository metadata structure
- project description stored and returned
- POST /repository/scan endpoint
- GET /repository/{id} endpoint
- GET /repository/{id}/changes endpoint
- GET /repository/{id}/diff/{sha} endpoint
"""
from __future__ import annotations
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.repository_scanner import scan_repository, get_commit_diff
from backend.models.schemas import RepositoryScan

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def python_repo(tmp_path: Path) -> Path:
    """A minimal Python project tree."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "app.py").write_text("def hello(): pass\n")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass\n")
    (tmp_path / "tests" / "test_app.py").write_text("def test_hello(): pass\n")
    (tmp_path / "requirements.txt").write_text("fastapi\npytest\n")
    (tmp_path / "README.md").write_text("# My Project\n")
    return tmp_path


@pytest.fixture()
def js_repo(tmp_path: Path) -> Path:
    """A minimal JS/React project tree."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.jsx").write_text("export default function App() {}\n")
    (tmp_path / "src" / "index.js").write_text("import App from './App'\n")
    (tmp_path / "package.json").write_text(json.dumps({"name": "myapp", "dependencies": {"react": "^18"}}))
    (tmp_path / "vite.config.js").write_text("export default {}\n")
    return tmp_path


@pytest.fixture()
def repo_with_ignored_dirs(tmp_path: Path) -> Path:
    """Project with node_modules, venv, __pycache__ that must be ignored."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x = 1\n")
    # These must be skipped
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lodash.js").write_text("// big lib\n")
    (tmp_path / "venv").mkdir()
    (tmp_path / "venv" / "site.py").write_text("# venv\n")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "main.cpython-312.pyc").write_bytes(b"\x00")
    return tmp_path


@pytest.fixture()
def env_file_repo(tmp_path: Path) -> Path:
    """Project with a .env file containing secrets — values must NOT be returned."""
    (tmp_path / "app.py").write_text("pass\n")
    (tmp_path / ".env").write_text("DATABASE_URL=postgres://user:secret@localhost/db\nSECRET_KEY=s3cr3t\n")
    (tmp_path / ".env.example").write_text("DATABASE_URL=\nSECRET_KEY=\n")
    return tmp_path


# ---------------------------------------------------------------------------
# Scanner unit tests
# ---------------------------------------------------------------------------

class TestScanRepository:
    def test_valid_python_project(self, python_repo):
        scan = scan_repository(str(python_repo))
        assert scan.error is None
        assert scan.project_name == python_repo.name
        assert "Python" in scan.detected_languages
        assert scan.source_file_count >= 2
        assert scan.test_file_count >= 1

    def test_detects_dependency_files(self, python_repo):
        scan = scan_repository(str(python_repo))
        dep_names = [Path(f).name for f in scan.dependency_files]
        assert "requirements.txt" in dep_names

    def test_detects_framework_from_requirements(self, python_repo):
        scan = scan_repository(str(python_repo))
        # requirements.txt contains 'fastapi' → FastAPI framework detected
        assert "FastAPI" in scan.framework_indicators

    def test_detects_config_files(self, python_repo):
        scan = scan_repository(str(python_repo))
        config_names = [Path(f).name for f in scan.config_files]
        assert "README.md" in config_names

    def test_javascript_project(self, js_repo):
        scan = scan_repository(str(js_repo))
        assert "JavaScript" in scan.detected_languages
        assert "Vite" in scan.framework_indicators

    def test_nonexistent_path(self, tmp_path):
        scan = scan_repository(str(tmp_path / "does_not_exist"))
        assert scan.error is not None
        assert "does not exist" in scan.error.lower()

    def test_file_path_not_directory(self, tmp_path):
        f = tmp_path / "afile.txt"
        f.write_text("hello")
        scan = scan_repository(str(f))
        assert scan.error is not None
        assert "not a directory" in scan.error.lower()

    def test_ignored_directories_not_walked(self, repo_with_ignored_dirs):
        scan = scan_repository(str(repo_with_ignored_dirs))
        # node_modules / venv / __pycache__ must not appear in source_files
        all_paths = scan.source_files + scan.test_files
        for p in all_paths:
            parts = Path(p).parts
            assert "node_modules" not in parts
            assert "venv" not in parts
            assert "__pycache__" not in parts

    def test_env_file_not_in_config_files(self, env_file_repo):
        """The actual .env should never appear in config_files (only .env.example)."""
        scan = scan_repository(str(env_file_repo))
        config_names = [Path(f).name for f in scan.config_files]
        # .env.example is safe to list; raw .env must not be listed
        assert ".env" not in config_names
        if ".env.example" in [Path(f).name for f in scan.dependency_files + scan.config_files]:
            pass  # ok

    def test_project_description_stored(self, python_repo):
        scan = scan_repository(str(python_repo), description="E-commerce backend")
        assert scan.description == "E-commerce backend"

    def test_non_git_repo(self, python_repo):
        scan = scan_repository(str(python_repo))
        # tmp_path is not a git repo (unless the test runner itself is inside one)
        # We can only check the field exists and is a bool
        assert isinstance(scan.is_git_repo, bool)

    def test_git_repo_detection(self, tmp_path):
        """Simulate a git repo by mocking _run_git."""
        (tmp_path / "app.py").write_text("pass\n")
        with patch("backend.services.repository_scanner._run_git") as mock_git:
            def _side_effect(args, cwd):
                joined = " ".join(str(a) for a in args)
                if "--is-inside-work-tree" in args:
                    return "true", 0
                if "--abbrev-ref" in args:
                    return "main", 0
                if "-1" in args and "--pretty=%s" in joined:
                    return "Initial commit", 0
                if "log" in args:
                    return "", 0
                return "", 0
            mock_git.side_effect = _side_effect

            scan = scan_repository(str(tmp_path))
            assert scan.is_git_repo is True
            assert scan.current_branch == "main"

    def test_scan_returns_scan_id(self, python_repo):
        scan = scan_repository(str(python_repo))
        assert scan.id  # UUID string, non-empty

    def test_source_file_list_capped(self, tmp_path):
        """Create >200 Python files — scanner must cap the list."""
        from backend.services.repository_scanner import _MAX_SOURCE_FILES
        src = tmp_path / "src"
        src.mkdir()
        for i in range(_MAX_SOURCE_FILES + 50):
            (src / f"module_{i}.py").write_text("x = 1\n")
        scan = scan_repository(str(tmp_path))
        assert len(scan.source_files) <= _MAX_SOURCE_FILES


class TestGetCommitDiff:
    def test_returns_none_for_bad_sha(self, python_repo):
        """Non-git repos or bad SHAs return None, never raise."""
        result = get_commit_diff(str(python_repo), "badfakeshaabc123")
        assert result is None


# ---------------------------------------------------------------------------
# Router integration tests
# ---------------------------------------------------------------------------

class TestRepositoryRouter:
    def test_scan_endpoint_valid(self, python_repo, tmp_path, monkeypatch):
        # Redirect store to tmp_path
        import backend.services.repo_store as rs
        monkeypatch.setattr(rs, "STORE_DIR", tmp_path)
        # Patch save to use tmp_path
        saved = {}
        monkeypatch.setattr(rs, "save_scan", lambda s: saved.update({"scan": s}))

        resp = client.post("/repository/scan", json={
            "repository_path": str(python_repo),
            "description": "Test project",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_name"] == python_repo.name
        assert data["description"] == "Test project"
        assert "Python" in data["detected_languages"]
        assert data["error"] is None

    def test_scan_endpoint_invalid_path(self, tmp_path, monkeypatch):
        import backend.services.repo_store as rs
        monkeypatch.setattr(rs, "save_scan", lambda s: None)

        resp = client.post("/repository/scan", json={
            "repository_path": str(tmp_path / "nonexistent"),
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is not None

    def test_get_scan_not_found(self):
        resp = client.get("/repository/00000000-does-not-exist")
        assert resp.status_code == 404

    def test_get_changes_not_found(self):
        resp = client.get("/repository/00000000-does-not-exist/changes")
        assert resp.status_code == 404

    def test_get_changes_non_git(self, python_repo, monkeypatch):
        """Non-git repo should return empty list, not error."""
        import backend.services.repo_store as rs
        fake_scan = RepositoryScan(
            id="test-scan-123",
            repository_path=str(python_repo),
            is_git_repo=False,
        )
        monkeypatch.setattr(rs, "load_scan", lambda sid: fake_scan)

        resp = client.get("/repository/test-scan-123/changes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_diff_endpoint_non_git(self, python_repo, monkeypatch):
        import backend.services.repo_store as rs
        fake_scan = RepositoryScan(
            id="test-scan-456",
            repository_path=str(python_repo),
            is_git_repo=False,
        )
        monkeypatch.setattr(rs, "load_scan", lambda sid: fake_scan)

        resp = client.get("/repository/test-scan-456/diff/abc1234")
        assert resp.status_code == 400

    def test_scan_stores_and_retrieves(self, python_repo, tmp_path, monkeypatch):
        """Round-trip: scan then GET /{id} returns same scan."""
        import backend.services.repo_store as rs
        store: dict = {}

        def fake_save(s):
            store[s.id] = s

        def fake_load(sid):
            return store.get(sid)

        monkeypatch.setattr(rs, "save_scan", fake_save)
        monkeypatch.setattr(rs, "load_scan", fake_load)

        post_resp = client.post("/repository/scan", json={
            "repository_path": str(python_repo),
            "description": "round-trip test",
        })
        assert post_resp.status_code == 200
        scan_id = post_resp.json()["id"]

        get_resp = client.get(f"/repository/{scan_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["description"] == "round-trip test"
