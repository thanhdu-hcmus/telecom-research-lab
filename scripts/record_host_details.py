"""Read host hardware and built-in Codex diagnostics; retain only setup data."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from probe_environment import ROOT, command, tool


def main() -> int:
    details = {}
    queries = {
        "os": "Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,OSArchitecture | ConvertTo-Json -Compress",
        "computer": "Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,TotalPhysicalMemory | ConvertTo-Json -Compress",
        "gpu": "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion | ConvertTo-Json -Compress",
    }
    for key, query in queries.items():
        result = tool("pwsh", ["-NoProfile", "-Command", query])
        if result["status"] == "PASS":
            try:
                details[key] = json.loads(result["stdout"])
            except json.JSONDecodeError:
                details[key] = {"status": "UNVERIFIED", "reason": "No valid CIM result"}
        else:
            details[key] = {"status": "UNVERIFIED", "reason": result.get("stderr", result.get("reason"))}
    details["powershell_version"] = tool("pwsh", ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"])
    details["wsl_python"] = tool("wsl", ["-d", "Ubuntu", "--exec", "python3", "--version"])
    details["remote_workstation"] = {"status": "UNVERIFIED", "reason": "No remote workstation inventory or launch target supplied"}
    target = ROOT / "docs" / "evidence" / "host-platform.json"
    target.write_text(json.dumps(details, indent=2) + "\n", encoding="utf-8")
    doctor = tool("codex", ["doctor", "--json"])
    try:
        diagnostic = json.loads(doctor.get("stdout", ""))
        (target.parent / "codex-doctor.json").write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
    except json.JSONDecodeError:
        (target.parent / "codex-doctor.json").write_text(json.dumps({"status": "FAIL", "reason": doctor}) + "\n", encoding="utf-8")
    print("Host platform and redacted Codex diagnostics recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
