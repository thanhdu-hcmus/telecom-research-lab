"""Single source of truth for Pydantic validation and exported JSON Schemas."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Text = Annotated[str, Field(min_length=1)]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Phase = Literal["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
Gate = Literal["G1", "G2", "G3", "G4", "G5", "G6", "G7"]


class Artifact(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Evidence(Artifact):
    source: Text
    page: Annotated[int, Field(ge=1)] | None = None
    location: Text


class PaperCard(Artifact):
    id: Text
    title: Text
    authors: list[Text] | None = Field(min_length=1)
    year: int | None = Field(ge=1900, le=2200)
    venue: dict[str, Any] | None
    citations: dict[str, Any] | None
    system: dict[str, Any] | None
    channel: dict[str, Any] | None
    objective: str | None
    constraints: list[str] | None
    method: list[str] | None
    baselines_compared: list[str] | None
    metrics: list[str] | None
    key_results: list[str] | None
    limitations_stated: list[str] | None
    future_work_stated: list[str] | None
    code: dict[str, Any] | None
    grounding: dict[str, list[Evidence]]
    notes: str = ""

    @model_validator(mode="after")
    def grounded(self):
        for name in type(self).model_fields:
            if name not in {"id", "grounding", "notes"} and getattr(self, name) is not None:
                if not self.grounding.get(name):
                    raise ValueError(f"Non-null field needs evidence: {name}")
                if name in {
                    "system",
                    "channel",
                    "objective",
                    "constraints",
                    "method",
                    "baselines_compared",
                    "metrics",
                    "key_results",
                    "limitations_stated",
                    "future_work_stated",
                    "code",
                }:
                    if not any(e.page is not None for e in self.grounding[name]):
                        raise ValueError(f"Scientific field needs a page reference: {name}")
        return self


class Score(Artifact):
    score: int = Field(ge=1, le=5)
    rationale: Text
    evidence: list[Text] = Field(default_factory=list)


class ClosestWork(Artifact):
    id: Text
    delta: Text


class Feasibility(Artifact):
    passed: bool = Field(alias="pass")
    reasons: list[Text] = Field(min_length=1)


class Novelty(Artifact):
    verdict: Literal["novel", "incremental-but-publishable", "already-done", "unclear"]
    report: Text


class IdeaCard(Artifact):
    id: Text
    title: Text
    problem: Text
    gap_refs: list[Text] = Field(min_length=1)
    closest_works: list[ClosestWork] = Field(min_length=3)
    method_sketch: Text
    expected_contributions: list[Text] = Field(min_length=1)
    risks: list[Text] = Field(min_length=1)
    risk_rating: int = Field(ge=1, le=5)
    resources: dict[str, Any]
    time_estimate_months: float = Field(gt=0)
    target_venue_class: Text
    feasibility: Feasibility
    novelty: Novelty
    scores: dict[Literal["thesis_fit", "time", "venue"], Score]

    @model_validator(mode="after")
    def complete(self):
        if len({w.id for w in self.closest_works}) < 3:
            raise ValueError("At least three distinct closest works required")
        if set(self.scores) != {"thesis_fit", "time", "venue"}:
            raise ValueError("All three scores required")
        if not self.resources.get("compute_estimate"):
            raise ValueError("Compute estimate required")
        if len(set(self.scores["venue"].evidence)) < 2:
            raise ValueError("Venue score needs at least two comparable papers")
        return self


class Assumption(Artifact):
    id: Text
    statement: Text
    justification: Text
    citation: Text
    consequence_if_violated: Text
    test_or_relaxation: Text


class Prediction(Artifact):
    id: Text
    statement: Text
    expression_or_law: Text
    regime: Text
    test_method: Text
    tolerance: dict[str, Any]


class CritiqueFinding(Artifact):
    id: Text
    severity: Literal["critical", "major", "minor"]
    category: Literal[
        "hidden-assumption",
        "sic-order-inconsistency",
        "unit-mismatch",
        "false-convexity",
        "unfair-baseline",
        "complexity-error",
        "novelty-overclaim",
        "prediction-error",
        "practicality",
        "other",
    ]
    location: Text
    issue: Text
    why_it_matters: Text
    suggested_fix_or_test: Text
    status: Literal["open", "fixed", "rebutted"] = "open"


class OutputFile(Artifact):
    path: Text
    storage: Literal["project", "library"] = "project"
    sha256: Digest
    bytes: int = Field(ge=0)


class RunManifest(Artifact):
    run_id: Text
    git_sha: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    protocol_commit: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    protocol_hash: Digest
    input_hashes: dict[str, Digest]
    scenario: Text
    params: dict[str, Any]
    seeds: list[int] = Field(min_length=1)
    language: Literal["python", "matlab"]
    env: dict[str, Any]
    host: dict[str, Any]
    start: Text
    end: Text
    runtime_s: float = Field(ge=0)
    outputs: list[OutputFile] = Field(min_length=1)
    status: Literal["complete", "failed"]


class VerificationItem(Artifact):
    id: Text
    prediction_ref: Text
    method: Text
    metric: Text
    value: float | None
    tolerance: dict[str, Any]
    verdict: Literal["PASS", "FAIL", "INCONCLUSIVE"]
    triage: (
        Literal["implementation-bug", "theory-error", "approximation-gap", "statistical-noise"]
        | None
    )
    evidence_paths: list[Text] = Field(min_length=1)


class Claim(Artifact):
    key: Annotated[str, Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")]
    value: float
    unit: Text
    source_manifest: Text
    computation: Text
    used_in: list[Text] = Field(min_length=1)


class GateDecision(Artifact):
    gate: Gate
    decision: Literal["approve", "revise", "rewind"]
    note: Text
    timestamp: Text
    git_user: Text
    selected_idea: str | None = None
    artifact_hashes: dict[str, Digest]
    previous_hash: str | None
    record_hash: Digest


class Deviation(Artifact):
    id: Text
    phase: Phase
    what: Text
    why: Text
    proposed_change: Text
    impact: Text
    status: Literal["open", "approved", "rejected"] = "open"
    decided_by: str | None = None
    decision_note: str | None = None


class Scope(Artifact):
    mode: Literal["research", "dry-run"] = "research"
    workflow: Literal["ideation", "reproduction"] = "ideation"
    profile: Text = "config/thesis-profile.yaml"
    area: Text
    keywords: list[Text] = Field(min_length=1)
    inclusion: list[Text] = Field(min_length=1)
    exclusion: list[Text] = Field(min_length=1)
    year_from: int = Field(ge=1900)
    target_venues: list[Text] = Field(min_length=1)
    thesis_profile_reviewed: bool


class ReproductionSelection(Artifact):
    id: Text
    reference_id: Text
    purpose: Literal["reproduce-and-ablate"]
    reference_figures: list[Text] = Field(min_length=1)
    ablation: Text
    expected_outputs: list[Text] = Field(min_length=1)
    code_status: Literal["official-code", "reimplementation"]
    code_revision: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")] | None = None
    data_availability: Text

    @model_validator(mode="after")
    def official_revision(self):
        if self.code_status == "official-code" and not self.code_revision:
            raise ValueError("Official code requires a full pinned commit SHA")
        return self


class GateState(Artifact):
    status: Literal["not_started", "pending", "approved", "revise", "invalidated"] = "not_started"
    timestamp: str | None = None
    note: str | None = None
    artifact_hashes: dict[str, Digest] = Field(default_factory=dict)
    checks_passed: bool = False


class ResearchState(Artifact):
    version: int = 1
    project: Text
    phase: Phase = "P1"
    gates: dict[Gate, GateState]
    selected_idea: str | None = None
    baselines: dict[str, Any] = Field(default_factory=dict)
    protocol_hash: str | None = None
    protocol_commit: str | None = None
    deviations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


MODELS = {
    name: model
    for name, model in {
        "paper_card": PaperCard,
        "idea_card": IdeaCard,
        "assumption": Assumption,
        "prediction": Prediction,
        "critique_finding": CritiqueFinding,
        "run_manifest": RunManifest,
        "verification_item": VerificationItem,
        "claim": Claim,
        "gate_decision": GateDecision,
        "deviation": Deviation,
        "scope": Scope,
        "reproduction_selection": ReproductionSelection,
        "research_state": ResearchState,
    }.items()
}
