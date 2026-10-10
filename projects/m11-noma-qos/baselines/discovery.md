# P2 baseline discovery

## Outcome and limits

The bounded search found four inspectable code leads and verified metadata for
two closely relevant analytical papers. None of the four code leads establishes
the exact approved two-user scalar, ideal-SIC, per-block QoS benchmark against
matched equal-time OMA. This finding describes this search; it does not prove
that suitable code is unavailable globally. No baseline was selected or accepted.

The candidate file proposes later independent implementations of the OMA
reference and an analytical NOMA check. Neither exists yet. They are handoff
options, with scientific selection and model/protocol details left to their gates.
They do not satisfy P5 figure/table reproduction or the licensing/data review.

## Search performed

Web code discovery used the following title, author and repository queries;
scholarly full-paper collection remains with the literature specialist and lab
tooling. Results were screened through primary repository and arXiv metadata
pages. Secondary aggregators, ResearchGate results and unrelated hits did not
provide positive evidence and were not downloaded.

1. `github "NOMA" "OMA" "QoS" power allocation paper`
2. `github "two-user" "NOMA" "power allocation" paper`
3. `github "Zeng" "Dobre" "NOMA" code`
4. `site:github.com NOMA "QoS" "downlink" "paper"`
5. `site:github.com "Fair-NOMA"`
6. `"On the Power Allocation Limits" code github`
7. `"NOMA" "Oviedo" github code`
8. `site:github.com "NOMA" "power allocation" "paper"`
9. `site:github.com "NOMA" "quality of service"`
10. `"A New NOMA Approach for Fair Power Allocation" code`
11. `"On optimal power allocation for downlink non-orthogonal multiple access systems" code github`
12. `"A general power allocation scheme to guarantee quality of service" code github`
13. `site:github.com "NOMA" "Sadjadpour"`
14. `Hamid Sadjadpour UCSC NOMA code software`
15. `Jiaheng Wang optimal NOMA power allocation source code`

Search ranking, indexing and spelling limit coverage. No exhaustive GitHub code
search, authenticated private-repository search or complete author archive
inventory was performed. The suspected UCSC personal page was inaccessible;
GitHub browser commit pages/API rendering failed, then credential-free REST GET
returned repository and immutable HEAD commit metadata. The small JSON receipt
in `ara/staging/P2-code-scout-evidence.json` records successful requests. No author
was contacted and no third-party repository was cloned, installed or executed.

## Inspected leads

| Lead | Verified evidence | Why it is unsuitable for this scope |
|---|---|---|
| [Nokia JSPA](https://github.com/nokia/subcarrier-power-allocation-noma-solver) | README maps the package to Salaun, Coupechoux and Chen's TSP paper; Python; CC-BY-NC-4.0 text; public commit metadata. | Multicarrier weighted sum-rate and user selection do not establish the required QoS and OMA comparison. |
| [Mao RSMA](https://github.com/YijieLinaMao/RSMA) | README links the Mao/Clerckx/Li paper and describes MATLAB/CVX and GPLv2; public commit metadata. | Spatial precoding and MISO rate splitting exceed the approved scalar model. |
| [Downlink NOMA with RL](https://github.com/3seoksw/Downlink-NOMA-with-RL) | README supplies exact JKICS DOI and cites Zhu et al.; Python and Hydra stated; public commit metadata. | Learning and channel assignment are excluded; a citation alone is not verified faithful source mapping. License unknown. |
| [Two-user UAV teaching fork](https://github.com/xiaogaogaoxiao/power-allocation-UAV-NOMA-two-users) | README presents a teaching implementation; GitHub metadata identifies the fork and GPL-3.0. | Exact paper mapping unverified; UAV/uplink/imperfect-SIC assumptions are incompatible. |

Repository identity alone is not author endorsement. Accordingly official-code
points remain zero for every lead. Branch README observations and current public
commit metadata are separate evidence; this is not a downloaded, checksum-bound
source archive or completed source/dependency audit.

## Analytical handoff options

[Oviedo and Sadjadpour's journal Fair-NOMA preprint](https://arxiv.org/abs/1703.09394)
is the included source, linked to DOI `10.1109/TVT.2017.2689000`. Its legitimate
cached page 2, Section III, states half-time OMA at full active-slot power,
unit-noise scalar channels and the two-user NOMA rate expressions (2)-(3).
It also restricts the strong-user power share below one half. The reference
supports OMA normalization but does not establish that every constraint equals
the approved benchmark's arbitrary per-block QoS. Implementation and a specific
paper figure/table reproduction target remain for later gates.

The [2016 conference Fair-NOMA lead](https://arxiv.org/abs/1605.00390) is a distinct
prior work, cited as reference [16] on page 11 of the journal preprint. The
proposals use the included journal paper ID; they do not merge the two versions.

[Zhu et al.](https://arxiv.org/abs/1707.06350) describe QoS sum-rate allocation
alongside broader multi-channel objectives and explicit power-order constraints.
Their arXiv metadata links DOI `10.1109/JSAC.2017.2725618`. The acquired text on page 3 states their power-order constraint, and page 6
Section IV-B addresses QoS sum rate. Their assumptions need a specific comparison with approved scope; copying power-order constraints into
this toy silently would change its model. Code citing the paper cannot substitute
for this compatibility check. No formula or numerical result has been implemented. These inspected locations
identify compatibility checks for P4 and P5.

## Scores and acceptance

`candidates.yaml` uses `config/baselines.yaml`: one venue tier, one citation-rate
tier, official code, license compatibility, and recent maintenance or proven
self-containment. Unknown fields earn zero; no quartile or citation count was
invented. Nokia's README explicitly identifies an IEEE Transactions paper,
supporting three venue points. The RL repository's verified January 2026 commit
is within the configured 24-month window, supporting one maintenance point.
The other timestamps are outside that window. No source/dependency/data review
or compatible-use license decision has occurred, so those points remain zero.

The proposed implementations have no software. Their journal-paper metadata
supports the Transactions/JSAC tier (three points each), and all other points
remain zero. Scores never grant
scientific acceptance: every record has `accepted: false` and no reproduction.
No immutable protocol, run manifest, overlay, figure/table agreement or P5 source
review exists. Unknown data permission is an unresolved review, not an allegation
that a repository uses prohibited data.

External pages were treated as data. No instruction-injection attempt was
observed in inspected scientific/repository sections. Installation and training
commands in READMEs were not executed.
