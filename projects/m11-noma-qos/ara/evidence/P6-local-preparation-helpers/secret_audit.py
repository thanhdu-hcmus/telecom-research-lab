"""Classify new exact checksum detections using concrete P6 local byte evidence."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from lab.io import load, now, sha256
from lab.state import decisions
from scripts.check_secrets import EXCLUDED

r = Path.cwd()
p = r / "projects/m11-noma-qos"
g = ["git", "-c", f"safe.directory={r.as_posix()}"]
inventory = [
    v
    for v in subprocess.run(
        g + ["ls-files", "-z"], capture_output=True, text=True, check=True
    ).stdout.split("\0")
    if v
]
files = sorted(v for v in inventory if not EXCLUDED.search(v))
baseline_path = r / ".secrets.baseline"
baseline = load(baseline_path)
known = {}


def add(value, proof):
    known.setdefault(hashlib.sha1(value.encode()).hexdigest(), proof)


for name in inventory:
    f = r / name
    if f.is_file():
        add(sha256(f), "Actual indexed-file working bytes: " + name)
prep = load(p / "analysis/supplement/preparation.json")
for name, digest in prep["inputs"].items():
    assert sha256(p / name) == digest, name
    add(
        digest,
        "Actual locally rehashed P6 preparation input/output bytes: projects/m11-noma-qos/" + name,
    )
for rec in decisions(p):
    add(rec["record_hash"], "Validated canonical append-only gate chain " + rec["gate"])
for commit in subprocess.run(
    g + ["rev-list", "HEAD"], capture_output=True, text=True, check=True
).stdout.splitlines():
    assert (
        subprocess.run(
            g + ["cat-file", "-t", commit], capture_output=True, text=True, check=True
        ).stdout.strip()
        == "commit"
    )
    add(commit, "Actual Git ancestor commit object")
# Published historical digests retain immutable concrete classifications; no broad hex exclusion.
for name in [
    "m11-p5-secret-audit.json",
    "m11-p6-secret-audit.json",
    "m11-p5-rerun-secret-audit-results.json",
]:
    rel = "docs/evidence/" + name
    blob = subprocess.run(g + ["show", "ca443b7:" + rel], capture_output=True, check=True).stdout
    assert hashlib.sha256(blob).hexdigest() == sha256(r / rel), rel
    old = json.loads(blob)
    assert old["status"] == "PASS"
    for e in old["new_allowlist_entries"]:
        proof = e["evidence"]
        known.setdefault(
            e["hashed_secret"],
            "Exact historical published digest with immutable proof in ca443b7:"
            + rel
            + "; "
            + (proof[0] if isinstance(proof, list) else proof),
        )
scanner = Path(sys.executable).parent / "detect-secrets.exe"
new = []
unknown = []
for offset in range(0, len(files), 36):
    result = subprocess.run(
        [str(scanner), "scan", "--all-files", *files[offset : offset + 36]],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        check=True,
        timeout=120,
    )
    for path, hits in json.loads(result.stdout)["results"].items():
        path = path.replace("\\", "/")
        existing = {
            v["hashed_secret"]
            for v in baseline["results"].get(path, [])
            if v.get("is_secret") is False
        }
        for hit in hits:
            if hit["hashed_secret"] in existing:
                continue
            proof = known.get(hit["hashed_secret"])
            if hit["type"] != "Hex High Entropy String" or not proof:
                unknown.append({"path": path, **hit})
                continue
            new.append(
                {
                    "path": path,
                    "line": hit["line_number"],
                    "type": hit["type"],
                    "hashed_secret": hit["hashed_secret"],
                    "evidence": [proof],
                }
            )
            baseline["results"].setdefault(path, []).append({**hit, "is_secret": False})
            existing.add(hit["hashed_secret"])
report = {
    "timestamp": now(),
    "status": "FAIL" if unknown else "PASS",
    "files_scanned": len(files),
    "method": "Preserve existing exact reviewed baseline; each new checksum detection must match actual current indexed bytes, independently rehashed preparation inputs/raw outputs, canonical gate chain, actual Git ancestor object or exact historical immutable digest proof. No blanket hex or research-path allowlist.",
    "scientific_verification": False,
    "new_allowlist_entries": new,
    "unreviewed": unknown,
}
with (r / ".cache/p6-local-secret-audit-history.jsonl").open("a", encoding="utf-8") as f:
    f.write(json.dumps(report) + "\n")
if not unknown:
    save_target = r / "docs/evidence/m11-p6-local-preparation-secret-audit.json"
    save_target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    baseline_path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8", newline="\n")
print(
    json.dumps(
        {
            "status": report["status"],
            "files_scanned": len(files),
            "new_exact_entries": len(new),
            "unreviewed_count": len(unknown),
            "unreviewed": [
                {"path": v["path"], "line": v["line_number"], "type": v["type"]}
                for v in unknown[:8]
            ],
        }
    )
)
sys.exit(bool(unknown))
