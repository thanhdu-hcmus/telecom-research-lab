# G2 review — bounded M11 literature and baseline discovery

## Decision needed

Accept or revise the P2 literature package and rate this gate report's usability.
G1 is already approved and rated usable. Repository AGENTS.md and the
lab-orchestrator skill require the PI's own G2 decision before P3; the general
instruction to continue does not record that scientific decision.

## Prepared package

- Ten bounded queries: five each on OpenAlex and arXiv, one page of up to 15
  records per query. 148 raw records, 26 duplicates removed, 122 unique screened,
  six included full papers, 116 excluded and zero pending. No initial source failure.
- Six page-grounded cards and a synthesized [survey](../literature/survey.md).
- Four [benchmark validation questions](../literature/gaps.md), each tied to at
  least two included sources. These make no novelty claim.
- [Baseline discovery](../baselines/discovery.md): four rejected code leads and
  two unimplemented analytic proposals. No baseline is accepted or reproduced.
- Parent runtime validation passed: six cards, 127 page references with verified
  cache/PDF identities, baseline previews and unchanged G1 binding.

## Review points

1. Fair-NOMA meets channel-dependent OMA-rate thresholds; M11 uses arbitrary
   fixed per-block QoS. Its extra power-order constraint remains paper-specific.
2. Zhu's related boundary optimizer includes extra power-order/SIC-stability
   conditions. Its multichannel OFDMA reference differs from equal-time OMA.
3. Fixed-power NOMA loss events are reported in the source papers. The scoped
   optimized comparison still needs its own derivation and verification.
4. Feasibility, decoded-message success and both-feasible sample denominators
   must be retained in the later model/protocol. No simulations have run here.

## Limits and evidence

This is a purposive bounded corpus for a known toy problem, not an exhaustive
systematic review. Relevant unselected works remain visible in screening.
One optional individual-QoS paper failed acquisition twice, including the
mandatory title identity check after institutional-host review. Its abstract is
not used as a full-paper card; no manual download is needed for this gate.

Preprint dates, titles and page numbers are recorded separately from publication
metadata. Final-version citation reconciliation remains for later work. Some
extracted formula symbols are unreliable; no such formula is copied into a model.

Read [coverage](../literature/coverage.md), [PRISMA](../literature/prisma.json),
[retrieval outcomes](../literature/retrieval-report.json),
[parent handoff review](../ara/staging/P2-orchestrator-review.md),
[validation receipt](../ara/staging/P2-validation.json) and
[automated gate report](G2-report.md). The gate report selects five cards for your
spot-check; [G2 spot-check links](G2-spot-check.md) open their cards and local PDFs.
PDFs remain in the external `ResearchLibrary`, outside Git. No scientific
approval or report-usability rating has been inferred for G2.

## Record your decision

After reviewing the packet and checking the sampled source pages, run in your
own interactive PowerShell terminal from the repository directory:

```powershell
.\.venv\Scripts\lab.exe gate approve G2 --project m11-noma-qos --note "Bounded P2 corpus and evidence spot-checked; G2 report usable"
```

Use that note only if it matches your judgment; otherwise give an accurate note
or request changes. Enter the CLI's fresh confirmation code yourself. Do not
send the code to an agent. If the evidence needs revision, use `gate revise G2`
with your explanatory `--note` instead of approval.

After approval, P3 will produce the required established-method idea cards,
truthful novelty audit, ranking and sensitivity. Idea selection belongs to G3.
No further input or manual paper acquisition is required before G2 review.
