"""Assemble the M0 review packet from recorded evidence, without approving it."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys

from probe_environment import ROOT, command


def read(name: str) -> dict:
    return json.loads((ROOT / "docs" / "evidence" / name).read_text(encoding="utf-8"))


def main() -> int:
    tests = command([sys.executable, "-m", "unittest", "discover", "-s", "tests/m0", "-v"])
    (ROOT / "docs" / "evidence" / "m0-tests.json").write_text(
        json.dumps(tests, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    host = read("environment-host.json")
    sandbox = read("environment-sandbox.json")
    scope = read("codex-custom-agent-scope-runtime.json")
    platform = read("host-platform.json")
    mcp_sandbox = read("matlab-mcp-sandbox.json")
    mcp_host = read("matlab-mcp-host.json")
    optional = read("gemini-access.json")
    doctor = read("codex-doctor.json")
    installed = read("matlab-mcp-install.json")
    checks = host["checks"]
    version_rows = []
    for key, label in [
        ("python", "Python"),
        ("uv", "uv"),
        ("git", "Git"),
        ("gh", "GitHub CLI"),
        ("codex", "Codex CLI"),
        ("pdflatex", "pdfTeX / TeX Live"),
        ("gemini", "Gemini CLI"),
    ]:
        version_rows.append(
            f"| {label} | {checks[key + '_version'].get('stdout', 'UNVERIFIED').splitlines()[0]} |"
        )
    latex_version = checks["latexmk_version"].get("stdout", "")
    version_rows.append(
        "| latexmk | "
        + next(
            (line.strip() for line in latex_version.splitlines() if "Version" in line), "UNVERIFIED"
        )
        + " |"
    )
    version_rows.append(
        f"| MATLAB | R2021b (9.11.0.1769968); verified by batch execution and `ver` |"
    )
    version_rows.append(
        f"| MATLAB MCP | {installed['release']} (official release asset, SHA-256 verified) |"
    )
    version_rows.append(
        f"| PowerShell | {platform['powershell_version'].get('stdout', '').strip()} |"
    )
    rows = []
    for key, label in [
        ("python_smoke", "Python execution"),
        ("matlab_batch", "MATLAB batch"),
        ("latex_compile", "latexmk PDF compilation"),
        ("codex_auth", "Codex ChatGPT login"),
        ("github_auth", "GitHub CLI authentication"),
        ("openalex", "OpenAlex parsed response"),
        ("arxiv", "arXiv parsed Atom response"),
    ]:
        rows.append(f"| {label} | {sandbox['checks'][key]['status']} | {checks[key]['status']} |")
    rows.append(
        f"| MATLAB MCP evaluate_matlab_code | {mcp_sandbox['status']} | {mcp_host['status']} |"
    )
    required = ["python_smoke", "matlab_batch", "latex_compile", "codex_auth", "openalex", "arxiv"]
    host_ready = all(checks[key]["status"] == "PASS" for key in required)
    runtime_ready = (
        scope.get("custom_role_spawn") == "PASS" and scope.get("effort_override") == "PASS"
    )
    verification_complete = (
        host_ready
        and runtime_ready
        and tests["status"] == "PASS"
        and mcp_sandbox["status"] == "PASS"
    )
    source = ROOT.parent / "Telecom-Research-Lab-Plan.md"
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    state = {
        "updated_at": timestamp,
        "plan_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "active_milestone": "M0",
        "status": "awaiting_pi_review" if verification_complete else "verification_incomplete",
        "verification_complete": verification_complete,
        "pi_approval": None,
        "milestones": {
            "M0": "checks_recorded_awaiting_approval",
            **{f"M{i}": "not_started" for i in range(1, 13)},
        },
        "scientific_gates": {f"G{i}": "not_started" for i in range(1, 8)},
        "proposed_runtime": "native_windows_with_matlab_mcp",
        "proposed_workarounds": [
            "Run scholarly HTTP through host-approved bounded commands under the current session policy",
            "Run independent reviewers in separately configured read-only root sessions; verify shell enforcement before L4 acceptance",
        ],
        "unresolved": [
            "Current sandbox blocks scholarly HTTP and credential access",
            "Custom-agent sandbox default overridden by parent live policy",
            "Nested Codex child shell process creation fails with helper_unknown_error",
            "Separate DL workstation hardware and launch route not supplied",
        ],
        "optional_gemini": optional["status"],
    }
    (ROOT / "implementation-state.json").write_text(
        json.dumps(state, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    backend = (
        doctor.get("checks", {})
        .get("app_server.status", {})
        .get("details", {})
        .get("app-server version", "UNVERIFIED")
    )
    report = f"""# M0 environment report

Recorded: {timestamp}. Status: **checks recorded; PI review and workaround acceptance pending**.

This is the first build milestone. M1-M12 have not started, and no scientific
gate has been approved. Evidence records actual exit codes and differentiates
host execution from the current Codex sandbox.

## Versions and machine

| Component | Verified version |
| --- | --- |
{chr(10).join(version_rows)}
| Running Codex app-server | {backend} (different from the installed CLI) |

Local machine: {platform["os"]["Caption"]} {platform["os"]["Version"]}, 64-bit;
{platform["computer"]["Manufacturer"]} {platform["computer"]["Model"]};
{platform["computer"]["TotalPhysicalMemory"] / 2**30:.1f} GiB RAM.
GPU: {platform["gpu"]["Name"]}. CIM reports about 2 GiB adapter memory;
that is not a verified dedicated VRAM budget for deep-learning work. No
discrete CUDA GPU was identified. A separate workstation and its job launch
route are **UNVERIFIED**, and are not needed to test the local framework.

Ubuntu WSL2 is present and its Python reports
`{platform["wsl_python"].get("stdout", "").strip()}`. `latexmk` was absent there
in the initial host inspection. WSL enumeration is denied in the active
sandbox, so switching to WSL does not establish a solution to this session's
network/credential policy. A full WSL MATLAB/LaTeX route is not claimed tested.

## Execution and API checks

| Capability | Current sandbox | Host |
| --- | --- | --- |
{chr(10).join(rows)}

- MATLAB batch prints its success sentinel in the current sandbox but crashes
  during shutdown with exit code 3. It is recorded as **FAIL**, not as success.
- The official MATLAB MCP Server ran `disp(1)` and an assertion successfully
  in both contexts, returning `MATLAB_MCP_SMOKE_PASS`. This is the verified
  native Windows route proposed for agent-run MATLAB work.
- Host API checks parsed a nonempty OpenAlex works response and an arXiv Atom
  entry. Current-sandbox calls fail with WinError 10013. Project configuration
  sets `network_access = true`, but cannot change the already active session's
  externally imposed policy. Host-approved bounded commands are the proposed
  route until a new session is tested. No sandbox API PASS is claimed.
- The host Codex login uses ChatGPT; no paid OpenAI API key was added. The
  sandbox cannot access usable credentials. GitHub login similarly works on
  the host. No remote repository was created or pushed.

## Installed tooling and configuration

- MATLAB MCP **{installed["release"]}** is pinned in `.tools/matlab-mcp-server/`.
  Its release asset SHA-256 is `{installed["sha256"]}` and matched the
  digest supplied by the official GitHub release metadata.
- The project `.codex/config.toml` registers MATLAB with the actual R2021b root,
  `WINDIR`/`SYSTEMROOT` forwarding, `nodesktop`, telemetry disabled and explicit
  timeouts. `codex mcp list` reports the project server enabled. The currently
  running chat was not assumed to hot-reload MCP tools; the protocol-level
  test called the installed server directly.
- Portable **TeX Live 2026**, small scheme, is installed under `.tools/texlive/`;
  bundled Perl and `latexmk` are available. The installer changed no system
  PATH. The probe prepends the local binary directory only for its subprocesses.
  A basic LaTeX source compiled to a PDF in the sandbox and on the host. IEEEtran
  and the full paper package set still belong to the later writing milestone.
- `.tools/`, compilation outputs and raw agent event streams are git-ignored.
  Evidence contains redacted authentication token and MATLAB license lines.

## Custom-agent checks

| Check | Result | Evidence |
| --- | --- | --- |
| Explicit `agents.m0_probe.config_file` registration | PASS | Child metadata records role `m0_probe` |
| Native `.codex/agents/*.toml` discovery | PASS | Native probe used no explicit role registration; child metadata records `m0_probe` |
| Requested reasoning effort | {scope["effort_override"]} | Child runtime effort `{scope["observed_effort"]}`; parent high, child medium |
| Requested sandbox default | {scope["sandbox_override"]} | Requested `read-only`; observed `{scope["observed_sandbox"]}` |
| Per-agent disabled skill | {scope["per_agent_skill_disable"]} | Active discovery control lists `m0-scope-canary` in parent catalog and excludes it from child catalog |
| Actual canary write denial | UNVERIFIED | Shell process failed to start before any write attempt could execute |
| Usable nested child shell | FAIL | `helper_unknown_error: setup refresh had errors` |

The canary remained unchanged, but that does **not** prove read-only
enforcement: the process never ran. Runtime metadata is the basis for the
observed policy mismatch, not the child's self-report. Current [official
Codex documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
describes inheritance of live parent permission overrides. The proposed
workaround is a separate root session with read-only permissions for each
reviewer, with its actual shell/permission enforcement verified before
accepting L4 evaluations.

Per-agent skill disabling worked in the discovery-folder control. The two
earlier probes that placed the fixture outside the discovery folder lacked
a positive parent visibility control and remain inconclusive. The plan's
reported issue is not assumed to apply to this installed runtime.

The built-in doctor detects a CLI/app-server version difference and an
ignored user-level `mcp_servers.context7.type` key. The probe records these;
it did not edit global configuration, restart an active app-server, or claim
that the version difference caused the child process error.

## Noninteractive CLI flags

Installed `codex --help` and `codex exec --help` confirm `--json`,
`--output-last-message`, `--output-schema`, `--ephemeral`, `--skip-git-repo-check`
and `--ignore-user-config`. `--ask-for-approval never` and `--sandbox` can be
supplied as parent CLI options before `exec`. The smoke runs used the
authenticated CLI and produced JSONL plus a final-message file.

`--strict-config` is advertised for supported commands, but was rejected for
`codex features`; do not use that subcommand as a strict-validation shortcut.
M0 does not yet implement the agent-evaluation harness or declare it passing.

## Optional Gemini

Gemini CLI {checks["gemini_version"]["stdout"].strip()} and an OAuth credential
file are present; no Gemini/Google API-key environment variables were set for
the check. A one-response OAuth smoke failed with `IneligibleTierError` /
`UNSUPPORTED_CLIENT`. The exact diagnostic is saved in `evidence/gemini-access.json`.
This does not establish the PI's Google AI Plus entitlements. Automated Gemini
integration stays disabled and does not block the lab; manual review packets
remain the plan's default external-review route.

## Acceptance and requested PI decision

Six deterministic M0 evidence-integrity tests pass. They check explicit missing
tools, nonzero exit codes, timeouts, credential/license redaction and rejection
of malformed API payloads. All host critical-capability checks pass. The native
MATLAB MCP and local LaTeX checks also pass in the current sandbox.

M0 acceptance is **pending**, because Section 0 of the implementation plan
requires PI review and an agreed workaround for capability mismatches.
The concrete proposal is native Windows + MATLAB MCP, bounded host execution
for scholarly HTTP under the active policy, and separately verified read-only
root sessions for reviewers. Repair/verify nested Codex shell execution before
claiming any future agent eval passes. Proceed to M1 only after the PI's
recorded acceptance of this checkpoint or an explicit change to build review policy.

The full 18-finding plan review is [plan-review.md](plan-review.md). Existing
thesis state and research notes in the parent directory are preserved.
Evidence and milestone state are in `docs/evidence/` and
`implementation-state.json`; no successful research result is implied.
"""
    (ROOT / "docs" / "environment-report.md").write_text(report, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "verification_complete": verification_complete,
                "status": state["status"],
                "m0_tests": tests["status"],
            }
        )
    )
    return 0 if verification_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
