---
name: idea-ranking
description: Use by ideator in approved P3 to screen, score and rank complete evidence-backed idea cards.
---

# idea-ranking

Read the PI-reviewed thesis profile, scope, findings and gap matrix. Produce at
least fifteen varied idea cards conforming to schemas/idea_card.schema.json.
Each includes three existing closest works with precise deltas, risks, compute
estimate, months to submission and two or three recent venue comparators.
Screen feasibility first, then an independent novelty verdict. Research-mode
eligibility is limited to the publishable verdicts allowed in config/ranking.yaml.
Only a G1-reviewed scope with mode: dry-run also permits already-done benchmarks;
retain that verdict and label outputs as a dry run. Unclear verdicts stay ineligible.
Use lab ideas rank/sensitivity. Time scores use the four configured month
thresholds (default <=3/4/6/9 =>5/4/3/2, else1).
For workflow: reproduction, prepare a schema-valid reproduction selection and
written figure/data/ablation plan instead of idea cards; G3 still requires the
PI's explicit selection. Never change the approved workflow to bypass a gate.
Never equate a high ranking score with novelty or PI selection. Request G3 with
the ranked shortlist and weight sensitivity; the PI selects the idea.
