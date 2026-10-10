# G1 — m11-noma-qos

## Summary

Scientific decision pending PI review.

## Artifacts

- `projects/m11-noma-qos/profile.yaml` — SHA256 `25f0f8ea5908d46c6564ba4c667aa576b867da6e3f72a3918bc595efd49c4cab`
- `projects/m11-noma-qos/scope.md` — SHA256 `d58c04fcf064de9299c77d73cab651075e43805c5d912107accf53f9b39d1625`
- `projects/m11-noma-qos/scope.yaml` — SHA256 `c5c3a637d6a1a374b8b760935958414a68c8d32c648c030c573f8f94b5945df4`

## Automated checks

| Check | Result | Details |
|---|---|---|
| scope.md | PASS | required artifact |
| scope.yaml | PASS | required artifact |
| research-log.md | PASS | required artifact |
| findings.md | PASS | required artifact |
| runtime-validation | PASS | schemas and phase invariants |
| deviations | PASS | [] |

## Findings and deviations

Review phase artifacts, unresolved issues and deviations.yaml.

## Untrusted-content alerts

Review alerts recorded by specialists; absence of a report is not a scan guarantee.

## Provenance and effort

See ara/trace/sessions; run provenance-epilogue before decision.

## PI checklist

- [ ] Scope and assumptions accepted
- [ ] Evidence spot-checked
- [ ] Deviations resolved
- [ ] Provenance reviewed

## Decide

`lab gate approve G1 --project m11-noma-qos --note "..."`

Alternatively use gate revise or rewind.
