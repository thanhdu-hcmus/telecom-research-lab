# G4 — m11-noma-qos

## Summary

Scientific decision pending PI review.

## Artifacts

- `projects/m11-noma-qos/model/algorithm.md` — SHA256 `ed193d86f630202a40fa9ee9fa37ede07da4a76fb2cb4e053f03fa74a98013e0`
- `projects/m11-noma-qos/model/assumptions.yaml` — SHA256 `48689bf9d889c0b4d4ccc9c7abe4f484cc41fde5ac27ddc4e5ea6e399ec16b4a`
- `projects/m11-noma-qos/model/check-results.json` — SHA256 `71ee6408378ac0238dcd0c85e2b9671e335972b4103cef1dcf9e0b3aa744207e`
- `projects/m11-noma-qos/model/checks.yaml` — SHA256 `51b14ababb3339b7871cf5be146ce9a320c2b486cc1c6a6148886a6804732bfb`
- `projects/m11-noma-qos/model/critique.yaml` — SHA256 `26998fdd143b5995c0f2e25cb555ada7b0a249f72178b98d24edc0da99ed586e`
- `projects/m11-noma-qos/model/model-spec.tex` — SHA256 `c885769e4d0d191bd82e11891de912340a7baa64af49d9b8c4584b4a3204f76e`
- `projects/m11-noma-qos/model/notation.yaml` — SHA256 `2e937f7f98e3240f476471c44cc2756afdfe77079aa8f5845cfe1bcfe920de22`
- `projects/m11-noma-qos/model/predictions.yaml` — SHA256 `b18859e62c3a5306b9b341331b5acd7e7ec5fb93b5fbc3cf82032fb8959a6fd2`
- `projects/m11-noma-qos/model/response.md` — SHA256 `581a57c877e6da76f9665b74f000a20c7cfc5b0ff6e182bc5d6df650245e86a9`
- `projects/m11-noma-qos/model/source-map.md` — SHA256 `88469e412cb23526941c2cda86efb3bca9be2f5f097d09ad021ddd54f6026d1d`

## Automated checks

| Check | Result | Details |
|---|---|---|
| model/model-spec.tex | PASS | required artifact |
| model/notation.yaml | PASS | required artifact |
| model/assumptions.yaml | PASS | required artifact |
| model/predictions.yaml | PASS | required artifact |
| model/critique.yaml | PASS | required artifact |
| model/response.md | PASS | required artifact |
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

`lab gate approve G4 --project m11-noma-qos --note "..."`

Alternatively use gate revise or rewind.
