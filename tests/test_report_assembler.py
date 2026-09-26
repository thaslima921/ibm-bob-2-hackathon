"""Tests for report_assembler service."""
import pytest
from backend.models.schemas import (
    CodeReviewResult,
    Finding,
    ImpactResult,
    TestGapResult,
    TestGenResult,
    TestRunResult,
)
from backend.services.report_assembler import compute_verdict, assemble_report


def _make_finding(severity: str, category: str = "security") -> Finding:
    return Finding(
        file="test.py",
        severity=severity,
        category=category,
        title=f"{severity} issue",
        description="desc",
    )


def test_verdict_block_on_critical():
    cr = CodeReviewResult(
        security_issues=[_make_finding("critical")],
        severity_counts={"critical": 1},
    )
    tg = TestGapResult(gap_score=0.0)
    tr = TestRunResult()
    verdict, reasons = compute_verdict(cr, tg, tr)
    assert verdict == "BLOCK"
    assert any("critical" in r.lower() for r in reasons)


def test_verdict_block_on_failing_tests():
    cr = CodeReviewResult(severity_counts={})
    tg = TestGapResult(gap_score=0.0)
    tr = TestRunResult(failed=2)
    verdict, _ = compute_verdict(cr, tg, tr)
    assert verdict == "BLOCK"


def test_verdict_caution_on_high_severity():
    cr = CodeReviewResult(
        bugs=[_make_finding("high", "bug")],
        severity_counts={"high": 1},
    )
    tg = TestGapResult(gap_score=0.3)
    tr = TestRunResult(passed=3)
    verdict, _ = compute_verdict(cr, tg, tr)
    assert verdict == "CAUTION"


def test_verdict_caution_on_large_gap():
    cr = CodeReviewResult(severity_counts={})
    tg = TestGapResult(gap_score=0.7)
    tr = TestRunResult(passed=2)
    verdict, _ = compute_verdict(cr, tg, tr)
    assert verdict == "CAUTION"


def test_verdict_go_clean():
    cr = CodeReviewResult(severity_counts={"low": 1})
    tg = TestGapResult(gap_score=0.2)
    tr = TestRunResult(passed=5)
    verdict, _ = compute_verdict(cr, tg, tr)
    assert verdict == "GO"


def test_verdict_caution_on_test_errors():
    """Test errors (not failures) should trigger CAUTION, not BLOCK."""
    cr = CodeReviewResult(severity_counts={})
    tg = TestGapResult(gap_score=0.0)
    tr = TestRunResult(errors=1)
    verdict, reasons = compute_verdict(cr, tg, tr)
    assert verdict == "CAUTION"
    assert any("error" in r.lower() for r in reasons)


def test_verdict_block_accumulates_both_reasons():
    """When both critical findings and failing tests exist, both reasons are reported."""
    cr = CodeReviewResult(severity_counts={"critical": 2})
    tg = TestGapResult(gap_score=0.0)
    tr = TestRunResult(failed=3)
    verdict, reasons = compute_verdict(cr, tg, tr)
    assert verdict == "BLOCK"
    assert len(reasons) == 2
    assert any("critical" in r.lower() for r in reasons)
    assert any("failing" in r.lower() or "failed" in r.lower() for r in reasons)


def test_verdict_block_failed_tests_reason_text():
    """BLOCK reason for failing tests should mention the count."""
    cr = CodeReviewResult(severity_counts={})
    tg = TestGapResult(gap_score=0.0)
    tr = TestRunResult(failed=4)
    verdict, reasons = compute_verdict(cr, tg, tr)
    assert verdict == "BLOCK"
    assert any("4" in r for r in reasons)


def test_verdict_go_reason_text():
    """GO verdict reason should be a positive message."""
    cr = CodeReviewResult(severity_counts={})
    tg = TestGapResult(gap_score=0.3)
    tr = TestRunResult(passed=2)
    verdict, reasons = compute_verdict(cr, tg, tr)
    assert verdict == "GO"
    assert len(reasons) == 1
    assert "critical" not in reasons[0].lower() or "no" in reasons[0].lower()


def test_assemble_report_structure():
    cr = CodeReviewResult(severity_counts={})
    tg = TestGapResult()
    tgen = TestGenResult()
    tr = TestRunResult()
    impact = ImpactResult()
    report = assemble_report("job1", "diff1", "Test label", impact, cr, tg, tgen, tr)
    assert report.job_id == "job1"
    assert report.diff_id == "diff1"
    assert report.release_verdict in {"GO", "CAUTION", "BLOCK"}
    assert len(report.verdict_reasons) > 0
