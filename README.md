# Telecom Research Lab

Implementation of `../Telecom-Research-Lab-Plan.md`, starting at milestone M0.

The existing thesis notes stay in the parent workspace. This isolated local
checkout is the environment spike; a GitHub repository is not created at M0.

Run reproducible environment checks using Python 3.11 or later:

```powershell
python scripts/probe_environment.py --context sandbox --network --matlab --latex --output docs/evidence/environment-sandbox.json
```

Repeat the command with `--context host` and a distinct output file in a normal
host terminal to distinguish sandbox restrictions from missing tools. JSON
records contain real exit codes and explicit missing/failing capabilities.
Tool stdout is retained for diagnostics; authentication token output is redacted.

M0 probes are not research runs. No scientific gate has been approved and no
paper result has been produced. See `docs/environment-report.md` for the current
readiness and `docs/plan-review.md` for issues identified in the implementation plan.
# Telecom Research Lab

A private, project-scoped framework for gated telecom research with Codex,
Python, MATLAB R2021b and IEEEtran. The framework build is authorized through
M10; scientific phases still require PI approval at G1–G7.

```powershell
uv sync --locked --dev
uv run lab --help
uv run lab doctor --full --json
uv run pytest
```

M0 evidence and runtime limitations: [environment report](docs/environment-report.md).
Build authorization: [record](docs/build-authorizations.md).
Schemas are generated with `uv run python scripts/export_schemas.py`.
Project PDFs default to `../ResearchLibrary`, outside this Git repository.
Optional API keys, contact email, Gemini and SJR data are not required to build.
Role skills are enabled as their implementation milestones pass; an M1 contract
stub is not a working research agent.

