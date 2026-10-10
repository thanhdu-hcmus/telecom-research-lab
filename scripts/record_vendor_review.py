import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "vendor/MANIFEST.yaml"
data = json.loads(path.read_text(encoding="utf-8"))
for record in data["files"]:
    source = ROOT / "vendor/orchestra" / record["path"]
    record["upstream_sha256"] = record["sha256"]
    normalized = source.read_bytes().replace(b"\r\n", b"\n")
    source.write_bytes(normalized)
    record["sha256"] = hashlib.sha256(normalized).hexdigest()
    record["normalization"] = "CRLF to LF for portable Git contracts; upstream digest retained"
    record["review"] = "reviewed: docs/vendor-review.md; archival text only, no execution"
data["adaptations"] = {
    "0-autoresearch-skill": ["lab-orchestrator"],
    "brainstorming-research-ideas": ["brainstorming-research-ideas"],
    "creative-thinking-for-research": ["creative-thinking-for-research"],
    "rigor-reviewer": ["model-critique", "ieee-peer-review"],
    "research-manager": ["provenance-epilogue"],
    "ml-paper-writing": ["ieee-paper-writing"],
    "academic-plotting": ["ieee-figures"],
    "ml-training-recipes": ["ml-training-recipes"],
    "tensorboard": ["tensorboard (optional, M8)"],
}
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
