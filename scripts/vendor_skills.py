"""Fetch only selected upstream SKILL.md files and the license at a fixed commit.

No upstream code or installer is run. Retained originals are data for review,
not discovered executable instructions. Adapted project skills live separately.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "773a52944ba4747a18bd4ae9ade53fff041adcbc"
PATHS = [
    "LICENSE",
    "0-autoresearch-skill/SKILL.md",
    "10-optimization/ml-training-recipes/SKILL.md",
    "13-mlops/tensorboard/SKILL.md",
    "20-ml-paper-writing/academic-plotting/SKILL.md",
    "20-ml-paper-writing/ml-paper-writing/SKILL.md",
    "21-research-ideation/brainstorming-research-ideas/SKILL.md",
    "21-research-ideation/creative-thinking-for-research/SKILL.md",
    "22-agent-native-research-artifact/research-manager/SKILL.md",
    "22-agent-native-research-artifact/rigor-reviewer/SKILL.md",
]


def main():
    records = []
    for name in PATHS:
        request = urllib.request.Request(
            f"https://raw.githubusercontent.com/Orchestra-Research/AI-Research-SKILLs/{COMMIT}/{name}",
            headers={"User-Agent": "telecom-research-lab-vendor/0.1"},
        )
        with urllib.request.urlopen(request, timeout=40) as response:
            data = response.read(2_000_000)
        path = ROOT / "vendor/orchestra" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        records.append(
            {
                "path": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "review": "pending",
            }
        )
    manifest = {
        "upstream": "https://github.com/Orchestra-Research/AI-Research-SKILLs",
        "commit": COMMIT,
        "license": "MIT",
        "scope": "Selected SKILL.md source documents only; supporting scripts/assets deliberately excluded. Originals are not discovered as project skills.",
        "files": records,
        "adaptations": {},
    }
    # JSON is valid YAML; no bootstrapping dependency necessary.
    (ROOT / "vendor/MANIFEST.yaml").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"commit": COMMIT, "files": len(records)}))


if __name__ == "__main__":
    main()
