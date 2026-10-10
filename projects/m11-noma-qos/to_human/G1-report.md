# G1 — m11-noma-qos

## Summary

Scientific decision pending PI review.

## Artifacts

- `projects/m11-noma-qos/profile.yaml` — SHA256 `dc4bdf213a81a65c2fab5ab99d5a455130e99c647422e666672fab5b33a8a79d`
- `projects/m11-noma-qos/scope.md` — SHA256 `d58c04fcf064de9299c77d73cab651075e43805c5d912107accf53f9b39d1625`
- `projects/m11-noma-qos/scope.yaml` — SHA256 `a63f32a19a41064fee5436b6d2d07a2c233285f238175c67b0ac9b760fca66b1`

## Automated checks

| Check | Result | Details |
|---|---|---|
| scope.md | PASS | required artifact |
| scope.yaml | PASS | required artifact |
| research-log.md | PASS | required artifact |
| findings.md | PASS | required artifact |
| runtime-validation | FAIL | PI must review the thesis profile and scope |
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
