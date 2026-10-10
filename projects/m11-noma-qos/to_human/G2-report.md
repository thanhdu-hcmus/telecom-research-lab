# G2 — m11-noma-qos

## Summary

Scientific decision pending PI review.
PI spot-check sample: r_arxiv_1504_07751_536e29b9bda8.yaml, r_doi_10_1109_icc_2018_8422366_80611aa7eda1.yaml, r_doi_10_1109_tvt_2017_2689000_33a4e1b77753.yaml, r_doi_10_1109_comst_2016_2621116_2ef25c3820bc.yaml, r_doi_10_1109_jsac_2017_2725618_92eae3178c8b.yaml

## Artifacts

- `projects/m11-noma-qos/baselines/candidates.yaml` — SHA256 `6390a2fbe1bf15b601c5fc5c5ab068703b0b44dda149e852f6539a61807d9083`
- `projects/m11-noma-qos/literature/candidates.jsonl` — SHA256 `4a1c0882cc414a7ce71ad8b13a2d3e21634f7ec1ea2dcb5682be41e44dd9a055`
- `projects/m11-noma-qos/literature/cards/r_arxiv_1504_07751_536e29b9bda8.yaml` — SHA256 `d4858de6d8453e9ffabcb485a0f9814d9b912c680981ded60a5e2327ec915432`
- `projects/m11-noma-qos/literature/cards/r_doi_10_1109_comst_2016_2621116_2ef25c3820bc.yaml` — SHA256 `42cd35cc4c8baae09c8c119b1310aca56e60c73f5cbe1c42072842febb06383f`
- `projects/m11-noma-qos/literature/cards/r_doi_10_1109_icc_2018_8422366_80611aa7eda1.yaml` — SHA256 `24fcbd52fa7b145c32705e3006063eb4286aa7a82c10b6c8874a94324881a2a2`
- `projects/m11-noma-qos/literature/cards/r_doi_10_1109_jsac_2017_2725618_92eae3178c8b.yaml` — SHA256 `e7e461610f9ad1326ae53bd6701a01491d50e8d351f8a9b62c5b88a8c4a40a07`
- `projects/m11-noma-qos/literature/cards/r_doi_10_1109_tvt_2017_2689000_33a4e1b77753.yaml` — SHA256 `1d17cbd898c5b477dff7420190e2f0b51b6a6e41d693a249e4c87e9f38da181b`
- `projects/m11-noma-qos/literature/cards/r_doi_10_48550_arxiv_1412_2799_1f2a4bca8547.yaml` — SHA256 `ec0c5ae2bfc24e4b77f16c3c8a0a9ad6619b9eff8ac2bc95a6d9290ded7efe94`
- `projects/m11-noma-qos/literature/coverage.md` — SHA256 `f413414d691e3bd082c36171bc39f289365d80dedc35dae11dcc2dfa18160362`
- `projects/m11-noma-qos/literature/gap-matrix.csv` — SHA256 `5a586ecb784cadd60398a1439b05c155f10538789d7986b9dc039732e1c6790d`
- `projects/m11-noma-qos/literature/gaps.md` — SHA256 `04b649fddf1683efb15e8a149e2ae11517262c3765232efaaa23dcdaa161952e`
- `projects/m11-noma-qos/literature/library.jsonl` — SHA256 `f9de5cd8bbe465044749cf14d8a2a991effd8363372fa737bfe812669bf68369`
- `projects/m11-noma-qos/literature/prisma.json` — SHA256 `4daf5e05b00db0aa234db9c43128a9d80fca51cbbb85d250b1ebd9c1030d5f99`
- `projects/m11-noma-qos/literature/query-plan.yaml` — SHA256 `af18d89b0e90363aecc3215c3b23cf128295e07dcf97ee3175d171b180ef8317`
- `projects/m11-noma-qos/literature/retrieval-report.json` — SHA256 `169ec4f00705b46c98b7164101d65ce0a5fc7f5ae47cb709e51f22fee1047d7f`
- `projects/m11-noma-qos/literature/screening.csv` — SHA256 `12867728e76bca12c6d9e2ff5150cd7fcd25f9b1f511a9c9519de78d3bb14a47`
- `projects/m11-noma-qos/literature/screening.yaml` — SHA256 `f4e12ea7a32858365e08471db4ef5374fbc58b9e7486f0b8598d2370f5cc3539`
- `projects/m11-noma-qos/literature/search-records.jsonl` — SHA256 `c323bbae077046d4b8308fa73e0f563ff3cd0eafb87945f6129787c564e6207b`
- `projects/m11-noma-qos/literature/search-report.json` — SHA256 `b4f4248607433c87ed5350489d3ae9972422fa55d41a6141ec736cfc6ab2a923`
- `projects/m11-noma-qos/literature/survey.md` — SHA256 `8d82ac2733c32c4c0b883901bba1565d00e0bc0a1ac6914b3d2f66bb44a8563d`

## Automated checks

| Check | Result | Details |
|---|---|---|
| literature/query-plan.yaml | PASS | required artifact |
| literature/candidates.jsonl | PASS | required artifact |
| literature/screening.yaml | PASS | required artifact |
| literature/gap-matrix.csv | PASS | required artifact |
| literature/gaps.md | PASS | required artifact |
| literature/survey.md | PASS | required artifact |
| baselines/candidates.yaml | PASS | required artifact |
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

`lab gate approve G2 --project m11-noma-qos --note "..."`

Alternatively use gate revise or rewind.

## Prepared P2 handoff

See [G2 review packet](G2-review.md) and [sampled source links](G2-spot-check.md).
Six included full papers, 122 screened candidates, four benchmark validation questions.
No novelty, measured M11 result or accepted baseline is claimed.
Actual named-specialist effort and negative outcomes: `ara/staging/P2-orchestrator-review.md`.
Validation: `ara/staging/P2-validation.json`. Format/archive receipt: `P2-normalization.json`.
