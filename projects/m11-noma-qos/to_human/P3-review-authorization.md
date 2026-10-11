# Permission needed for the independent P3 audit

## Current work

M0-M10 are complete. G1 and G2 are approved. P3 has 15 draft benchmark options
in `ideas/idea-01.yaml` through `ideas/idea-15.yaml`; their overview is
`ideas/design-options.md`. Local checks found all 15 schema-valid, all cited
closest-work and venue-context IDs included in the approved six-paper corpus,
UTF-8 LF text, and unchanged G1/G2 artifact hashes. Novelty is still `unclear`.
No ranking, G3 request, model, simulation or scientific selection has been made.

## Proposed action

Launch the named `novelty_auditor` through the existing authenticated OpenAI
Codex CLI in a separate read-only session. It will compare the drafts with the
published evidence and perform at least five targeted searches per option.
The parent will save the returned reports and audit the effective permissions.

The finite research packet contains:

- The 15 M11 draft idea cards.
- M11 approved scope and its synthetic benchmark profile.
- M11 research-state and findings for phase context.
- The six grounded literature cards, their explicitly cited cached published
  paper text, candidate metadata, survey, gaps, comparison matrix and coverage.
- Reviewer instructions, the novelty-audit skill, schemas and bounded search
  adapter configuration.

Local research text in that packet will be processed by OpenAI through the
authenticated Codex reviewer. Public discovery queries may reach the live web
  search service and scholarly/author/code pages. Credentials and unrelated
  research files are excluded. The review does not authorize gate approval,
  simulations, publication or sending messages to other people.

## Why approval is needed

Automatic approval review rejected the attempted launch because it could export
unpublished local research artifacts to another service without explicit approval
for the payload and destination. The rejection happened before execution; this
review session has not been launched. It has not been retried or bypassed.

Approval is requested only for this bounded external audit. After it finishes,
the eligible options can be ranked for the separate PI choice at G3.
