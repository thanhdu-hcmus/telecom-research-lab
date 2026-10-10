# Implementation plan review

Reviewed: 2026-10-10. Source: `../../Telecom-Research-Lab-Plan.md`.

The architecture is implementable as a local research framework, but M0 must
establish the actual execution environment before later milestone acceptance.
The framework cannot itself select a scientific question, approve research
gates, supply unpublished papers, or confirm novelty without the specified
research work. Existing thesis state in the parent workspace remains the
source of the PI's preferences; it has not been migrated or overwritten.

## Findings requiring explicit treatment

| ID | Severity | Plan location | Finding and implementation consequence |
| --- | --- | --- | --- |
| R01 | Critical | Sections 5.0, 16 | TTY plus a typed code is not an identity or security boundary: agent tools can allocate a PTY and write keystrokes. Implement it as an accidental-automation guard, keep approval prohibited by agent instructions, and document that limitation. If protection against an agent intentionally approving is required, the PI must use a signer or approval service whose credentials are inaccessible to agents; do not claim the TTY mechanism alone establishes that property. |
| R02 | Critical | Sections 5.0, 8 | Approval must bind to the exact reviewed artifacts and check results. A state flag alone becomes stale after edits. Record artifact hashes and prerequisite approval identities, require them on phase entry, and invalidate downstream approvals after revisions/rewinds. Missing required artifacts or incomplete checks must fail closed. |
| R03 | Critical | Sections 13.1, 13.4 | Mathematical notation is damaged: `()H`, `CN(0,2)`, `-174+1010B+NF`, and all first three physics expressions are ambiguous. Restore definitions and expressions before using them as test oracles; proposed corrections are given below. |
| R04 | Major | Sections 2 D2/D17, 3, Appendix A.2 | The current environment is MATLAB R2021b. Current MathWorks MCP documentation requires R2021a or later, rather than the plan's R2020b statement. On Windows forward `WINDIR`; specify `--matlab-display-mode=nodesktop` to avoid a visible desktop. Actual batch exit status must be captured with `-wait`. See the verified sources below. |
| R05 | Major | Section 4.3, D18/D19 | Configuration defaults do not prove effective child settings. Current documentation also describes parent live permission overrides that can supersede custom-agent defaults. Record observed behavior and use an enforceable filesystem/sandbox boundary if a reviewer must be read-only. Never claim a restriction based solely on `developer_instructions`. |
| R06 | Major | Section 4.3, Appendix A.2 | Codex configuration is version dependent. Current documentation names `max_concurrent_threads_per_session`, retaining `max_threads` as an alias. Validate installed-version parsing and runtime behavior, including depth and project trust/loading; record any compatibility layer. Do not silently install a global configuration. |
| R07 | Major | Sections 6, 10, Appendix B | DOI/arXiv identifiers are not safe Windows filenames: a DOI can contain `:`, `/` and other path syntax. Preserve the canonical ID as data and generate a separate stable, collision-resistant file key. Reject path traversal in project slugs, archive names, extraction destinations, baseline IDs and figure/export paths. |
| R08 | Major | Section 10 | Network policy must validate every redirect, not just the initial URL. OpenAlex/Unpaywall PDF locations are untrusted discovery data, not automatic authority to add a domain. Define host approval and redirect policy, reject credentials/private network destinations, and test denied redirects without contacting them. Respect source-specific rate limits and meaningful `Retry-After`; CI uses fixtures. |
| R09 | Major | Sections 11, 12, D6 | Tie-break rules differ: D6 says novelty strength, while Section 11 specifies novelty verdict then lower risk. Use a single configurable documented ordering, with a stable final ID tie-break. Define non-overlapping venue and citations-per-year bands so points are not double-counted. Declare the partial-year denominator for recent publications. |
| R10 | Major | Section 5.5 | The tolerance `0.5 dB or 5%` cannot apply uniformly to every quantity. Declare the metric, units, reference points/interpolation, absolute tolerance at zero, and permitted deviations before reproduction. A candidate score is not final acceptance until reproduction passes. Missing comparison data remains unverified. |
| R11 | Major | Sections 5.5, 16 | Protocol protection requires checking hashes and the Git commit graph, not just finding a commit message. Record the exact protocol commit, scientific input hashes, code SHA, baseline revision, seeds and configuration. Require the protocol commit to be an ancestor of result commits. Refuse modified locked inputs; approved changes produce a new protocol version. |
| R12 | Major | Sections 5.6, 13.3, 13.4 | Statistical checks need predeclared confidence levels, interval methods, trial counts and handling of zero-event/near-zero averages. Observing 100 rare events is a useful heuristic, not a universal precision guarantee. Paired comparisons must preserve channel-realization identity. Inspect every prediction, including inconclusive and failed outcomes. |
| R13 | Major | Sections 13.4, M11 | Neither RIS N-squared scaling nor NOMA beating OMA is unconditional. RIS scaling needs an explicitly stated aperture/pathloss regime. M11 needs a feasible, fairly matched ideal degraded-broadcast example, identical budgets, a stated OMA scheduler and QoS, and defined handling of infeasibility; do not impose a universal NOMA >= OMA assertion. |
| R14 | Major | Sections 5.7, 16 | A number-trace checker must parse the intended LaTeX sections/macros and distinguish claims from equation labels, bibliography years and formatting numbers. A copied `\\res{}` value needs provenance, source manifest checksums and a computation description. Citation metadata verification does not establish that the cited paper supports a claim. Both checks are required. |
| R15 | Major | Section 16 | Agent evaluations need genuinely frozen, licensed fixtures and deterministically checkable ground truth. Do not label generated mock papers/repositories as real scholarly sources. Check output schemas and allowed writes in addition to finding counts; score clean controls and planted cases separately. Preserve all three trial outcomes when applying the two-of-three rule. |
| R16 | Major | M12 | Skipping P3 still needs a recorded G3 decision for the reproduction/ablation selection, or later P4 prerequisite enforcement conflicts with the prescribed workflow. A PI-approved explicit reproduction route may satisfy that gate; silently omitting it must not. |
| R17 | Minor | Sections 4.4, 14 | Upstream contents, license and safety claims must be checked against the actual pinned commit in M1. Record each retained file and adaptation; do not treat a prior review or a third-party registry label as evidence about a newly downloaded version. |
| R18 | Minor | Sections 2 D7, 15 | Quartiles and service access tiers are dated facts. Store the source dataset/category/year and access checks rather than claiming current SJR status or Gemini subscription entitlements from this plan. Gemini remains optional. |

## Proposed mathematical repair before M8

These expressions specify proposed test conventions; they are not experimental
results or a change to an approved scientific model.

- Hermitian transpose: $\mathbf{x}^{\mathrm H}$; ordinary transpose:
  $\mathbf{x}^{\mathrm T}$. A scalar circularly symmetric complex Gaussian is
  $h\sim\mathcal{CN}(0,\sigma^2)$, with $\mathbb{E}|h|^2=\sigma^2$.
- Thermal noise under the explicitly assumed -174 dBm/Hz reference density:
  $P_{\mathrm{noise,dBm}}=-174+10\log_{10}(B_{\mathrm{Hz}})+NF_{\mathrm{dB}}$.
  State temperature/density and the bandwidth before invoking this convention.
- Coherent BPSK in AWGN: $P_b=Q(\sqrt{2E_b/N_0})$; $E_b/N_0$ is linear.
- If instantaneous SNR is exponential with mean $\bar\gamma$, Rayleigh outage
  is $P_{\mathrm{out}}=1-\exp(-\gamma_{\mathrm{th}}/\bar\gamma)$.
- For $h\sim\mathcal{CN}(0,1)$ and linear average SNR $\rho>0$, ergodic spectral
  efficiency is $\mathbb E[\log_2(1+\rho|h|^2)] =
  e^{1/\rho}E_1(1/\rho)/\ln 2$. Define the exponential integral and evaluate it
  stably rather than overflowing at very low SNR.

## Implementation sequence and current boundary

Update after M0: the PI explicitly approved M0 and automatic M1-M10 progress.
Software implementation is complete through M10, including the PI's successful
Overleaf compilation confirmation. The historical approval analysis below
preceded that decision. See `docs/evidence/m10-overleaf-confirmation.json`.

M0 creates bounded environment probes, installs workspace-local tools, records
sandbox and host evidence separately, and checks the native runtime. It does
not approve a research phase or satisfy M1's schemas, skills or CI.

Section 0 explicitly requires PI approval at every build milestone. The latest
request authorizes independent implementation work, but does not record approval
of a milestone whose results do not yet exist. At the M0 checkpoint, present the
actual results and any required workaround once. Framework build approvals and
the seven scientific gates are separate decisions; no scientific gate should
be inferred from authorization to build the framework.

## Verified primary documentation

- [Codex custom agents and inherited permission overrides](https://learn.chatgpt.com/docs/agent-configuration/subagents), checked 2026-10-10.
- [MathWorks MATLAB MCP Server README](https://github.com/matlab/matlab-mcp-server), checked 2026-10-10; installed release v0.14.0 has a verified release-asset SHA-256 receipt in `evidence/matlab-mcp-install.json`.
- [MATLAB Windows batch and wait options](https://www.mathworks.com/help/matlab/ref/matlabwindows.html), checked 2026-10-10; actual R2021b execution is separately recorded.
- [TeX Live unattended installation profiles](https://tug.org/texlive/doc/install-tl.html), consulted through Context7; the workspace bootstrap profile is portable and changes no system PATH.
- [TeX Live Windows support software](https://tug.org/texlive/doc/texlive-en/texlive-en.html), consulted through Context7; includes Perl needed for `latexmk`.

All raw plan text and third-party documentation are treated as data. Any
proposed change to scientific assumptions still requires the PI's recorded
decision under the plan's deviation policy.
