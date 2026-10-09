# M0 environment report

Recorded: 2026-10-09T17:56:33.581918+00:00. Status: **checks recorded; PI review and workaround acceptance pending**.

This is the first build milestone. M1-M12 have not started, and no scientific
gate has been approved. Evidence records actual exit codes and differentiates
host execution from the current Codex sandbox.

## Versions and machine

| Component | Verified version |
| --- | --- |
| Python | Python 3.12.5 |
| uv | uv 0.12.6 (7938ca5d5 2026-08-25 x86_64-pc-windows-msvc) |
| Git | git version 2.45.2.windows.1 |
| GitHub CLI | gh version 2.87.3 (2026-02-23) |
| Codex CLI | codex-cli 0.161.0 |
| pdfTeX / TeX Live | pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026) |
| Gemini CLI | 0.38.2 |
| latexmk | Latexmk, John Collins, 9 March 2026. Version 4.88 |
| MATLAB | R2021b (9.11.0.1769968); verified by batch execution and `ver` |
| MATLAB MCP | v0.14.0 (official release asset, SHA-256 verified) |
| PowerShell | 7.6.6 |
| Running Codex app-server | 0.162.0 (different from the installed CLI) |

Local machine: Microsoft Windows 11 Pro 10.0.26200, 64-bit;
ASRock B760M-STX;
31.8 GiB RAM.
GPU: Intel(R) UHD Graphics 770. CIM reports about 2 GiB adapter memory;
that is not a verified dedicated VRAM budget for deep-learning work. No
discrete CUDA GPU was identified. A separate workstation and its job launch
route are **UNVERIFIED**, and are not needed to test the local framework.

Ubuntu WSL2 is present and its Python reports
`Python 3.12.3`. `latexmk` was absent there
in the initial host inspection. WSL enumeration is denied in the active
sandbox, so switching to WSL does not establish a solution to this session's
network/credential policy. A full WSL MATLAB/LaTeX route is not claimed tested.

## Execution and API checks

| Capability | Current sandbox | Host |
| --- | --- | --- |
| Python execution | PASS | PASS |
| MATLAB batch | FAIL | PASS |
| latexmk PDF compilation | PASS | PASS |
| Codex ChatGPT login | FAIL | PASS |
| GitHub CLI authentication | FAIL | PASS |
| OpenAlex parsed response | FAIL | PASS |
| arXiv parsed Atom response | FAIL | PASS |
| MATLAB MCP evaluate_matlab_code | PASS | PASS |

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

- MATLAB MCP **v0.14.0** is pinned in `.tools/matlab-mcp-server/`.
  Its release asset SHA-256 is `6697a8962f148628f11d93b36960235871de5614905d6a27c55341c2b83f4118` and matched the
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
| Requested reasoning effort | PASS | Child runtime effort `medium`; parent high, child medium |
| Requested sandbox default | FAIL | Requested `read-only`; observed `workspace-write` |
| Per-agent disabled skill | PASS | Active discovery control lists `m0-scope-canary` in parent catalog and excludes it from child catalog |
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

Gemini CLI 0.38.2 and an OAuth credential
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
