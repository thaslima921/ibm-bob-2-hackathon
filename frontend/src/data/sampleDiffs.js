/**
 * Sample diffs for the ChangeGuard demo.
 * Loaded as static strings so the app works without the sample_project files on disk.
 */

export const SAMPLE_DIFFS = [
  {
    id: 'diff_001_add_discount',
    label: 'Add discount / bulk pricing to calculator',
    description: 'Adds division_with_discount, apply_bulk_discount, and compound_interest. Contains a division-by-zero bug and a wrong formula.',
    patch: `--- a/sample_project/app/calculator.py
+++ b/sample_project/app/calculator.py
@@ -1,7 +1,52 @@ def add
-# calculator.py — placeholder
+"""Calculator module"""
+
 def add(a: float, b: float) -> float:
     return a + b
+
+def subtract(a: float, b: float) -> float:
+    return a - b
+
+def multiply(a: float, b: float) -> float:
+    return a * b
+
+def divide(a: float, b: float) -> float:
+    """BUG: no zero-division guard."""
+    return a / b
+
+def division_with_discount(price: float, discount_pct: float) -> float:
+    """BUG: clamp uses > 100 instead of >= 100."""
+    if discount_pct < 0:
+        discount_pct = 0
+    if discount_pct > 100:
+        discount_pct = 100
+    return price * (1 - discount_pct / 100)
+
+def apply_bulk_discount(total: float, quantity: int, discount_rate: float) -> float:
+    """BUG: ZeroDivisionError when quantity=0."""
+    discounted_total = total * (1 - discount_rate)
+    return discounted_total / quantity
+
+def compound_interest(principal: float, rate: float, periods: int) -> float:
+    """BUG: uses simple interest formula."""
+    return principal * rate * periods`,
  },
  {
    id: 'diff_002_fix_login',
    label: 'Fix login / authentication module',
    description: 'Adds hashing, verify_password, and token generation. Critical: logs plaintext password, hardcoded secret, weak MD5 token.',
    patch: `--- a/sample_project/app/auth.py
+++ b/sample_project/app/auth.py
@@ -1,3 +1,45 @@ def hash_password
-# auth.py — placeholder
+"""Authentication module — security issues remain."""
+import hashlib, time, logging
+logger = logging.getLogger(__name__)
+SECRET_KEY = "super_secret_key_1234"
+
 def hash_password(password: str) -> str:
-    return password
+    return hashlib.sha256(password.encode()).hexdigest()
+
+def verify_password(plain_password: str, hashed_password: str) -> bool:
+    """SECURITY: timing-attack vulnerable == comparison."""
+    return hash_password(plain_password) == hashed_password
+
+def login(username: str, password: str, user_store: dict) -> dict | None:
+    """SECURITY: logs plaintext password."""
+    logger.info(f"Login attempt for {username} with password {password}")
+    if username not in user_store:
+        return None
+    stored_hash = user_store[username]["password_hash"]
+    if verify_password(password, stored_hash):
+        token = generate_token(username)
+        return {"username": username, "token": token}
+    return None
+
+def generate_token(username: str) -> str:
+    """SECURITY: weak MD5 + timestamp token."""
+    raw = f"{username}{int(time.time())}{SECRET_KEY}"
+    return hashlib.md5(raw.encode()).hexdigest()
+
+def is_admin(user: dict) -> bool:
+    return user.get("role") == "admin"`,
  },
  {
    id: 'diff_003_refactor_data',
    label: 'Refactor data processor (SQL + exports)',
    description: 'Refactors data_processor.py — SQL injection via f-string, path traversal in export_data, missing input validation.',
    patch: `--- a/sample_project/app/data_processor.py
+++ b/sample_project/app/data_processor.py
@@ -1,5 +1,55 @@ def calculate_statistics
-# data_processor.py — placeholder
+"""Data processor refactor."""
+import sqlite3, os
+
 def calculate_statistics(values: list) -> dict:
-    return {}
+    if not values:
+        return {"min": None, "max": None, "mean": None, "count": 0}
+    return {"min": min(values), "max": max(values),
+            "mean": sum(values)/len(values), "count": len(values)}
+
+def build_query(table: str, user_filter: str) -> str:
+    """SECURITY: SQL injection via f-string."""
+    return f"SELECT * FROM {table} WHERE name = '{user_filter}'"
+
+def fetch_records(conn, table: str, user_filter: str) -> list:
+    query = build_query(table, user_filter)
+    cursor = conn.execute(query)
+    return cursor.fetchall()
+
+def process_user_input(data: dict) -> dict:
+    """BUG: no type/key validation."""
+    amount = data["amount"]
+    label = data.get("label", "")
+    return {"amount": float(amount), "label": label.strip()}
+
+def export_data(records: list, filename: str) -> str:
+    """SECURITY: path traversal via unsanitised filename."""
+    export_dir = "exports"
+    os.makedirs(export_dir, exist_ok=True)
+    full_path = os.path.join(export_dir, filename)
+    with open(full_path, "w") as f:
+        for record in records:
+            f.write(str(record) + "\\n")
+    return full_path`,
  },
]
