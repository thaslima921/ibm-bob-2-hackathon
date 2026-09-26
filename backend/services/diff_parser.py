"""
Diff parser — converts unified diff text into structured ChangeGuard data.

Parses added/removed lines and infers changed Python functions by scanning
for 'def ' and 'class ' context lines in diff hunks.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field


@dataclass
class ParsedFile:
    path: str
    added_lines: int = 0
    removed_lines: int = 0
    changed_functions: list[str] = field(default_factory=list)
    raw_diff: str = ""


@dataclass
class ParsedDiff:
    files: list[ParsedFile] = field(default_factory=list)
    total_added: int = 0
    total_removed: int = 0

    @property
    def changed_file_paths(self) -> list[str]:
        return [f.path for f in self.files]

    @property
    def all_changed_functions(self) -> list[str]:
        fns: list[str] = []
        for f in self.files:
            for fn in f.changed_functions:
                qualified = f"{f.path}::{fn}"
                if qualified not in fns:
                    fns.append(qualified)
        return fns


# Regex patterns
_FILE_HEADER = re.compile(r"^\+\+\+ b?/?(.*)")
_HUNK_HEADER = re.compile(r"^@@ .* @@\s*(.*)")
_DEF_RE = re.compile(r"^\s*(?:def|class)\s+(\w+)")


def parse_diff(diff_text: str) -> ParsedDiff:
    """Parse a unified diff string into a ParsedDiff structure."""
    result = ParsedDiff()
    current_file: ParsedFile | None = None
    context_functions: list[str] = []

    for line in diff_text.splitlines():
        # New file header
        m = _FILE_HEADER.match(line)
        if m and not line.startswith("--- "):
            path = m.group(1).strip()
            # Skip /dev/null
            if path == "/dev/null":
                continue
            current_file = ParsedFile(path=path)
            result.files.append(current_file)
            context_functions = []
            continue

        if current_file is None:
            continue

        # Hunk header — extract function context hint after @@
        hh = _HUNK_HEADER.match(line)
        if hh:
            hint = hh.group(1).strip()
            if hint:
                dm = _DEF_RE.match(hint)
                if dm:
                    fn_name = dm.group(1)
                    if fn_name not in current_file.changed_functions:
                        current_file.changed_functions.append(fn_name)
            continue

        # Count added/removed lines
        if line.startswith("+") and not line.startswith("+++"):
            current_file.added_lines += 1
            result.total_added += 1
            # Check if this added line defines a function
            dm = _DEF_RE.match(line[1:])
            if dm:
                fn_name = dm.group(1)
                if fn_name not in current_file.changed_functions:
                    current_file.changed_functions.append(fn_name)
        elif line.startswith("-") and not line.startswith("---"):
            current_file.removed_lines += 1
            result.total_removed += 1
            # Check if this removed line defines a function
            dm = _DEF_RE.match(line[1:])
            if dm:
                fn_name = dm.group(1)
                if fn_name not in current_file.changed_functions:
                    current_file.changed_functions.append(fn_name)

    return result
