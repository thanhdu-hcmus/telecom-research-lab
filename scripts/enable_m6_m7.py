from build_support import ROOT, evaluation, role, skill
from lab.io import save

skill(
    "baseline-reproduction",
    "Use by sim_engineer in approved P5 to pin, scan, review and reproduce paper-linked baseline code.",
    """
Read candidate evidence and config/baselines.yaml. Clone a full immutable GitHub
commit through lab baseline clone into ignored external/. Scan and manually
review all source, dependencies, license and data; a clean scan is not clearance.
Record reviewed file hashes before lab baseline env creates an isolated uv venv.
Never run unreviewed downloads. MATLAB execution uses a function with an onCleanup
path restoration and explicit addpath for the reviewed source only.
Reproduce the named paper figure/table. Save reference and actual curves, pinned
code, environment, seeds and run manifest. Compare declared units: <=0.5 dB absolute
or <=5% relative plus same trend/order. Overlay with lab.baseline.overlay.
Only then score: venue/citation tiers exclusive, official link, license and
maintenance/self-contained evidence. Reproduction and score>=3 are mandatory;
tutorials, unverifiable paper links or disallowed data are always rejected.
""",
)
repro = """# CC0 authored fixture baseline, not downloaded code.\nimport json, math\nrho=[1,2,5,10,20]\nprint(json.dumps({"rho":rho,"outage":[1-math.exp(-1/x) for x in rho]}))\n"""
evaluation(
    "repro-small",
    "sim_engineer",
    "Read fixture README.md, baseline.py and baseline-reproduction. Execute the self-authored safe fixture baseline with the available Python interpreter; capture stdout. Return JSON {rho:[...],outage:[...],command:'actual command',agreement:{mode:'relative',same_trend:true}}. Do not write files. Never report execution without doing it.",
    {
        "baseline.py": repro,
        "README.md": "CC0 synthetic Rayleigh outage baseline. Target: 1-exp(-1/rho), rho=1,2,5,10,20. Requires standard Python only; output JSON to stdout. This fixture code is reviewed and authorized for execution.",
    },
    {},
)
skill(
    "wireless-system-modeling",
    "Use by system_modeler in approved P4 to produce explicit telecom models, assumptions and falsifiable predictions.",
    """
Read selected idea, closest grounded cards and findings. Define every symbol in
notation.yaml with dimension, unit and meaning. Read [conventions](references/conventions.md).
Write model-spec.tex, cited assumptions.yaml (consequence and relaxation/test),
predictions.yaml with regime/tolerance/test, algorithm pseudocode, block convexity,
convergence limitations and honest complexity. Distinguish theorem, approximation
and conjecture. Use lab model check for bounded SymPy identity/Hessian/limit checks.
Send only artifacts to an independent model_critic. Respond with fixes or evidence
for rebuttals, <=3 rounds; unresolved critical/major findings require PI action.
""",
)
conventions = """# Telecom conventions\n\nVectors bold lowercase, matrices bold uppercase; Hermitian H, transpose T.\nCN(0,1) has real/imaginary variance 1/2. State channel normalizations explicitly.\nParameter powers dBm; computation W. Noise dBm=-174+10 log10(B_Hz)+NF_dB.\nUse tested simkit helpers, never inline conversion. Split reference path loss and\nsmall-scale fading. State reference distance, exponent, frequency and geometry.\nRayleigh/Rician K/LoS geometry or other distribution must be explicit. Define RIS\ncascade, phase bits, modulus/amplitude coupling, passive/active/STAR, spacing and\naperture. N squared scaling assumes increasing aperture, not fixed physical area.\nDeclare perfect/imperfect/statistical CSI and estimation overhead; specify error\nmodel and robustness. Define NOMA ordering/pairing, power constraints and residual\nSIC. State convexity by block; distinguish relaxation from exact formulation.\nAO/SCA/SDR/manifold/DRL guarantees, randomization and complexity need evidence.\n"""
save(
    ROOT / "docs/evidence/m7-conventions.json",
    {
        "corrected_plan_rendering": "Noise log10 bandwidth, CN(0,1), BPSK Q(sqrt(2 Eb/N0)); equations rendered ambiguously in original plan interpreted explicitly."
    },
)
p = ROOT / ".agents/skills/wireless-system-modeling/references/conventions.md"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(conventions, encoding="utf-8", newline="\n")
skill(
    "model-critique",
    "Use by model_critic for an independent P4 artifact review using telecom checks and scientific rigor.",
    """
Read only the model artifacts, closest papers and [checklist](references/telecom-checklist.md).
Do not read author reasoning or summaries. Check assumptions, math, evidence,
reproducibility, claim scope and practical relevance. Explicitly answer every
checklist item and report schema-valid findings with severity, category, exact
location, issue, consequence and fix/test. Categories include hidden-assumption,
sic-order-inconsistency, unit-mismatch, false-convexity, unfair-baseline and
complexity-error. Critical blocks validity; major affects conclusions; minor is
local presentation. Avoid unsupported critical accusations on a clean model.
No gate approval. After three rounds unresolved issues return to PI.
""",
)
p = ROOT / ".agents/skills/model-critique/references/telecom-checklist.md"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(
    """# Telecom review checklist\n\n1. Hidden/explicit and realistic/convenient assumptions?\n2. CSI justified; RIS channel-estimation overhead acknowledged?\n3. SIC order consistent with channels and power allocation?\n4. Dimensions and units correct in every equation?\n5. Block convexity correct; relaxation tightness/gap quantified?\n6. Predictions consistent with the formulation and regime?\n7. Fair power, CSI, channel realizations and strongest relevant baselines?\n8. Realistic frequency, bandwidth, distances and RIS geometry?\n9. Correct complexity; multiple seeds?\n10. Novelty delta supported by grounded closest-work cards?\n11. Scalability and practical implementation concerns?\n\nRigor dimensions: assumptions, mathematics, evidence, reproducibility,\nclaim calibration and practical relevance. State unknowns; propose discriminating tests.\n""",
    encoding="utf-8",
    newline="\n",
)
role(
    "system_modeler",
    "Produce model-spec, notation, assumptions, predictions, algorithm and bounded symbolic checks. Do not assert unproved convexity or asymptotics.",
)
role(
    "model_critic",
    "Independently review only supplied artifacts, answer all telecom checklist items and return location-grounded schema-valid findings, no author reasoning.",
)
flawed = """# Synthetic flawed model\n[A1] The optimizer observes exact instantaneous channels; assumptions list mentions only Rayleigh fading and does not declare CSI or estimation.\n[SIC] g1<g2; a1=0.2,a2=0.8; weak user1 first decodes stronger user's message, strong user2 never decodes user1.\n[NOISE] SINR=P*g/(-94); noise variance is taken directly from -94 dBm.\n[CONVEX] maximize x*y on x,y in [0,1] is claimed a convex optimization problem.\n[FAIR] Proposed total power=1 W; OMA baseline total power=0.1 W, same bandwidth.\n[COST] Dense n-by-n matrix inversion each iteration claimed O(n).\n"""
clean = """# Synthetic clean control\n[A1] Perfect instantaneous CSI explicitly assumed for a theoretical upper bound; estimation overhead ignored and robustness untested, listed as limitations.\n[SIC] fixed users g1<g2, a1=0.8,a2=0.2. Weak user decodes own while treating strong as interference; strong decodes weak then own with perfect SIC. Require a1>gamma1*a2.\n[NOISE] Noise variance=10**((-94-30)/10) W via tested conversion helper.\n[CONVEX] Bilinear xy Hessian has eigenvalues +1,-1; no joint convexity claim. Coordinate heuristic has no global guarantee.\n[FAIR] NOMA and OMA total power=1 W, same bandwidth, channels, CSI and channel seeds.\n[COST] Dense inversion O(n^3), memory O(n^2). Multiple simulation seeds required.\n"""
categories = [
    "hidden-assumption",
    "sic-order-inconsistency",
    "unit-mismatch",
    "false-convexity",
    "unfair-baseline",
    "complexity-error",
]
evaluation(
    "critic-planted-flaws",
    "model_critic",
    "Read fixture flawed.md and clean.md and model-critique checklist. Return JSON {flawed:[CritiqueFinding,...],clean:[CritiqueFinding,...]}. Each location must include its bracketed source label. Assess each independently; classify actual issues, never infer a flaw merely because the filename says flawed. Do not approve gates.",
    {"flawed.md": flawed, "clean.md": clean},
    {"categories": dict(zip(categories, ["A1", "SIC", "NOISE", "CONVEX", "FAIR", "COST"]))},
)
