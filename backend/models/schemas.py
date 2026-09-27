"""Pydantic schemas for ChangeGuard backend."""
from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Repository scan models
# ---------------------------------------------------------------------------

class RepositoryScanRequest(BaseModel):
    # Exactly one of these must be provided:
    # - repository_path: local filesystem path (local dev only)
    # - github_url: public GitHub HTTPS URL
    repository_path: str = ""
    github_url: str = ""
    description: str = ""


class RepoCommit(BaseModel):
    sha: str
    short_sha: str
    message: str
    author: str = ""
    date: str = ""
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0


class RepositoryScan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repository_path: str
    description: str = ""
    scanned_at: str = Field(default_factory=_now)
    # project metadata
    project_name: str = ""
    detected_languages: list[str] = []
    framework_indicators: list[str] = []
    # file counts
    source_file_count: int = 0
    test_file_count: int = 0
    config_file_count: int = 0
    # important paths
    source_files: list[str] = []      # capped list of representative paths
    test_files: list[str] = []
    config_files: list[str] = []
    dependency_files: list[str] = []
    important_dirs: list[str] = []
    # git
    is_git_repo: bool = False
    current_branch: str = ""
    latest_commit: str = ""
    recent_commits: list[RepoCommit] = []
    # For remote repos: flag that test execution is disabled for safety
    remote_repo: bool = False
    # status / errors
    error: str | None = None


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AnalysisRequest(BaseModel):
    diff_id: str
    diff_text: str
    label: str = ""
    # optional repository context wired from a prior /repository/scan
    repository_id: str | None = None
    project_description: str = ""


class SubagentStatus(BaseModel):
    impact: str = "pending"
    code_review: str = "pending"
    test_gap: str = "pending"
    test_gen: str = "pending"
    test_run: str = "pending"


class AnalysisJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "queued"  # queued | running | complete | error
    diff_id: str = ""
    label: str = ""
    created_at: str = Field(default_factory=_now)
    subagent_status: SubagentStatus = Field(default_factory=SubagentStatus)
    report_id: str | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Report sub-models
# ---------------------------------------------------------------------------

class ChangedFile(BaseModel):
    path: str
    added_lines: int = 0
    removed_lines: int = 0
    changed_functions: list[str] = []


class RippleRisk(BaseModel):
    area: str
    reason: str
    severity: str = "medium"  # low | medium | high


class ImpactResult(BaseModel):
    changed_files: list[ChangedFile] = []
    changed_functions: list[str] = []
    ripple_risk_areas: list[RippleRisk] = []


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    file: str
    function: str = ""
    line: int | None = None
    severity: str = "medium"  # low | medium | high | critical
    category: str = ""
    title: str
    description: str
    recommendation: str = ""


class CodeReviewResult(BaseModel):
    bugs: list[Finding] = []
    quality_issues: list[Finding] = []
    security_issues: list[Finding] = []
    severity_counts: dict[str, int] = {}


class TestGapResult(BaseModel):
    covered_functions: list[str] = []
    uncovered_functions: list[str] = []
    missing_edge_cases: list[str] = []
    gap_score: float = 0.0  # 0.0 = fully covered, 1.0 = nothing tested


class GeneratedTest(BaseModel):
    function: str
    test_code: str
    rationale: str


class TestGenResult(BaseModel):
    generated_tests: list[GeneratedTest] = []


class TestRunResult(BaseModel):
    passed: int = 0
    failed: int = 0
    errors: int = 0
    output: str = ""


# ---------------------------------------------------------------------------
# Full release report
# ---------------------------------------------------------------------------

class ReleaseReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    diff_id: str
    label: str = ""
    created_at: str = Field(default_factory=_now)
    release_verdict: str = "GO"  # GO | CAUTION | BLOCK
    verdict_reasons: list[str] = []
    impact: ImpactResult = Field(default_factory=ImpactResult)
    code_review: CodeReviewResult = Field(default_factory=CodeReviewResult)
    test_gap: TestGapResult = Field(default_factory=TestGapResult)
    test_gen: TestGenResult = Field(default_factory=TestGenResult)
    test_run: TestRunResult = Field(default_factory=TestRunResult)
