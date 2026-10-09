"""Record optional Gemini account access without using paid API credentials."""
from __future__ import annotations

import json
import os
from pathlib import Path

from probe_environment import ROOT, executable, command


def main() -> int:
    oauth_present = (Path.home() / ".gemini" / "oauth_creds.json").exists()
    api_env_present = any(os.environ.get(key) for key in ["GEMINI_API_KEY", "GOOGLE_API_KEY"])
    result = {"optional": True, "oauth_file_present": oauth_present,
              "api_key_env_present": api_env_present, "subscription_entitlements": "UNVERIFIED"}
    if not oauth_present or api_env_present:
        result["status"] = "NOT_RUN"
        result["reason"] = "OAuth login unavailable or API-key environment would change the billing route"
    else:
        gemini = executable("gemini")
        if not gemini:
            result["status"] = "MISSING"
        else:
            smoke = command(gemini + ["-p", "Reply only GEMINI_M0_SMOKE_PASS. Do not use tools or read files.",
                                      "--output-format", "json"], timeout=90)
            result["probe"] = smoke
            result["status"] = "PASS" if smoke["status"] == "PASS" and "GEMINI_M0_SMOKE_PASS" in smoke.get("stdout", "") else "FAIL"
    target = ROOT / "docs" / "evidence" / "gemini-access.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "probe"}, indent=2))
    return 0  # Optional capability never blocks M0.


if __name__ == "__main__":
    raise SystemExit(main())
