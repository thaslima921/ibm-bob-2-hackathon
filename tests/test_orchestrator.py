"""Integration tests for the orchestrator (mocked file I/O)."""
import pytest
from unittest.mock import patch, MagicMock
from backend.models.schemas import AnalysisJob
from backend.services.orchestrator import run_analysis


def _make_job() -> AnalysisJob:
    return AnalysisJob(diff_id="test_diff", label="test")


SIMPLE_DIFF = """\
--- a/sample_project/app/calculator.py
+++ b/sample_project/app/calculator.py
@@ -1,3 +1,10 @@ def add
+def divide(a, b):
+    return a / b
"""


def test_orchestrator_completes(tmp_path, monkeypatch):
    """Full pipeline should run to completion for a valid diff."""
    # Redirect store to tmp_path
    import backend.services.store as store_mod
    monkeypatch.setattr(store_mod, "STORE_DIR", tmp_path)

    # Patch run_generated_tests to avoid subprocess
    from backend.services import test_runner
    monkeypatch.setattr(
        test_runner,
        "run_generated_tests",
        lambda code: __import__("backend.models.schemas", fromlist=["TestRunResult"]).TestRunResult(passed=3),
    )

    job = _make_job()
    # Patch save/load so they use our tmp_path
    saved = {}

    def fake_save_job(j):
        saved["job"] = j

    def fake_save_report(r):
        saved["report"] = r

    monkeypatch.setattr(store_mod, "save_job", fake_save_job)
    monkeypatch.setattr(store_mod, "save_report", fake_save_report)

    run_analysis(job, SIMPLE_DIFF)

    assert job.status == "complete"
    assert job.report_id is not None
    assert "report" in saved


def test_orchestrator_error_on_bad_diff(monkeypatch):
    """Orchestrator should set status=error if analysis raises."""
    import backend.services.store as store_mod
    saved = {}
    monkeypatch.setattr(store_mod, "save_job", lambda j: saved.update({"job": j}))
    monkeypatch.setattr(store_mod, "save_report", lambda r: None)

    # Patch analyser to raise
    import backend.services.orchestrator as orch
    monkeypatch.setattr(orch, "analyse_impact", lambda p: (_ for _ in ()).throw(RuntimeError("boom")))

    job = _make_job()
    with pytest.raises(RuntimeError):
        run_analysis(job, SIMPLE_DIFF)

    assert job.status == "error"
