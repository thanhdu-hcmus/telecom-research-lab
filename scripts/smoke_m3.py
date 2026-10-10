"""Live CLI smoke in a synthetic, isolated test repo, never a PI research project."""

import json
import os
import shutil
import uuid
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from lab import state
from lab.cli import app
from lab.io import git, load, read_jsonl, save
from lab.net import Network

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".cache" / ("m3-live-smoke-" + uuid.uuid4().hex[:8])
if WORK.exists():
    raise SystemExit("Smoke workspace already exists; use a new bounded folder to rerun")
shutil.copytree(ROOT / "config", WORK / "config")
save(WORK / "config/lab.config.yaml", {"library_root": "../m3-live-library", "contact_email": None})
profile = load(WORK / "config/thesis-profile.yaml")
profile["pi_reviewed"] = True  # Synthetic test profile only.
save(WORK / "config/thesis-profile.yaml", profile)
git(WORK, "init", "-b", "main")
git(WORK, "config", "user.name", "Synthetic fixture PI")
git(WORK, "config", "user.email", "fixture@example.invalid")
state.init(WORK, "fixture")
path = state.project(WORK, "fixture")
save(
    path / "scope.yaml",
    {
        "area": "Live tool integration fixture",
        "keywords": ["RIS", "NOMA"],
        "inclusion": ["RIS-NOMA metadata"],
        "exclusion": ["unrelated"],
        "year_from": 2020,
        "target_venues": ["test preprint"],
        "thesis_profile_reviewed": True,
    },
)
git(WORK, "add", ".")
git(WORK, "commit", "-m", "synthetic fixture init")
state.request(path, "G1")
with patch(
    "lab.state.pi_confirm", lambda _: None
):  # Test-only simulated PI input, not production bypass.
    state.decide(
        path, "G1", "approve", "Synthetic integration fixture; not real scientific approval"
    )
state.enter(path, "P2")
save(
    path / "literature/query-plan.yaml",
    {
        "queries": [
            {
                "source": "openalex",
                "query": '"reconfigurable intelligent surface" AND NOMA',
                "limit": 5,
            },
            {
                "source": "arxiv",
                "query": 'all:"reconfigurable intelligent surface" AND all:NOMA',
                "limit": 5,
            },
        ]
    },
)
runner = CliRunner()
reports = []
os.chdir(WORK)
for argv in [["lit", "search", "--project", "fixture", "--json"]]:
    result = runner.invoke(app, argv)
    reports.append({"argv": argv, "exit_code": result.exit_code, "output": result.stdout})
    if result.exit_code:
        raise SystemExit(result.stdout + str(result.exception))
items = read_jsonl(path / "literature/candidates.jsonl")
selected = next(r for r in items if r.get("arxiv_id"))
for argv in [
    ["lit", "fetch", selected["id"], "--project", "fixture", "--json"],
    ["lit", "extract", selected["id"], "--project", "fixture", "--json"],
]:
    result = runner.invoke(app, argv)
    reports.append({"argv": argv, "exit_code": result.exit_code, "output": result.stdout})
os.chdir(ROOT)
report = {
    "status": "PASS" if all(r["exit_code"] == 0 for r in reports) else "FAIL",
    "synthetic_fixture": True,
    "real_pi_gates_approved": 0,
    "results": len(items),
    "downloaded_record": selected["id"],
    "commands": reports,
}
save(ROOT / "docs/evidence/m3-live-smoke.json", report)
print(json.dumps(report))

# A specific-paper Semantic Scholar lookup avoids the broad anonymous search throttle.
try:
    with Network(ROOT) as net:
        data = net.json(
            "https://api.semanticscholar.org/graph/v1/paper/ARXIV:" + selected["arxiv_id"],
            params={
                "fields": "title,authors,year,abstract,venue,externalIds,citationCount,openAccessPdf"
            },
        )
    save(ROOT / "tests/fixtures/http/semanticscholar.json", {"data": [data]})
    save(
        ROOT / "docs/evidence/semantic-fixture-lookup.json",
        {"status": "PASS", "id": selected["arxiv_id"], "route": "specific paper lookup"},
    )
except ValueError as error:
    save(
        ROOT / "docs/evidence/semantic-fixture-lookup.json", {"status": "FAIL", "error": str(error)}
    )
raise SystemExit(report["status"] != "PASS")
