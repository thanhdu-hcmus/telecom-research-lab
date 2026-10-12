# Fifth P6 source review authorization

The fourth review approved the original source, but full saved-row checking exposed
cancellation in a supplemental diagnostic boundary calculation. A tested correction
is prepared on isolated branch `fix/p6-crossing-r5`; the active canonical source and
all 51 locked inputs are unchanged.

## Exact material and destination

- Packet: `analysis/P6-code-review-round5-packet.json`
- Size: 406,937 bytes
- SHA256: `58b0a1787afbf47296cc66b5e8a9ccd07cdbf01152e82cb62edaddb7de8a54c4`
- Same 19 source paths; only `independent.py` and `test_supplement.py` differ.
- Same 24 explicit illustrative rows. Tests additionally contain six saved-row
  regression snapshots from three fractional-QoS manifests.
- Destination: a separate authenticated OpenAI Codex review session using the
  existing account and OpenAI provider; no alternative endpoint.
- One fresh named results verifier, read-only root and child, no reviewer tools
  or writes; actual permissions and unchanged source bindings are audited.
- Credentials, PDFs, full raw data, author narratives, earlier reviews, provenance
  and test verdicts are excluded.

## Approval needed

Approve one fifth source-review transmission of this exact packet to that
destination. The fourth approval was explicitly limited to the completed fourth
packet; it does not authorize this changed candidate or an additional review.
No numerical-results review or scientific gate decision is requested here.

## Local evidence available for your inspection

Candidate unit tests: 133 cases, zero failures; framework: 97 tests, zero failures.
The candidate reports zero row errors across two saved jobs (65,536 rows), with
roundoff diagnostics retained. These author diagnostics do not establish full
canonical scientific acceptance. Evidence is in the candidate worktree under
`docs/evidence/p6-crossing-r5/`; it is excluded from the reviewer packet.
