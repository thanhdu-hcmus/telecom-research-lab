# Telecom Research Lab

A private framework for telecom literature, ideas, models, reproducible Python
and MATLAB simulations, independent verification and IEEE manuscripts.

The PI authorized the software build through M10. Scientific gates G1-G7 require
separate PI decisions; this repository contains no approved original research.
M10's final manual acceptance is one Overleaf compilation confirmation.

```powershell
uv sync --locked --dev
uv run lab --help
uv run lab doctor --full --json
uv run lab project init my-project
```

- [User guide](docs/user-guide.md): commands, artifact contracts and PI gates.
- [Acceptance report](docs/acceptance-m5-m10.md): actual checks, failures and limits.
- [Implementation state](implementation-state.json): milestone and gate status.
- [Build authorization](docs/build-authorizations.md): approved scope.
- [Environment report](docs/environment-report.md): host and sandbox behavior.
- [Evaluation runtime](docs/evaluation-runtime.md): audited independent reviewers.

Python dependencies are locked in `uv.lock`. MATLAB R2021b and portable TeX Live
2026 are configured for the current workstation; adjust paths for another host.
PDFs and large results default to `../ResearchLibrary`, outside Git. Optional
Gemini, scholarly API keys, SJR data and a DL workstation remain configurable.

Before real ideation, the PI must complete `config/thesis-profile.yaml` and review
target venues. Start with scope approval G1, then follow the phase commands.
M11's integrated research dry run and M12's real study require PI participation.

## Development acceptance

```powershell
uv run python scripts/verify_milestone.py
uv run python scripts/run_matlab_physics.py
uv run python scripts/roundtrip_matlab.py
uv run python scripts/smoke_m8_m10.py
```

The last command creates an isolated synthetic software fixture and the local
handoff `to_human/framework-overleaf-smoke.zip`. It grants no scientific approval.
Agent evaluations use actual Codex children; acceptance requires two of three
trials and a verified read-only runtime. Failed trials are retained.
