# P4 independent model review authorization

## Concrete review ready

The PI approved G3 in commit cb4061a, selecting idea-01 and rating the report
usable. P4 started. The seven authored model files, check specification and
generated results are ready; all 13 bounded symbolic checks passed. No
simulation or numerical protocol has been selected. See [model-review.md](model-review.md)
for the current artifact packet.

## Why another permission is needed

Automatic approval review rejected the isolated model_critic launch before any
process started. Its stated reason was that the earlier external-review approval
covered the bounded P3 audit, not the new unpublished P4 model payload. The
required independent P4 critique remains incomplete; G4 is not requested.
The lab-orchestrator skill requires a separate read-only root because a role
TOML alone does not enforce child permissions under the observed parent session.

## Requested bounded action

Authorize an independent artifact-only model_critic review using the existing
authenticated OpenAI Codex account. This sends unpublished local model text to
that provider in a separate session. It does not send credentials, author
reasoning, provenance summaries, unrelated files or PDFs.

The prepared payload contains **21 text artifacts**:

- Eight model artifacts: model-spec.tex, notation.yaml, assumptions.yaml,
  predictions.yaml, algorithm.md, checks.yaml, check-results.json and source-map.md.
- Three approved scope/profile files: scope.yaml, scope.md and profile.yaml.
- Six grounded literature cards already used in P2/P3.
- The model-critique skill, telecom checklist, wireless conventions and finding schema.

It also includes **35 cited cached pages from the six published manuscripts**,
as extracted text. Exact paths and SHA256 values are in
`ara/staging/P4-review-payload.json`; the prepared payload is stored locally under
`.cache/p4-model-review/9f8e5fb9fc5a489292ade485e2e86fc0/inline-packet.json`.
It has not been transmitted.

Use up to three critique rounds, limited to these artifact types and revisions
within the approved idea-01 scope. The reviewer sees final artifacts and grounded
sources only; no author reasoning or earlier critique is included. No live web
search, downloads, code execution, filesystem tools or mutation tools are allowed
for the reviewer. The delegation root is read-only, no-daemon, approval never,
with one named model_critic at depth one. The parent verifies effective runtime
permissions, unchanged inputs and actual child handoff before accepting a review.

This permission does not approve G4, alter assumptions, choose a protocol or
authorize simulation. G4 remains a later PI decision after critique and fixes.

## Current limitation

The parent's algebra/schema checks are complete but are not an independent
scientific critique. No critique verdict, unresolved-finding count or G4 readiness
is asserted until an actual review is accepted.
