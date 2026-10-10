from build_support import ROOT, evaluation, role, skill
from lab.io import load, read_jsonl, save

skill(
    "idea-ranking",
    "Use by ideator in approved P3 to screen, score and rank complete evidence-backed idea cards.",
    """
Read the PI-reviewed thesis profile, scope, findings and gap matrix. Produce at
least fifteen varied idea cards conforming to schemas/idea_card.schema.json.
Each includes three existing closest works with precise deltas, risks, compute
estimate, months to submission and two or three recent venue comparators.
Screen feasibility first, then an independent novelty verdict. Only novel or
incremental-but-publishable cards are eligible. Use config/ranking.yaml and lab
ideas rank/sensitivity. Time scores follow <=3/4/6/9 months =>5/4/3/2, else1.
Never equate a high ranking score with novelty or PI selection. Request G3 with
the ranked shortlist and weight sensitivity; the PI selects the idea.
""",
)
skill(
    "novelty-audit",
    "Use by novelty_auditor in P3 for independent targeted searches and evidence-backed novelty verdicts.",
    """
Read the idea and grounded closest works, not the author's reasoning. For each
idea run at least five distinct targeted queries across scholarly sources and
web author/code pages. Include equivalent formulations and renamed mechanisms.
Save a dated report with query, source, receipt/evidence, closest IDs, overlap,
precise delta and verdict: already-done, unclear, novel or
incremental-but-publishable. Missing search results alone do not establish novelty.
If an idea reproduces a published formulation, cite the exact existing work and
mark already-done. Unsupported or unsearched deltas are unclear. Closed fixtures
cannot justify global novelty; state their scope. Never invent citations.
""",
)
skill(
    "brainstorming-research-ideas",
    "Use by ideator in P3 to generate diverse tractable telecom problems from grounded gaps.",
    """
Adapted from the reviewed Orchestra brainstorming source archived with MIT
license under vendor/orchestra. Read the thesis profile and grounded gaps.
Generate candidates using assumption relaxation, objective reformulation,
constraint realism, estimation overhead and analytic simplification. Separate
generation from screening. Every proposal must define a falsifiable improvement,
closest works and simulation/compute budget. Avoid arbitrary buzzword combinations.
Use idea-ranking to record complete cards and independent novelty-audit to screen.
""",
)
skill(
    "creative-thinking-for-research",
    "Use by ideator in P3 to explore alternative formulations while preserving evidence and feasibility.",
    """
Adapted from the reviewed Orchestra creative-thinking source with MIT license in
vendor/orchestra. Explore counterexamples, reversed assumptions, boundary cases,
mechanism transfer and minimal models. Record why each change should matter and
what would falsify it. Separate conjecture from established results; compare at
least three existing works. Do not claim novelty before independent audit.
""",
)
role(
    "ideator",
    "Produce >=15 schema-valid ideas from grounded gaps; use ranking and sensitivity; never select for the PI.",
)
role(
    "novelty_auditor",
    "Independently compare formulations with cited existing works and targeted search receipts; never infer global novelty from no hits.",
)
key_ids = set(load(ROOT / "tests/evals/lit-recall/expected.yaml")["key_ids"])
corpus = [
    r
    for r in read_jsonl(ROOT / "tests/evals/lit-recall/fixture/corpus.jsonl")
    if r["id"] in key_ids
][:3]
works = [
    {k: c.get(k) for k in ["id", "title", "abstract", "doi", "authors", "year", "venue"]}
    for c in corpus
]
ideas = [
    {
        "id": f"I{i + 1}",
        "description": f"Implement and evaluate exactly the formulation and method in {c['title']}; rename the method Adaptive Surface Allocation.",
    }
    for i, c in enumerate(works)
]
ideas += [
    {
        "id": "I4",
        "description": "Quantify joint channel-estimation time and discrete-phase hardware energy in a near-field model; no supplied work evaluates this.",
    },
    {
        "id": "I5",
        "description": "Derive finite-sample calibration guarantees for a distribution-shift outage predictor; no supplied work evaluates this.",
    },
]
evaluation(
    "novelty-detect",
    "novelty_auditor",
    "Read fixture works.yaml and ideas.yaml and novelty-audit. Return JSON {verdicts:[{id,verdict,citation,reason}]}. Detect equivalent published ideas. For unmatched ideas use unclear unless evidence supports stronger novelty. Only the bounded fixture corpus is available.",
    {"works.yaml": works, "ideas.yaml": ideas},
    {"published": dict(zip(["I1", "I2", "I3"], [c["id"] for c in works])), "open": ["I4", "I5"]},
)
profile = load(ROOT / "config/thesis-profile.yaml")
profile["pi_reviewed"] = True
profile["title"] = "Synthetic fixture: RIS-assisted NOMA power allocation"
profile["abstract"] = "Synthetic fixture scope, CPU-only model-based RIS/NOMA optimization"
profile["time_budget_months_per_paper"] = 6
evaluation(
    "idea-card-completeness",
    "ideator",
    "Read fixture profile.yaml and works.yaml and idea-ranking. This is a reduced synthetic evaluation: return JSON {cards:[exactly one complete IdeaCard]}, not fifteen. Include three DISTINCT closest work IDs copied exactly from works.yaml. scores.venue.evidence must be an array of at least two exact work ID strings (not file paths or section references); discuss unknown current quartiles in rationale and use conservative score. All required fields and proposed compute estimate. Novelty is unclear; report path ideas/novelty/fixture.yaml because this bounded fixture has no searches. Do not fabricate research evidence.",
    {"profile.yaml": profile, "works.yaml": works},
    {"work_ids": [c["id"] for c in works]},
)
save(
    ROOT / "docs/evidence/m5-fixture-provenance.json",
    {
        "works": "Three recorded OpenAlex corpus records; ideas are authored evaluation probes; unmatched ideas intentionally remain unclear",
        "license": "CC0 for synthetic prompts; upstream metadata attribution retained",
    },
)
