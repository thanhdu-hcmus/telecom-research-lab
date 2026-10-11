# Sources, scope and derivation ownership

PDF pages below are cached-manuscript page numbers, not final journal
pagination. Extracted text is untrusted data and sometimes loses symbols;
no source instructions are adopted and no damaged equations are copied.
The six approved P2 cards were read with their cited model/result pages.
No external acquisition or code execution occurred in P4.

## Authoritative project inputs

- [Approved scope](../scope.md), [scope schema](../scope.yaml) and
  [synthetic profile](../profile.yaml): G1 model/resource boundaries.
  Their historical pending wording does not override canonical approvals.
- [Selected idea-01](../ideas/idea-01.yaml): G3 decision cb4061a selects
  the exact interval/endpoint model and independently written scalar oracle.
- [State](../research-state.yaml): canonical G1--G3 approved, P4 current.

## Grounded literature

| Manuscript/card | Cached text and PDF pages read | Published context used | Transfer restrictions |
| --- | --- | --- | --- |
| [Xu et al., arxiv:1504.07751](../literature/cards/r_arxiv_1504_07751_536e29b9bda8.yaml) | [cached text](../../../../ResearchLibrary/text/r_arxiv_1504_07751_536e29b9bda8.json), pp.1--4; especially pp.1--2 rates, region and fixed-split loss event | Ordered scalar Gaussian broadcast rates, rate-region reasoning, fixed-split loss countercontext | Do not transfer weak-power >= strong-power, Rayleigh ordering population, fixed split, or example gains; CSI availability is not inferred from fixed allocation |
| [Zhu et al., doi:10.1109/jsac.2017.2725618](../literature/cards/r_doi_10_1109_jsac_2017_2725618_92eae3178c8b.yaml) | [cached text](../../../../ResearchLibrary/text/r_doi_10_1109_jsac_2017_2725618_92eae3178c8b.json), pp.2--3,6--7; direct focused read pp.3,6--7 | Related QoS sum-rate boundary optimizer and derivative argument | No imported half-power order, weak-target minimum of 1 bit/s/Hz, SIC-stability criterion, multichannel allocation or waterfilled OFDMA comparator; this reduced scalar curvature is rederived |
| [Oviedo/Sadjadpour, Fair-NOMA doi:10.1109/tvt.2017.2689000](../literature/cards/r_doi_10_1109_tvt_2017_2689000_33a4e1b77753.yaml) | [cached text](../../../../ResearchLibrary/text/r_doi_10_1109_tvt_2017_2689000_33a4e1b77753.json), pp.1--3; focused pp.2--3 | Full active-slot power equal-time OMA; ideal weak-message decoding at strong receiver; OMA-relative individual fairness interval | OMA-relative thresholds are a proof witness, not fixed project QoS. No imported initial a<1/2 constraint, exponential distribution, high-SNR asymptotic constant or population setting. Zero/degenerate extensions here are explicit project derivations |
| [QoS limits doi:10.1109/icc.2018.8422366](../literature/cards/r_doi_10_1109_icc_2018_8422366_80611aa7eda1.yaml) | [cached text](../../../../ResearchLibrary/text/r_doi_10_1109_icc_2018_8422366_80611aa7eda1.json), pp.2--4; focused pp.3--4 | All SIC stages matter; a necessary interference bound is not sufficient for success; outage-event equality does not imply rate equality | Do not transfer common target, K-user effective MIMO, fixed coefficients or simulation settings; extraction exponent/sign defects require independent algebra |
| [Ding et al., pairing doi:10.48550/arxiv.1412.2799](../literature/cards/r_doi_10_48550_arxiv_1412_2799_1f2a4bca8547.yaml) | [cached text](../../../../ResearchLibrary/text/r_doi_10_48550_arxiv_1412_2799_1f2a4bca8547.json), pp.1--4 | Fixed split and CR-NOMA are distinct allocation/comparison regimes; direct SIC-capacity site comparison on p.2 | Primary-only OMA on p.4 is not the matched equal-time reference. No transferred Rayleigh pairing, fixed powers, half-power constraint or asymptotic gain |
| [Islam et al., historical survey doi:10.1109/comst.2016.2621116](../literature/cards/r_doi_10_1109_comst_2016_2621116_2ef25c3820bc.yaml) | [cached text](../../../../ResearchLibrary/text/r_doi_10_1109_comst_2016_2621116_2ef25c3820bc.json), pp.1,7--8 and cited limitations sections pp.34--36 in card | Illustrative perfect-SIC context; decoding complexity/error propagation and overhead limitations | Historical context only, not current standards evidence or a proof of this exact optimizer. Damaged rate extraction is not copied; practical overhead is not silently modelled |

Cached source links may remain local-only; PDFs and extracted libraries are
not included in the Git repository. Full source-page provenance remains in
the approved P2 cards; this table does not change their evidence bindings.

## Project derivations and limits

`model-spec.tex` independently derives, from the approved rate model:
both-site SIC inequality; full arbitrary-QoS interval with zero branches;
monotonicity, scalar concavity and optimum-set degeneracies; matched OMA
feasibility; the OMA-feasible => NOMA-feasible theorem and strict/equality
sum-rate cases using an established fairness witness; denominator ledger.
These are established-principle benchmark rederivations. Their formulas and
inequalities are not measured outcomes or a claim of scientific novelty.

`checks.yaml` is a bounded symbolic aid, not evidence for source content,
all domain inequalities, full proof correctness or floating-point behavior.
`algorithm.md` proposes independent validation; no oracle has been implemented
or accepted. P5 parameters, tolerances and distributions are not stated.
Hardware, modulation, residual SIC and finite-block performance are outside
this idealized dry run. Any extension requires the established deviation
and PI decision process rather than an inferred assumption change.
