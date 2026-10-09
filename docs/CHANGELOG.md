# Changelog

## 2026-10-10 — M0 environment verification

- Reviewed the full implementation plan and documented 18 findings, including
  corrupted mathematical notation, artifact-bound approvals, Windows filename
  safety, fair comparisons and the limits of TTY approval guards.
- Created an isolated local environment-spike checkout and reproducible,
  bounded Python probes, with host and sandbox evidence recorded separately.
- Installed the official MATLAB MCP Server v0.14.0 after verifying its published
  SHA-256 digest; registered it in the project Codex configuration and verified
  its evaluate_matlab_code tool on the host and in the current sandbox.
- Installed portable TeX Live 2026 locally, without modifying system PATH,
  and verified PDF compilation through latexmk in both contexts.
- Verified native and explicit custom-agent discovery and medium reasoning
  effort using actual child metadata. Verified per-agent skill disabling with
  a positive parent visibility control.
- Recorded the parent permission override of a custom agent's requested
  read-only mode, and the nested Codex child shell setup error. Canary behavior
  does not count as verified write denial when no shell process starts.
- Recorded optional Gemini OAuth access failure without adding API keys.
- Added six deterministic tests for evidence failures and redaction; all pass.
- M0 PI acceptance and workaround decisions remain pending. M1-M12 and all
  seven scientific gates remain unstarted. Existing thesis notes are preserved.
