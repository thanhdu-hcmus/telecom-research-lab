from pathlib import Path

import pytest

from lab import state
from lab.io import LabError, git, load, save


@pytest.fixture
def scoped(tmp_path):
    (tmp_path / "projects").mkdir()
    save(tmp_path / "config/thesis-profile.yaml", {"pi_reviewed": True})
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Fixture PI")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    state.init(tmp_path, "toy")
    path = state.project(tmp_path, "toy")
    save(
        path / "scope.yaml",
        dict(
            area="Two-user NOMA",
            keywords=["NOMA"],
            inclusion=["Rayleigh"],
            exclusion=["beam management"],
            year_from=2020,
            target_venues=["Q2"],
            thesis_profile_reviewed=True,
        ),
    )
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "fixture init")
    return path


def test_init_contract_and_gate_stops_progress(scoped):
    assert state.state(scoped)["phase"] == "P1"
    with pytest.raises(LabError, match="PI approval"):
        state.enter(scoped, "P2")
    assert state.request(scoped, "G1")["status"] == "PASS"
    with pytest.raises(LabError, match="interactive"):
        state.decide(scoped, "G1", "approve", "approved")
    assert not state.decisions(scoped)


def test_approval_binds_artifacts_and_invalidation(scoped, monkeypatch):
    monkeypatch.setattr(state, "pi_confirm", lambda _: None)  # Test-only PI input substitute.
    state.request(scoped, "G1")
    state.decide(scoped, "G1", "approve", "Fixture decision")
    state.enter(scoped, "P2")
    # Evolving narrative and append-only logs do not invalidate the scope.
    (scoped / "findings.md").write_text("New literature findings", encoding="utf-8", newline="\n")
    state.require(scoped, "G1")
    (scoped / "scope.md").write_text("Changed assumptions", encoding="utf-8", newline="\n")
    with pytest.raises(LabError, match="changed"):
        state.require(scoped, "G1")
    assert all(g["status"] == "invalidated" for g in state.state(scoped)["gates"].values())


def test_edit_between_request_and_approve_rejected(scoped, monkeypatch):
    monkeypatch.setattr(state, "pi_confirm", lambda _: None)
    state.request(scoped, "G1")
    (scoped / "scope.md").write_text("new scope", encoding="utf-8", newline="\n")
    with pytest.raises(LabError, match="changed"):
        state.decide(scoped, "G1", "approve", "Fixture")


def test_rewind_archives_and_history_is_append_only(scoped, monkeypatch):
    monkeypatch.setattr(state, "pi_confirm", lambda _: None)
    state.request(scoped, "G1")
    state.decide(scoped, "G1", "approve", "Fixture")
    before = state.decisions(scoped)[0].copy()
    state.enter(scoped, "P2")
    (scoped / "literature/keep.txt").write_text("irreplaceable", encoding="utf-8", newline="\n")
    result = state.rewind(scoped, "P2", "Fixture rewind")
    assert (Path(result["archive"]) / "literature/keep.txt").read_text() == "irreplaceable"
    assert state.decisions(scoped)[0] == before
    records = state.decisions(scoped)
    records[0]["note"] = "tampered"
    save(scoped / "gates/decisions.yaml", records)
    with pytest.raises(LabError, match="altered"):
        state.decisions(scoped)


def test_forged_state_and_failed_validation_are_rejected(scoped, monkeypatch):
    value = state.state(scoped)
    value["gates"]["G1"].update(status="approved", artifact_hashes=state.snapshot(scoped, 1))
    state.update(scoped, value)
    with pytest.raises(LabError, match="recorded"):
        state.require(scoped, "G1")
    save(scoped / "scope.yaml", {})
    assert state.request(scoped, "G1")["status"] == "FAIL"
    monkeypatch.setattr(state, "pi_confirm", lambda _: None)
    with pytest.raises(LabError, match="checks failed"):
        state.decide(scoped, "G1", "approve", "Fixture")


def test_deviation_tty_and_provenance(scoped):
    opened = state.deviation_open(
        scoped, "metric", "new idea", "change metric", "invalidates comparison"
    )
    with pytest.raises(LabError, match="interactive"):
        state.deviation_resolve(scoped, opened["deviation"]["id"], "approved", "Fixture")
    result = state.provenance(scoped, "AI drafted scope", ["scope.md"])
    assert result["session"]["provenance"] == "ai"
    assert load(scoped / "ara/trace/sessions/session_index.yaml")


def test_confirmation_mismatch(monkeypatch):
    monkeypatch.setattr(state.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(state.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "incorrect")
    with pytest.raises(LabError, match="did not match"):
        state.pi_confirm("APPROVE G1")


def test_failed_commit_does_not_leave_approval(scoped, monkeypatch):
    monkeypatch.setattr(state, "pi_confirm", lambda _: None)
    state.request(scoped, "G1")

    def fail(*args):
        raise LabError("Commit failed")

    monkeypatch.setattr(state, "commit_decision", fail)
    with pytest.raises(LabError, match="Commit failed"):
        state.decide(scoped, "G1", "approve", "Fixture")
    assert state.state(scoped)["gates"]["G1"]["status"] == "pending"
    assert state.decisions(scoped) == []
