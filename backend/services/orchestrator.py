"""
Orchestrator — runs the full analysis pipeline for a given diff.

Steps:
  1. Parse the diff
  2. Analyse impact
  3. Analyse code & security (parallel conceptually, sequential here for simplicity)
  4. Analyse test gaps
  5. Generate tests for gaps
  6. Run generated tests  (skipped for remote repositories — untrusted code safety)
  7. Assemble the final report
  8. Persist job + report

This runs synchronously in a background thread (via FastAPI's run_in_executor).
"""
from __future__ import annotations
import traceback

from backend.models.schemas import AnalysisJob, SubagentStatus, TestRunResult
from backend.services.diff_parser import parse_diff
from backend.services.analyzer import (
    analyse_impact,
    analyse_code_and_security,
    analyse_test_gaps,
    generate_tests,
)
from backend.services.test_runner import run_existing_tests, run_generated_tests
from backend.services.report_assembler import assemble_report
from backend.services import store, repo_store


def _set_stage(job: AnalysisJob, stage: str, state: str) -> None:
    setattr(job.subagent_status, stage, state)
    store.save_job(job)


def _is_remote_repo(repository_id: str | None) -> bool:
    """Return True if the analysis is for a remotely cloned repository."""
    if not repository_id:
        return False
    scan = repo_store.load_scan(repository_id)
    return scan is not None and scan.remote_repo


def run_analysis(
    job: AnalysisJob,
    diff_text: str,
    repository_id: str | None = None,
) -> None:
    """Execute the full analysis pipeline. Called in a background thread."""
    try:
        job.status = "running"
        store.save_job(job)

        remote = _is_remote_repo(repository_id)

        # --- Stage 1: Parse diff ---
        parsed = parse_diff(diff_text)

        # --- Stage 2: Impact analysis ---
        _set_stage(job, "impact", "running")
        impact = analyse_impact(parsed)
        _set_stage(job, "impact", "done")

        # --- Stage 3: Code & security review ---
        _set_stage(job, "code_review", "running")
        code_review = analyse_code_and_security(parsed)
        _set_stage(job, "code_review", "done")

        # --- Stage 4: Test gap analysis ---
        _set_stage(job, "test_gap", "running")
        test_gap = analyse_test_gaps(parsed)
        _set_stage(job, "test_gap", "done")

        # --- Stage 5: Test generation ---
        _set_stage(job, "test_gen", "running")
        test_gen = generate_tests(test_gap, parsed)
        _set_stage(job, "test_gen", "done")

        # --- Stage 6: Run tests ---
        _set_stage(job, "test_run", "running")
        if remote:
            # Safety: never execute untrusted code from a remote repository
            # on the server.  Test execution is skipped until a proper sandbox
            # is available.
            test_run = TestRunResult(
                passed=0,
                failed=0,
                errors=0,
                output=(
                    "⚠ Test execution skipped for remote repositories.\n"
                    "Running untrusted repository code on the server is disabled "
                    "for security. Provide a local repository or a sandboxed "
                    "execution environment to enable test runs."
                ),
            )
        else:
            combined_code = "\n\n".join(t.test_code for t in test_gen.generated_tests)
            if combined_code.strip():
                test_run = run_generated_tests(combined_code)
            else:
                test_run = run_existing_tests()
        _set_stage(job, "test_run", "done")

        # --- Stage 7: Assemble report ---
        report = assemble_report(
            job_id=job.id,
            diff_id=job.diff_id,
            label=job.label,
            impact=impact,
            code_review=code_review,
            test_gap=test_gap,
            test_gen=test_gen,
            test_run=test_run,
        )
        store.save_report(report)

        job.status = "complete"
        job.report_id = report.id
        store.save_job(job)

    except Exception as exc:  # noqa: BLE001
        job.status = "error"
        job.error = traceback.format_exc()
        store.save_job(job)
        raise
