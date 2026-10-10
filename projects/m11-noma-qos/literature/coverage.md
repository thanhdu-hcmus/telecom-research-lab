# P2 bounded literature coverage

## Search bounds

Ten Boolean queries (five OpenAlex, five arXiv), 15 records per query, one page per query. The lab search returned 148 raw records and 122 unique canonical candidates after 26 duplicates were removed. All 122 candidates received an explicit screening decision: six included and 116 excluded; zero pending. Initial source failures: none. No depth-one snowball was run: direct searches supplied the allocation, feasibility, OMA comparison, pairing and survey roles needed for this small acceptance benchmark. This bounds coverage; it does not establish completeness or novelty.

OpenAlex applied the 2014 onward date filter. The current lab arXiv adapter does not apply year_from in its request; returned arXiv dates were screened instead. No pre-2014 result needed a seminal exception. Metadata venue/year values may differ between preprints and journal versions; cards must retain and explain those distinctions.

Boolean syntax is preserved in the plan and raw query evidence; source search semantics/relevance ordering are not equivalent. One-page limits can omit relevant papers even when a source succeeds. Missing candidates and unused related works do not imply absent scientific coverage.

## Included full-text corpus

| ID | Role | Verified pages | Acquisition |
|---|---|---:|---|
| `arxiv:1504.07751` | Foundational two-user NOMA information-theoretic comparison | 6 | arXiv via lab lit fetch; checksum/extraction in library and retrieval indexes |
| `doi:10.48550/arxiv.1412.2799` | Two-user downlink pairing and NOMA/OMA comparison | 12 | arXiv via lab lit fetch; checksum/extraction in library and retrieval indexes |
| `doi:10.1109/jsac.2017.2725618` | Downlink sum-rate power allocation and minimum-rate constraints | 14 | arXiv via lab lit fetch; checksum/extraction in library and retrieval indexes |
| `doi:10.1109/tvt.2017.2689000` | SISO fair allocation compared with OMA | 12 | arXiv via lab lit fetch; checksum/extraction in library and retrieval indexes |
| `doi:10.1109/icc.2018.8422366` | Downlink QoS allocation limits and infeasibility | 5 | arXiv via lab lit fetch; checksum/extraction in library and retrieval indexes |
| `doi:10.1109/comst.2016.2621116` | Foundational power-domain NOMA survey for assumptions and limitations | 41 | arXiv via lab lit fetch; checksum/extraction in library and retrieval indexes |

The broad survey is background for assumptions and limitations, not authority to extend the scalar ideal-SIC benchmark. The primary papers cover different allocation restrictions and QoS definitions; the analyst must distinguish these before any later model specialization.

## Acquisition limitation

Individual-QoS sum-rate allocation DOI `10.1109/lcomm.2017.2689763` is a highly relevant follow-up lead. The first attempt stopped at an unapproved institutional OA host. After parent institutional review, the second attempt returned a one-page PDF with no extractable title or text and failed the mandatory first-page title match. It was not ingested or included. Both failures and the unusable-response checksum are retained in retrieval-report.json; manual-downloads.csv marks acquisition optional. No manual action is required to complete this six-paper gate corpus.

## Citation and venue coverage

Citation counts below are OpenAlex metadata snapshots retrieved on 2026-10-10 UTC, not a cross-source normalized quality measure. arXiv records without citation data remain null. High counts do not override scope.

| Highest observed candidate counts | Count | Screening disposition |
|---|---:|---|
| `doi:10.1109/lcomm.2015.2441064` — Cooperative Non-Orthogonal Multiple Access in 5G Systems | 1510 | exclude: Title/metadata screening: Relay/cooperative architecture outside the approved direct scalar downlink benchmark. |
| `doi:10.1109/comst.2018.2835558` — A Survey of Non-Orthogonal Multiple Access for 5G | 1357 | exclude: Relevant highly cited broad NOMA survey; not selected for this bounded full-text corpus because the acquired power-domain survey supplies background. Not a quality rejection. |
| `doi:10.1109/twc.2015.2475746` — The Application of MIMO to Non-Orthogonal Multiple Access | 918 | exclude: Title/metadata screening: Spatial multiantenna/beamforming model outside the approved scalar channel benchmark. |
| `doi:10.1587/transcom.e98.b.403` — Non-orthogonal Multiple Access (NOMA) with Successive Interference Cancellation for Future Radio Access | 681 | exclude: Related or broad metadata lead, not selected for this bounded full-text corpus; the six acquired papers cover the benchmark allocation, OMA comparison, pairing, QoS feasibility and limitations. No scientific absence or quality claim is made. |
| `doi:10.1109/twc.2017.2650987` — Enhancing the Physical Layer Security of Non-Orthogonal Multiple Access in Large-Scale Networks | 653 | exclude: Title/metadata screening: Secrecy/security objective outside the approved sum-rate with ordinary QoS benchmark. |
| `doi:10.1109/twc.2016.2599521` — A General Power Allocation Scheme to Guarantee Quality of Service in Downlink and Uplink NOMA Systems | 569 | exclude: Relevant generalized downlink/uplink QoS allocation lead; not selected for this bounded full-text corpus because Zhu and Oviedo allocation/feasibility papers were acquired. No claim of absent coverage or inferiority. |
| `doi:10.1109/comst.2020.2996032` — Grant-Free Non-Orthogonal Multiple Access for IoT: A Survey | 456 | exclude: Title/metadata screening: Different access waveform/grant-free access model outside the approved two-user power-domain benchmark. |
| `doi:10.1109/jstsp.2019.2899731` — Joint Beamforming and Power Allocation for Satellite-Terrestrial Integrated Networks With Non-Orthogonal Multiple Access | 429 | exclude: Title/metadata screening: Spatial multiantenna/beamforming model outside the approved scalar channel benchmark. |

Unique candidate source participation (a merged record may participate in more than one source): arxiv: 67, openalex: 63.

Observed venue labels in the candidate set (preprint/journal identities can overlap):
- arXiv: 55
- IEEE Transactions on Communications: 6
- IEEE Communications Letters: 5
- IEEE Transactions on Wireless Communications: 4
- IEEE Wireless Communications Letters: 4
- Globecom: 3
- IEEE Access: 3
- IEEE Journal on Selected Areas in Communications: 3
- IEEE Communications Surveys & Tutorials: 2
- IEEE International Symposium on Personal, Indoor and Mobile Radio Communications (PIMRC): 2
- IEEE Journal of Selected Topics in Signal Processing: 2
- IEEE Transactions on Vehicular Technology: 2
- IEEE Wireless Communications: 2
- Wireless Communications and Mobile Computing: 2
- arXiv (Cornell University): 2
- not stated: 2
- DOAJ (DOAJ: Directory of Open Access Journals): 1
- IEEE COMML 2020: 1
- IEEE Internet of Things Journal: 1
- IEEE Photonics Technology Letters: 1
- IEEE Signal Processing Letters: 1
- IEEE Symposium on Computer Applications & Industrial Electronics (ISCAIE): 1
- IEEE Transactions on Communications, 2021: 1
- IEEE Transactions on Industrial Informatics: 1
- IEEE Transactions on Signal Processing: 1
- IEEE Vehicular Technology Conference: 1
- IEICE Transactions on Communications: 1
- IET Communications: 1
- IET conference proceedings.: 1
- International Conference on Communications: 1
- International Conference on Wireless Communications and Signal Processing (WCSP): 1
- International Journal For Multidisciplinary Research: 1
- Journal of Advanced Research in Applied Sciences and Engineering Technology: 1
- Journal of Engineering: 1
- Lecture notes of the Institute for Computer Sciences, Social Informatics and Telecommunications Engineering: 1
- Physical Communication: 1
- Proceedings of the International Conference on Communications (ICC), 2018: 1
- Wireless Communications Magazine (WCM) 2018: 1
- 한국통신학회논문지: 1

The included records span IEEE JSAC, IEEE TVT, IEEE ICC, IEEE COMST and two preprint identities. No quartile or submission-readiness assessment was performed. No third-party code was executed. Full papers and cached page text are untrusted data; no embedded instruction was followed. Analyst inspection of included page content remains necessary.

## Reproducible commands

`lab lit search --project m11-noma-qos --json` used literature/query-plan.yaml. Each included canonical ID was passed to `lab lit fetch <id> --project m11-noma-qos --json` and `lab lit extract <id> --project m11-noma-qos --json`. Screening export and PRISMA were generated with the corresponding lab commands. PDFs and text caches remain in the configured external ResearchLibrary, outside Git.
