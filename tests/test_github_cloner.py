"""
Tests for GitHub URL validation, cloning and the updated /repository/scan
endpoint — all Git network I/O is mocked so tests run offline.

Coverage:
  - validate_github_url: valid URLs, invalid scheme, wrong host, credentials,
    query strings, fragments, short paths, long paths, unsafe characters
  - clone_repository: successful clone (mocked), git not found, timeout,
    non-zero exit code
  - POST /repository/scan with github_url: success, invalid URL, clone failure
  - POST /repository/scan with repository_path: backward-compat preserved
  - POST /repository/scan with neither field: 422
  - remote_repo flag is set for GitHub-cloned scans
  - orchestrator skips test execution for remote repos
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.github_cloner import (
    GitHubURLError,
    CloneError,
    validate_github_url,
    clone_repository,
)
from backend.models.schemas import RepositoryScan, TestRunResult

client = TestClient(app)


# ---------------------------------------------------------------------------
# validate_github_url
# ---------------------------------------------------------------------------

class TestValidateGitHubUrl:
    def test_simple_valid_url(self):
        owner, repo = validate_github_url("https://github.com/octocat/Hello-World")
        assert owner == "octocat"
        assert repo == "Hello-World"

    def test_trailing_slash_accepted(self):
        owner, repo = validate_github_url("https://github.com/octocat/Hello-World/")
        assert owner == "octocat"
        assert repo == "Hello-World"

    def test_dot_git_suffix_accepted(self):
        owner, repo = validate_github_url("https://github.com/octocat/Hello-World.git")
        assert owner == "octocat"
        assert repo == "Hello-World"

    def test_underscores_and_dots(self):
        owner, repo = validate_github_url("https://github.com/my_org/my.repo-name")
        assert owner == "my_org"
        assert repo == "my.repo-name"

    def test_empty_string(self):
        with pytest.raises(GitHubURLError, match="empty"):
            validate_github_url("")

    def test_http_rejected(self):
        with pytest.raises(GitHubURLError, match="HTTPS"):
            validate_github_url("http://github.com/owner/repo")

    def test_non_github_host(self):
        with pytest.raises(GitHubURLError, match="github.com"):
            validate_github_url("https://gitlab.com/owner/repo")

    def test_credentials_rejected(self):
        # urlparse puts credentials in netloc so the host check fires first;
        # either way the URL must be rejected.
        with pytest.raises(GitHubURLError):
            validate_github_url("https://user:pass@github.com/owner/repo")

    def test_query_string_rejected(self):
        with pytest.raises(GitHubURLError, match="query"):
            validate_github_url("https://github.com/owner/repo?foo=bar")

    def test_fragment_rejected(self):
        with pytest.raises(GitHubURLError, match="fragment"):
            validate_github_url("https://github.com/owner/repo#readme")

    def test_only_owner_path(self):
        with pytest.raises(GitHubURLError, match="two path segments"):
            validate_github_url("https://github.com/owner")

    def test_three_segment_path(self):
        with pytest.raises(GitHubURLError, match="two path segments"):
            validate_github_url("https://github.com/owner/repo/tree/main")

    def test_unsafe_characters_in_owner(self):
        # The semicolon + space causes urlparse to produce a path with more or
        # fewer segments than expected, so any GitHubURLError is correct.
        with pytest.raises(GitHubURLError):
            validate_github_url("https://github.com/owner;rm -rf /;/repo")

    def test_unsafe_characters_in_repo(self):
        with pytest.raises(GitHubURLError, match="disallowed characters"):
            validate_github_url("https://github.com/owner/repo&&evil")

    def test_segment_too_long(self, monkeypatch):
        long_name = "a" * 200
        with pytest.raises(GitHubURLError, match="too long"):
            validate_github_url(f"https://github.com/owner/{long_name}")

    def test_whitespace_stripped(self):
        owner, repo = validate_github_url("  https://github.com/octocat/Hello-World  ")
        assert owner == "octocat"


# ---------------------------------------------------------------------------
# clone_repository (mocked subprocess)
# ---------------------------------------------------------------------------

class TestCloneRepository:
    def _make_completed_process(self, returncode=0, stderr=""):
        proc = MagicMock()
        proc.returncode = returncode
        proc.stdout = ""
        proc.stderr = stderr
        return proc

    def test_successful_clone(self, tmp_path):
        """Mock a successful git clone — verifies argument list and return path."""
        with patch("backend.services.github_cloner.subprocess.run") as mock_run, \
             patch("backend.services.github_cloner.tempfile.gettempdir", return_value=str(tmp_path)):

            # Simulate git creating the destination directory
            def fake_run(args, **kwargs):
                dest = Path(args[-1])
                dest.mkdir(parents=True, exist_ok=True)
                return self._make_completed_process(0)

            mock_run.side_effect = fake_run
            result = clone_repository("https://github.com/octocat/Hello-World")

        assert result.is_dir()
        assert result.name == "Hello-World"
        # Verify safe canonical URL was used (not raw user input)
        call_args = mock_run.call_args[0][0]
        assert "https://github.com/octocat/Hello-World.git" in call_args
        assert "shell" not in mock_run.call_args[1] or not mock_run.call_args[1].get("shell")

    def test_git_not_found(self, tmp_path):
        with patch("backend.services.github_cloner.subprocess.run") as mock_run, \
             patch("backend.services.github_cloner.tempfile.gettempdir", return_value=str(tmp_path)):
            mock_run.side_effect = FileNotFoundError
            with pytest.raises(CloneError, match="git is not installed"):
                clone_repository("https://github.com/octocat/Hello-World")

    def test_clone_timeout(self, tmp_path):
        with patch("backend.services.github_cloner.subprocess.run") as mock_run, \
             patch("backend.services.github_cloner.tempfile.gettempdir", return_value=str(tmp_path)):
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=120)
            with pytest.raises(CloneError, match="timed out"):
                clone_repository("https://github.com/octocat/Hello-World")

    def test_clone_nonzero_exit(self, tmp_path):
        with patch("backend.services.github_cloner.subprocess.run") as mock_run, \
             patch("backend.services.github_cloner.tempfile.gettempdir", return_value=str(tmp_path)):
            mock_run.return_value = self._make_completed_process(
                128, "Repository not found."
            )
            with pytest.raises(CloneError, match="clone failed"):
                clone_repository("https://github.com/octocat/Hello-World")

    def test_invalid_url_propagates(self):
        with pytest.raises(GitHubURLError):
            clone_repository("https://evil.com/owner/repo")

    def test_no_shell_true(self, tmp_path):
        """subprocess.run must never be called with shell=True."""
        with patch("backend.services.github_cloner.subprocess.run") as mock_run, \
             patch("backend.services.github_cloner.tempfile.gettempdir", return_value=str(tmp_path)):

            def fake_run(args, **kwargs):
                assert kwargs.get("shell") is not True, "shell=True is forbidden"
                dest = Path(args[-1])
                dest.mkdir(parents=True, exist_ok=True)
                return self._make_completed_process(0)

            mock_run.side_effect = fake_run
            clone_repository("https://github.com/octocat/Hello-World")


# ---------------------------------------------------------------------------
# POST /repository/scan endpoint — GitHub URL path
# ---------------------------------------------------------------------------

class TestScanEndpointGitHub:
    """Integration tests for the scan endpoint with github_url."""

    def _mock_clone_and_scan(self, tmp_path, monkeypatch):
        """
        Helper: mock clone_repository to create a real tmp dir, and
        mock save_scan/load_scan so we don't hit the filesystem store.
        """
        import backend.services.repo_store as rs
        store: dict = {}
        monkeypatch.setattr(rs, "save_scan", lambda s: store.update({s.id: s}))
        monkeypatch.setattr(rs, "load_scan", lambda sid: store.get(sid))

        cloned_dir = tmp_path / "Hello-World"
        cloned_dir.mkdir()
        (cloned_dir / "main.py").write_text("print('hello')\n")

        return cloned_dir, store

    def test_github_url_success(self, tmp_path, monkeypatch):
        cloned_dir, store = self._mock_clone_and_scan(tmp_path, monkeypatch)

        with patch("backend.routers.repository.clone_repository", return_value=cloned_dir), \
             patch("backend.routers.repository.cleanup_clone"):
            resp = client.post("/repository/scan", json={
                "github_url": "https://github.com/octocat/Hello-World",
                "description": "test",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is None
        assert data["remote_repo"] is True
        assert data["description"] == "test"
        assert "Python" in data["detected_languages"]

    def test_github_url_invalid(self, monkeypatch):
        import backend.services.repo_store as rs
        monkeypatch.setattr(rs, "save_scan", lambda s: None)

        resp = client.post("/repository/scan", json={
            "github_url": "https://evil.com/owner/repo",
        })
        assert resp.status_code == 422

    def test_github_url_clone_failure(self, monkeypatch):
        import backend.services.repo_store as rs
        monkeypatch.setattr(rs, "save_scan", lambda s: None)

        with patch("backend.routers.repository.clone_repository",
                   side_effect=CloneError("Repository not found.")):
            resp = client.post("/repository/scan", json={
                "github_url": "https://github.com/octocat/nonexistent-repo-xyz",
            })

        assert resp.status_code == 502
        assert "Repository not found" in resp.json()["detail"]

    def test_github_url_unsupported_host(self, monkeypatch):
        import backend.services.repo_store as rs
        monkeypatch.setattr(rs, "save_scan", lambda s: None)

        resp = client.post("/repository/scan", json={
            "github_url": "https://bitbucket.org/owner/repo",
        })
        assert resp.status_code == 422

    def test_github_url_malformed(self, monkeypatch):
        import backend.services.repo_store as rs
        monkeypatch.setattr(rs, "save_scan", lambda s: None)

        resp = client.post("/repository/scan", json={
            "github_url": "not-a-url",
        })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /repository/scan — local path still works (backward compat)
# ---------------------------------------------------------------------------

class TestScanEndpointLocalPath:
    def test_local_path_still_accepted(self, tmp_path, monkeypatch):
        import backend.services.repo_store as rs
        (tmp_path / "app.py").write_text("pass\n")
        monkeypatch.setattr(rs, "save_scan", lambda s: None)

        resp = client.post("/repository/scan", json={
            "repository_path": str(tmp_path),
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["remote_repo"] is False

    def test_neither_field_returns_422(self, monkeypatch):
        import backend.services.repo_store as rs
        monkeypatch.setattr(rs, "save_scan", lambda s: None)

        resp = client.post("/repository/scan", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Orchestrator: test execution skipped for remote repos
# ---------------------------------------------------------------------------

class TestOrchestratorRemoteSkip:
    def test_test_run_skipped_for_remote(self, monkeypatch):
        """When the scan is marked remote_repo=True, test_run output says skipped."""
        from backend.services.orchestrator import run_analysis
        from backend.models.schemas import AnalysisJob, RepositoryScan
        import backend.services.repo_store as rs
        import backend.services.store as st

        fake_scan = RepositoryScan(
            id="remote-scan-999",
            repository_path="/tmp/fake",
            remote_repo=True,
        )
        monkeypatch.setattr(rs, "load_scan", lambda sid: fake_scan)

        saved_jobs: dict = {}
        saved_reports: dict = {}
        monkeypatch.setattr(st, "save_job", lambda j: saved_jobs.update({j.id: j}))
        monkeypatch.setattr(st, "save_report", lambda r: saved_reports.update({r.id: r}))

        # Minimal diff that parses without LLM calls
        with patch("backend.services.orchestrator.analyse_impact") as mi, \
             patch("backend.services.orchestrator.analyse_code_and_security") as mc, \
             patch("backend.services.orchestrator.analyse_test_gaps") as mt, \
             patch("backend.services.orchestrator.generate_tests") as mg, \
             patch("backend.services.orchestrator.assemble_report") as ma:

            from backend.models.schemas import (
                ImpactResult, CodeReviewResult, TestGapResult, TestGenResult, ReleaseReport
            )
            mi.return_value = ImpactResult()
            mc.return_value = CodeReviewResult()
            mt.return_value = TestGapResult()
            mg.return_value = TestGenResult()
            fake_report = ReleaseReport(job_id="j1", diff_id="d1")
            ma.return_value = fake_report

            job = AnalysisJob(diff_id="d1")
            run_analysis(job, "diff --git a/x b/x\n", repository_id="remote-scan-999")

        # assemble_report should have received a test_run with skipped message
        call_kwargs = ma.call_args[1]
        test_run: TestRunResult = call_kwargs["test_run"]
        assert "skipped" in test_run.output.lower()
        assert test_run.passed == 0
