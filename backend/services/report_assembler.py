"""
Report assembler — merges analysis results into a final ReleaseReport.

Verdict logic:
  BLOCK  — any critical severity finding (security or bug)
  CAUTION — any high severity finding, or gap_score >= 0.5, or any failed tests
  GO     — no issues above medium severity and gap_score < 0.5
"""
from __future__ import annotations
from backend.models.schemas import (
    CodeReviewResult,
    ImpactResult,
    ReleaseReport,
    TestGapResult,
    TestGenResult,
    TestRunResult,
)


def compute_verdict(
    code_review: CodeReviewResult,
    test_gap: TestGapResult,
    test_run: TestRunResult,
) -> tuple[str, list[str]]:
    reasons: list[str] = []

    # BLOCK conditions
    critical_count = code_review.severity_counts.get("critical", 0)
    if critical_count > 0:
        reasons.append(f"{critical_count} critical finding(s) detected — immediate remediation required.")

    if test_run.failed > 0:
        reasons.append(f"{test_run.failed} test(s) are failing.")

    if reasons:
        return "BLOCK", reasons

    # CAUTION conditions
    high_count = code_review.severity_counts.get("high", 0)
    if high_count > 0:
        reasons.append(f"{high_count} high-severity finding(s) require attention before release.")

    if test_gap.gap_score >= 0.5:
        pct = int(test_gap.gap_score * 100)
        reasons.append(f"Test coverage gap is {pct}% — too many untested functions.")

    if test_run.errors > 0:
        reasons.append(f"{test_run.errors} test error(s) encountered.")

    if reasons:
        return "CAUTION", reasons

    return "GO", ["No critical or high-severity issues found. Test coverage is adequate."]


def assemble_report(
    job_id: str,
    diff_id: str,
    label: str,
    impact: ImpactResult,
    code_review: CodeReviewResult,
    test_gap: TestGapResult,
    test_gen: TestGenResult,
    test_run: TestRunResult,
) -> ReleaseReport:
    verdict, reasons = compute_verdict(code_review, test_gap, test_run)
    return ReleaseReport(
        job_id=job_id,
        diff_id=diff_id,
        label=label,
        release_verdict=verdict,
        verdict_reasons=reasons,
        impact=impact,
        code_review=code_review,
        test_gap=test_gap,
        test_gen=test_gen,
        test_run=test_run,
    )
