"""
Calculator module — intentionally contains logic bugs for ChangeGuard demo.

Known issues:
  - division_with_discount: off-by-one in percentage clamp (allows 101%)
  - apply_bulk_discount: division by zero when quantity=0
  - compound_interest: wrong formula uses simple interest formula
"""


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b. BUG: no zero-division guard."""
    return a / b  # BUG: raises ZeroDivisionError when b == 0


def division_with_discount(price: float, discount_pct: float) -> float:
    """Apply a percentage discount to a price.

    BUG: clamp condition uses > 100 instead of >= 100, allowing 100.something%
    which results in a negative price that slips through validation.
    """
    if discount_pct < 0:
        discount_pct = 0
    if discount_pct > 100:  # BUG: should be >= 100 to block exactly 100%
        discount_pct = 100
    return price * (1 - discount_pct / 100)


def apply_bulk_discount(total: float, quantity: int, discount_rate: float) -> float:
    """Return per-unit discounted price.

    BUG: no guard against quantity == 0 → ZeroDivisionError.
    """
    discounted_total = total * (1 - discount_rate)
    return discounted_total / quantity  # BUG: ZeroDivisionError when quantity=0


def compound_interest(principal: float, rate: float, periods: int) -> float:
    """Calculate compound interest.

    BUG: uses simple-interest formula instead of compound formula.
    Should be: principal * ((1 + rate) ** periods - 1)
    """
    return principal * rate * periods  # BUG: simple interest, not compound
