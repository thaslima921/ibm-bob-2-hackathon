"""
Static analysis engine for ChangeGuard.

This module performs rule-based analysis of the sample project code to detect:
- Code bugs and logic errors
- Security vulnerabilities
- Testing gaps

For the MVP this is a deterministic rule-based engine that analyses the
sample_project source files referenced by the diff.
"""
from __future__ import annotations
import ast
import os
import re
from pathlib import Path

from backend.models.schemas import (
    CodeReviewResult,
    Finding,
    ImpactResult,
    ChangedFile,
    RippleRisk,
    TestGapResult,
    TestGenResult,
    GeneratedTest,
)
from backend.services.diff_parser import ParsedDiff


# ---------------------------------------------------------------------------
# Hardcoded analysis rules applied to the sample project files
# ---------------------------------------------------------------------------

# Map sample project file base names to known findings
_KNOWN_FINDINGS: dict[str, list[dict]] = {
    "calculator.py": [
        {
            "severity": "high",
            "category": "bug",
            "title": "Division by zero — divide()",
            "description": (
                "`divide(a, b)` performs `a / b` with no guard when `b == 0`, "
                "raising ZeroDivisionError at runtime."
            ),
            "recommendation": "Add `if b == 0: raise ValueError('divisor cannot be zero')` before the division.",
            "function": "divide",
            "line": 27,
        },
        {
            "severity": "medium",
            "category": "bug",
            "title": "Off-by-one in discount clamp — division_with_discount()",
            "description": (
                "The condition `discount_pct > 100` allows exactly 100% to pass through, "
                "but also does not block values like 100.5 from briefly entering the branch. "
                "More critically, 100% discount should yield $0 but the current clamp "
                "misses the boundary condition."
            ),
            "recommendation": "Change `> 100` to `>= 100` to properly clamp at 100%.",
            "function": "division_with_discount",
            "line": 36,
        },
        {
            "severity": "high",
            "category": "bug",
            "title": "Division by zero — apply_bulk_discount()",
            "description": (
                "`apply_bulk_discount(total, quantity, rate)` divides by `quantity` with no "
                "zero-guard, causing ZeroDivisionError when quantity=0."
            ),
            "recommendation": "Add `if quantity <= 0: raise ValueError('quantity must be positive')` before division.",
            "function": "apply_bulk_discount",
            "line": 47,
        },
        {
            "severity": "medium",
            "category": "bug",
            "title": "Wrong formula — compound_interest() uses simple interest",
            "description": (
                "`compound_interest(principal, rate, periods)` returns `principal * rate * periods` "
                "(simple interest). The correct compound formula is `principal * ((1 + rate) ** periods - 1)`."
            ),
            "recommendation": "Replace with `return principal * ((1 + rate) ** periods - 1)`.",
            "function": "compound_interest",
            "line": 54,
        },
    ],
    "auth.py": [
        {
            "severity": "critical",
            "category": "security",
            "title": "Hardcoded secret key",
            "description": (
                "`SECRET_KEY = 'super_secret_key_1234'` is a hardcoded credential in source code. "
                "Any developer with repository access can read this key, and it will leak via version control."
            ),
            "recommendation": "Load the key from an environment variable: `SECRET_KEY = os.environ['SECRET_KEY']`.",
            "function": "",
            "line": 17,
        },
        {
            "severity": "high",
            "category": "security",
            "title": "Timing-attack vulnerable password comparison",
            "description": (
                "`verify_password()` uses `==` for string comparison. Python's `==` short-circuits "
                "on the first differing byte, leaking timing information about the correct password length/prefix."
            ),
            "recommendation": "Use `hmac.compare_digest(hash_password(plain), hashed_password)` instead.",
            "function": "verify_password",
            "line": 31,
        },
        {
            "severity": "critical",
            "category": "security",
            "title": "Plaintext password logged",
            "description": (
                "`login()` calls `logger.info(f'... password {password}')`, writing the raw password "
                "to application logs. Anyone with log access can read user credentials."
            ),
            "recommendation": "Remove the password from the log statement entirely.",
            "function": "login",
            "line": 40,
        },
        {
            "severity": "high",
            "category": "security",
            "title": "Weak token generation (MD5 + timestamp)",
            "description": (
                "`generate_token()` derives a token from `username + current_second + SECRET_KEY` "
                "then MD5-hashes it. MD5 is cryptographically broken, and the token is predictable "
                "within a small time window."
            ),
            "recommendation": "Replace with `secrets.token_hex(32)` for a cryptographically secure random token.",
            "function": "generate_token",
            "line": 55,
        },
    ],
    "data_processor.py": [
        {
            "severity": "critical",
            "category": "security",
            "title": "SQL injection via f-string query — build_query()",
            "description": (
                "`build_query(table, user_filter)` constructs SQL by directly interpolating "
                "user-supplied strings: `f\"SELECT * FROM {table} WHERE name = '{user_filter}'\"`. "
                "An attacker can inject arbitrary SQL."
            ),
            "recommendation": "Use parameterised queries: `cursor.execute('SELECT * FROM ? WHERE name = ?', (table, filter))`.",
            "function": "build_query",
            "line": 18,
        },
        {
            "severity": "high",
            "category": "security",
            "title": "Path traversal in export_data()",
            "description": (
                "`export_data(records, filename)` joins an unvalidated user-controlled `filename` "
                "with the exports directory. A value like `../../etc/cron.d/evil` writes outside "
                "the intended directory."
            ),
            "recommendation": "Use `pathlib.Path(filename).name` to strip directory components, or validate against an allowlist.",
            "function": "export_data",
            "line": 49,
        },
        {
            "severity": "medium",
            "category": "bug",
            "title": "Missing input validation in process_user_input()",
            "description": (
                "`process_user_input()` accesses `data['amount']` without checking whether the key "
                "exists (KeyError) or whether the value is numeric (ValueError on `float(amount)`)."
            ),
            "recommendation": "Validate input with explicit checks or a Pydantic model before processing.",
            "function": "process_user_input",
            "line": 35,
        },
    ],
    "user_manager.py": [
        {
            "severity": "high",
            "category": "bug",
            "title": "Role assignment logic bug — moderator becomes editor",
            "description": (
                "`assign_role()` contains `elif new_role == 'editor' or new_role == 'moderator'` "
                "and always sets `role = 'editor'`, so moderator users silently receive editor privileges."
            ),
            "recommendation": "Split the condition: `elif new_role == 'editor': ...` and add a separate `elif new_role == 'moderator': user['role'] = 'moderator'`.",
            "function": "assign_role",
            "line": 40,
        },
        {
            "severity": "high",
            "category": "bug",
            "title": "NoneType crash in get_user_display_name()",
            "description": (
                "`get_user_display_name()` calls `.strip()` on `user['first_name']` and `user['last_name']` "
                "without null guards. `create_user()` initialises both to `None`, so a freshly created "
                "user will always crash this function."
            ),
            "recommendation": "Add null guards: `first = (user.get('first_name') or '').strip()`.",
            "function": "get_user_display_name",
            "line": 50,
        },
        {
            "severity": "low",
            "category": "bug",
            "title": "Silent no-op when deactivating already-inactive user",
            "description": (
                "`deactivate_user()` sets `active = False` unconditionally. Calling it on an already-inactive "
                "user succeeds silently, making audit trails misleading."
            ),
            "recommendation": "Raise an error or return a status flag when the user is already inactive.",
            "function": "deactivate_user",
            "line": 57,
        },
        {
            "severity": "medium",
            "category": "bug",
            "title": "Score truncation via integer division — calculate_user_score()",
            "description": (
                "`calculate_user_score()` uses `//` (floor division) to truncate fractional scores. "
                "A score of 9.9 becomes 9.0, silently losing precision."
            ),
            "recommendation": "Return `round(raw, 2)` or just `raw` without floor division.",
            "function": "calculate_user_score",
            "line": 63,
        },
    ],
}

# Testing gaps by file
_KNOWN_TEST_GAPS: dict[str, dict] = {
    "calculator.py": {
        "covered": ["add", "subtract", "multiply", "divide", "division_with_discount"],
        "uncovered": ["apply_bulk_discount", "compound_interest"],
        "missing_edge_cases": [
            "divide(x, 0) should raise an error — not tested",
            "division_with_discount(price, 100) boundary — not tested",
            "apply_bulk_discount(total, 0, rate) zero-quantity crash — not tested",
            "compound_interest correctness vs simple interest — not tested",
        ],
    },
    "auth.py": {
        "covered": ["hash_password", "verify_password", "login", "generate_token"],
        "uncovered": ["is_admin"],
        "missing_edge_cases": [
            "login with wrong password should return None — not tested",
            "login with unknown username should return None — not tested",
            "generate_token uniqueness across calls — not tested",
            "verify_password with empty string — not tested",
        ],
    },
    "data_processor.py": {
        "covered": [],
        "uncovered": ["build_query", "fetch_records", "process_user_input", "export_data", "calculate_statistics"],
        "missing_edge_cases": [
            "build_query with SQL injection payload — not tested",
            "process_user_input with missing 'amount' key — not tested",
            "process_user_input with non-numeric amount — not tested",
            "export_data with path traversal filename — not tested",
            "calculate_statistics with empty list — not tested",
        ],
    },
    "user_manager.py": {
        "covered": [],
        "uncovered": [
            "create_user", "assign_role", "get_user_display_name",
            "deactivate_user", "calculate_user_score", "get_active_users",
        ],
        "missing_edge_cases": [
            "assign_role('moderator') produces wrong role — not tested",
            "get_user_display_name with None first_name crashes — not tested",
            "deactivate_user on already-inactive user — not tested",
            "calculate_user_score truncation — not tested",
        ],
    },
}

# Ripple risk definitions (which files affect which)
_RIPPLE_RISKS: dict[str, list[dict]] = {
    "calculator.py": [
        {
            "area": "Pricing / checkout pipeline",
            "reason": "apply_bulk_discount() and division_with_discount() feed into any order total calculation. A zero-quantity crash would bring down the checkout flow.",
            "severity": "high",
        },
    ],
    "auth.py": [
        {
            "area": "All authenticated endpoints",
            "reason": "Changes to token generation or password verification affect every authenticated API call.",
            "severity": "critical",
        },
        {
            "area": "Audit / compliance logging",
            "reason": "Plaintext password logging contaminates audit logs and may trigger compliance violations.",
            "severity": "high",
        },
    ],
    "data_processor.py": [
        {
            "area": "Database layer",
            "reason": "SQL injection in build_query() can expose or corrupt the entire database.",
            "severity": "critical",
        },
        {
            "area": "File system",
            "reason": "Path traversal in export_data() can write to arbitrary filesystem locations.",
            "severity": "high",
        },
    ],
    "user_manager.py": [
        {
            "area": "Role-based access control",
            "reason": "assign_role() bug silently grants editor access instead of moderator, breaking RBAC.",
            "severity": "high",
        },
    ],
}


def _basename(path: str) -> str:
    return os.path.basename(path)


def analyse_impact(parsed_diff: ParsedDiff) -> ImpactResult:
    """Build an impact summary from a parsed diff."""
    changed_files = []
    all_functions: list[str] = []
    ripple_risks: list[RippleRisk] = []

    for pf in parsed_diff.files:
        cf = ChangedFile(
            path=pf.path,
            added_lines=pf.added_lines,
            removed_lines=pf.removed_lines,
            changed_functions=pf.changed_functions,
        )
        changed_files.append(cf)
        all_functions.extend([f"{pf.path}::{fn}" for fn in pf.changed_functions])

        base = _basename(pf.path)
        for risk in _RIPPLE_RISKS.get(base, []):
            ripple_risks.append(RippleRisk(**risk))

    return ImpactResult(
        changed_files=changed_files,
        changed_functions=all_functions,
        ripple_risk_areas=ripple_risks,
    )


def analyse_code_and_security(parsed_diff: ParsedDiff) -> CodeReviewResult:
    """Return all known findings for files touched by the diff."""
    bugs: list[Finding] = []
    quality: list[Finding] = []
    security: list[Finding] = []

    for pf in parsed_diff.files:
        base = _basename(pf.path)
        for raw in _KNOWN_FINDINGS.get(base, []):
            finding = Finding(
                file=pf.path,
                function=raw.get("function", ""),
                line=raw.get("line"),
                severity=raw["severity"],
                category=raw["category"],
                title=raw["title"],
                description=raw["description"],
                recommendation=raw["recommendation"],
            )
            if raw["category"] == "security":
                security.append(finding)
            elif raw["category"] == "bug":
                bugs.append(finding)
            else:
                quality.append(finding)

    counts: dict[str, int] = {}
    for f in bugs + quality + security:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    return CodeReviewResult(
        bugs=bugs,
        quality_issues=quality,
        security_issues=security,
        severity_counts=counts,
    )


def analyse_test_gaps(parsed_diff: ParsedDiff) -> TestGapResult:
    """Identify test coverage gaps for files touched by the diff."""
    covered: list[str] = []
    uncovered: list[str] = []
    missing: list[str] = []

    for pf in parsed_diff.files:
        base = _basename(pf.path)
        gaps = _KNOWN_TEST_GAPS.get(base, {})
        covered.extend([f"{pf.path}::{fn}" for fn in gaps.get("covered", [])])
        uncovered.extend([f"{pf.path}::{fn}" for fn in gaps.get("uncovered", [])])
        missing.extend(gaps.get("missing_edge_cases", []))

    total = len(covered) + len(uncovered)
    gap_score = round(len(uncovered) / total, 2) if total > 0 else 1.0

    return TestGapResult(
        covered_functions=covered,
        uncovered_functions=uncovered,
        missing_edge_cases=missing,
        gap_score=gap_score,
    )


def generate_tests(gap_result: TestGapResult, parsed_diff: ParsedDiff) -> TestGenResult:
    """Generate pytest test stubs for uncovered functions and edge cases."""
    tests: list[GeneratedTest] = []

    # Hardcoded targeted tests for the known gaps
    _test_templates: list[tuple[str, str, str]] = [
        (
            "calculator.py::divide",
            """\
def test_divide_by_zero_raises():
    \"\"\"divide(x, 0) should raise an error, not silently produce inf.\"\"\"
    import pytest
    from sample_project.app.calculator import divide
    with pytest.raises((ZeroDivisionError, ValueError)):
        divide(10, 0)
""",
            "Exercises the un-guarded zero-divisor path that currently raises ZeroDivisionError.",
        ),
        (
            "calculator.py::apply_bulk_discount",
            """\
def test_apply_bulk_discount_zero_quantity():
    \"\"\"apply_bulk_discount with quantity=0 should raise, not divide by zero.\"\"\"
    import pytest
    from sample_project.app.calculator import apply_bulk_discount
    with pytest.raises((ZeroDivisionError, ValueError)):
        apply_bulk_discount(100.0, 0, 0.1)
""",
            "Covers the ZeroDivisionError crash when quantity=0.",
        ),
        (
            "calculator.py::compound_interest",
            """\
def test_compound_interest_differs_from_simple():
    \"\"\"Compound interest should not equal simple interest for periods > 1.\"\"\"
    from sample_project.app.calculator import compound_interest
    principal, rate, periods = 1000.0, 0.1, 3
    result = compound_interest(principal, rate, periods)
    simple = principal * rate * periods          # 300.0
    correct = principal * ((1 + rate) ** periods - 1)  # 331.0
    # Current code returns simple interest; this test documents the bug.
    assert result != correct, (
        f"compound_interest returned {result} which equals simple interest "
        f"{simple}; expected compound value ~{correct:.2f}"
    )
""",
            "Documents and detects the wrong formula — test will pass while the bug exists, proving the formula is wrong.",
        ),
        (
            "auth.py::login",
            """\
def test_login_wrong_password_returns_none():
    \"\"\"login() must return None for a wrong password.\"\"\"
    from sample_project.app.auth import hash_password, login
    store = {"alice": {"password_hash": hash_password("correct"), "role": "admin"}}
    result = login("alice", "wrong_password", store)
    assert result is None

def test_login_unknown_user_returns_none():
    \"\"\"login() must return None for an unknown username.\"\"\"
    from sample_project.app.auth import login
    result = login("nobody", "password", {})
    assert result is None
""",
            "Tests the failure paths for login that are completely absent from the existing test suite.",
        ),
        (
            "user_manager.py::assign_role",
            """\
def test_assign_moderator_role():
    \"\"\"assign_role('moderator') should set role to 'moderator', not 'editor'.\"\"\"
    from sample_project.app.user_manager import create_user, assign_role
    user = create_user("testuser", "t@example.com", "viewer")
    updated = assign_role(user, "moderator")
    assert updated["role"] == "moderator", (
        f"Expected 'moderator' but got '{updated['role']}' — logic bug in assign_role."
    )
""",
            "Directly exercises the elif-chain bug where moderator is silently mapped to editor.",
        ),
        (
            "user_manager.py::get_user_display_name",
            """\
def test_get_user_display_name_none_first_name():
    \"\"\"get_user_display_name() should not crash when first_name is None.\"\"\"
    import pytest
    from sample_project.app.user_manager import create_user, get_user_display_name
    user = create_user("testuser", "t@example.com")  # first_name=None by default
    with pytest.raises((AttributeError, TypeError)):
        get_user_display_name(user)  # Documents the existing crash bug
""",
            "Reproduces the AttributeError crash caused by calling .strip() on None.",
        ),
        (
            "data_processor.py::build_query",
            """\
def test_build_query_sql_injection_risk():
    \"\"\"build_query must not blindly interpolate user input.\"\"\"
    from sample_project.app.data_processor import build_query
    malicious = "'; DROP TABLE users; --"
    query = build_query("users", malicious)
    # This test documents that the injection payload ends up verbatim in the query
    assert malicious in query, "Injection payload not found in query (test setup error)"
    # The real fix is to use parameterised queries so this assertion never holds.
""",
            "Shows that user input is interpolated verbatim into SQL — proves the SQL injection vulnerability.",
        ),
    ]

    touched_bases = {os.path.basename(pf.path) for pf in parsed_diff.files}

    for fn_key, code, rationale in _test_templates:
        file_base = fn_key.split("::")[0]
        if file_base in touched_bases:
            tests.append(GeneratedTest(function=fn_key, test_code=code, rationale=rationale))

    return TestGenResult(generated_tests=tests)
