"""Use UTF-8/LF for authored artifacts across Windows and Linux checkouts."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for directory in ["lab", "scripts", "tests"]:
    for file in (ROOT / directory).rglob("*.py"):
        source = file.read_text(encoding="utf-8")
        lines = source.encode("utf-8").splitlines(keepends=True)
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line))
        inserts = []
        for node in ast.walk(ast.parse(source)):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "write_text"
                and not any(k.arg == "newline" for k in node.keywords)
            ):
                inserts.append(offsets[node.end_lineno - 1] + node.end_col_offset - 1)
        raw = source.encode("utf-8")
        for offset in sorted(inserts, reverse=True):
            # A trailing comma already separates the keyword from the prior argument.
            prefix = b"" if raw[:offset].rstrip().endswith(b",") else b", "
            raw = raw[:offset] + prefix + b'newline="\\n"' + raw[offset:]
        file.write_bytes(raw)

for directory in [
    "lab",
    "scripts",
    "tests",
    "schemas",
    "config",
    "templates",
    ".agents",
    ".codex",
    "matlab",
    "docs",
]:
    for file in (ROOT / directory).rglob("*"):
        if file.is_relative_to(ROOT / "docs/evidence/raw"):
            continue  # Original evaluated replies and execution transcripts are immutable.
        if file.is_file() and file.suffix in {
            ".py",
            ".md",
            ".yaml",
            ".json",
            ".toml",
            ".tex",
            ".bib",
            ".m",
            ".txt",
        }:
            file.write_bytes(file.read_bytes().replace(b"\r\n", b"\n"))
