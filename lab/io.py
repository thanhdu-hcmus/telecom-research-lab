"""Portable serialization, paths and checksums shared by every command."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class LabError(ValueError):
    """An actionable, fail-closed command error."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def root(start: Path | None = None) -> Path:
    candidate = (start or Path.cwd()).resolve()
    for path in (candidate, *candidate.parents):
        if (path / "config/lab.config.yaml").exists():
            return path
    raise LabError("Run inside the framework repository or set --root.")


def load(path: Path, default: Any = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise LabError(f"Missing artifact: {path}")
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        json.dumps(value, indent=2, ensure_ascii=False) + "\n"
        if path.suffix == ".json"
        else yaml.safe_dump(value, sort_keys=False, allow_unicode=True)
    )
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path: Path, values: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in values), encoding="utf-8"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_id(value: str) -> str:
    prefix = re.sub(r"[^a-zA-Z0-9_-]", "_", value)[:42].rstrip("_") or "record"
    # Also avoids reserved Windows device names and normalization collisions.
    return "r_" + prefix + "_" + hashlib.sha256(value.encode()).hexdigest()[:12]


def within(base: Path, name: str | Path) -> Path:
    target = (base / name).resolve()
    if not target.is_relative_to(base.resolve()):
        raise LabError(f"Path escapes workspace: {name}")
    return target


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={repo.resolve().as_posix()}", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=60,
        env=os.environ.copy(),
    )
    if check and result.returncode:
        raise LabError(result.stderr.strip() or "Git operation failed")
    return result.stdout.strip()


def library(repo: Path) -> Path:
    value = load(repo / "config/lab.config.yaml")["library_root"]
    return (repo / os.path.expandvars(os.path.expanduser(value))).resolve()
