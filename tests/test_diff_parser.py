"""Tests for diff_parser service."""
import pytest
from backend.services.diff_parser import parse_diff

DIFF_001 = open("sample_project/diffs/diff_001_add_discount.patch").read()
DIFF_002 = open("sample_project/diffs/diff_002_fix_login.patch").read()
DIFF_003 = open("sample_project/diffs/diff_003_refactor_data.patch").read()


def test_parse_diff_001_detects_file():
    result = parse_diff(DIFF_001)
    paths = result.changed_file_paths
    assert any("calculator.py" in p for p in paths)


def test_parse_diff_001_counts_lines():
    result = parse_diff(DIFF_001)
    calc = next(f for f in result.files if "calculator.py" in f.path)
    assert calc.added_lines > 0


def test_parse_diff_002_detects_auth():
    result = parse_diff(DIFF_002)
    paths = result.changed_file_paths
    assert any("auth.py" in p for p in paths)


def test_parse_diff_003_detects_data_processor():
    result = parse_diff(DIFF_003)
    paths = result.changed_file_paths
    assert any("data_processor.py" in p for p in paths)


def test_parse_empty_diff():
    result = parse_diff("")
    assert result.files == []
    assert result.total_added == 0
    assert result.total_removed == 0


def test_parse_diff_all_changed_functions_qualified():
    result = parse_diff(DIFF_001)
    # all_changed_functions should be :: qualified
    for fn in result.all_changed_functions:
        assert "::" in fn


def test_parse_diff_002_removed_lines():
    result = parse_diff(DIFF_002)
    auth = next((f for f in result.files if "auth.py" in f.path), None)
    assert auth is not None
    # The diff has a removed placeholder line
    assert auth.removed_lines >= 1
