import hashlib
import json
import subprocess
import sys
from pathlib import Path

from lab.io import git, save

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/check_secrets.py"


def test_scan_finds_a_synthetic_canary_in_the_requested_repository(tmp_path):
    git(tmp_path, "init", "-b", "main")
    (tmp_path / ".secrets.baseline").write_text('{"results": {}}\n', encoding="utf-8")
    canary = hashlib.sha256(b"public synthetic secret-scanner regression canary").hexdigest()
    save(tmp_path / "fixture.json", {"canary": canary})
    git(tmp_path, "add", "--", ".secrets.baseline", "fixture.json")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path)], capture_output=True, text=True
    )
    report = json.loads(result.stdout)
    assert result.returncode == 1, report
    assert report["status"] == "FAIL"
    assert any(f[0] == "fixture.json" for f in report["findings"])
    assert report["files_scanned"] == 1


def test_scan_fails_closed_without_a_git_inventory(tmp_path):
    (tmp_path / ".secrets.baseline").write_text('{"results": {}}\n', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path)], capture_output=True, text=True
    )
    report = json.loads(result.stdout)
    assert result.returncode == 1, report
    assert report["status"] == "FAIL"
    assert "inventory" in report["error"].lower()
