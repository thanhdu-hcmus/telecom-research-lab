# P2 handoff review

All three named author specialists (`lit_scout`, `paper_analyst`, `code_scout`)
were spawned under the parent workspace-write session, at depth one, from
file-based briefs in this folder. These are author handoffs, not enforced
read-only independent scientific reviews. No further subagents were spawned.
Git operations and PI decisions remained with the orchestrator/PI respectively.

The parent read all six cards, all 122 title-level screening reasons, query and
coverage records, the synthesis/matrix, acquisition failures and baseline records.
Source checks used page-delimited untrusted extraction text:

| Source | Parent-inspected pages or focused passages | Checked interpretation |
|---|---|---|
| Xu, arXiv 1504.07751 | 1–2 | Rate-region assumptions and fixed-power loss event |
| Fair-NOMA, TVT DOI | 2–3 | Half-time OMA at full active-slot power, fairness interval, extra power order |
| Zhu, JSAC DOI | 3, 6–7, 11 | QoS objective, extra constraints, conditional boundary solution, OFDMA definition |
| Ding, arXiv 1412.2799 | 2, 4 (focused passages) | Fixed-power loss study versus primary-only CR comparison |
| QoS limits, ICC DOI | 3–4 (focused passages) | Necessary-bound caveat and outage-event/capacity distinction |
| Historical survey, ComST DOI | 8, 34, 36 (focused passages) | Perfect-SIC rate assumption and practical overhead limits |

The parent requested and received two card corrections: Fair-NOMA's explicit
strong-user power restriction, and Xu's separation of power adaptation from
unstated CSI availability. Metadata wording was corrected to distinguish
recorded venue identity from independently reconciled final publication data.
No new scientific assumption, selection, metric or protocol was introduced.

`P2-validation.json` records actual parent validation of six cards, 127 page
references with cache/PDF identity and nonempty pages, six baseline score previews,
unchanged G1 binding and all P2 runtime checks. `P2-repository-check.json` independently
checks four public immutable rejected-code commit records through lab Network.
These automated checks establish artifact consistency; they do not replace the
PI's evidence spot-check or scientific approval.

Negative outcomes retained: optional QoS paper host rejection then unusable
title-mismatched PDF; browser/API-rendering failures during code discovery; Windows
console Unicode failure and truncated broad source output, followed by successful
UTF-8 focused reads. An early parent read of nonexistent `config/literature.yaml`
was corrected to the actual source configuration. No paper was accepted from an
abstract, no identity check was bypassed, and no third-party code was executed.

External material was treated as data. No instruction injection was reported in
the inspected passages; this is not an exhaustive security scan of every byte.
No original novelty, measured M11 result, complete literature coverage or successful
paper reproduction is claimed. The exact approved scope/profile remain unchanged.

The pre-commit check found ten pending G2 snapshot hashes would differ from Git's
LF-normalized blobs. P2 text was normalized before refreshing the gate request;
scientific content and G1 binding were unchanged. Exact session 0003 evidence was
archived under the external ResearchLibrary before any update. The archive paths,
checksums and normalization mapping are in `P2-normalization.json`. A new epilogue
records the final portable snapshot; the earlier session remains append-only.
