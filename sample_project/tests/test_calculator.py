"""Tests for calculator module — happy-path only (testing gap intentional)."""
import pytest
from sample_project.app.calculator import add, subtract, multiply, divide, division_with_discount


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_subtract():
    assert subtract(10, 4) == 6
    assert subtract(0, 5) == -5


def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-2, 5) == -10


def test_divide_happy_path():
    assert divide(10, 2) == 5.0
    assert divide(9, 3) == 3.0


def test_division_with_discount_basic():
    # 10% off $100 = $90
    assert division_with_discount(100, 10) == 90.0
    # 0% = full price
    assert division_with_discount(50, 0) == 50.0


# TESTING GAP: no test for divide(x, 0) → ZeroDivisionError
# TESTING GAP: no test for discount_pct == 100 (should give $0 but bug allows slip)
# TESTING GAP: no test for apply_bulk_discount with quantity=0
# TESTING GAP: no test for compound_interest correctness
