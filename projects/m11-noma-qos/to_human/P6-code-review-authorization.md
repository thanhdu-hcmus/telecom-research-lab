# P6 independent source review authorization

G5 approval is recorded and P6 phase start passed. The native verifier remains
pinned and the additional checker is under `analysis/supplement/`. Review this
bounded [local packet](../analysis/P6-code-review-packet.json) and its
[file/hash inventory](../analysis/P6-code-review-payload.json).

Local isolated tests: **37 PASS**, with
0 failures and 0 errors.
The canonical dataset has not been independently verified.

## Exact proposed scope

Send the listed source artifacts and 24 illustrative raw rows to a separate
authenticated OpenAI Codex session using the existing account. The review root
will be read-only with approval disabled and MCP disabled. It will spawn one
fresh named results_verifier, given artifacts only, with no tools or writes.
Actual runtime permissions, source hashes and reviewer tool calls must be audited.
The proposed authorization covers up to three bounded source-review rounds and
routine fixes only within analysis/. Numerical-result review will have its own
concrete packet after execution.

Packet size: **277,412 bytes**.
SHA256: `4c0991c42bac89a188c460cd8433709b86ce8443c654ead71512a54c41ab0111`.
Full raw CSV, PDFs, credentials, author reasoning and previous reviews are excluded.

## Why approval is needed

Automatic approval review rejected creating the external review helper because
the general continuation instruction did not specifically authorize this private
payload and destination. The repository AGENTS.md and lab-orchestrator skill
require an enforced independent review. Local implementation and isolated tests
can proceed while this approval is pending.

## Included source files

- `model/model-spec.tex`
- `model/notation.yaml`
- `model/assumptions.yaml`
- `model/predictions.yaml`
- `sim/protocol.md`
- `sim/protocol.yaml`
- `sim/protocol-errata.md`
- `sim/cases.yaml`
- `sim/lock.json`
- `sim/src/verifier.py`
- `sim/src/oracle.py`
- `analysis/supplement/benchmark_synthetic.py`
- `analysis/supplement/checker.py`
- `analysis/supplement/independent.py`
- `analysis/supplement/replay.py`
- `analysis/supplement/run_unit_tests.py`
- `analysis/supplement/test_supplement.py`
- `@repo/lab/verification.py`
- `@repo/schemas/verification_item.schema.json`

This packet requests a source review before the full canonical verifier run.
It is not a numerical result, an independent verdict or G6 scientific approval.
