import subprocess
from pathlib import Path

import pytest

import lab.simulation
from lab.io import LabError
from lab.verification import custom_verify


class SelectedPinnedScript(Exception):
    pass


@pytest.fixture
def artifact(tmp_path, monkeypatch):
    p = tmp_path / "projects/probe"
    p.mkdir(parents=True)
    (tmp_path / "pinned.py").write_text("# isolated unit fixture\n", encoding="utf-8")
    spec = {"entrypoint": "simulator.py", "verifier": "pinned.py"}
    monkeypatch.setattr(
        lab.simulation,
        "locked",
        lambda path: (spec, {"input_hashes": {"pinned.py": "unchanged-digest"}}),
    )

    def prevent_execution(argv, **kwargs):
        kwargs.pop("env", None)
        assert Path(argv[1]) == tmp_path / "pinned.py"
        assert kwargs["timeout"] == 3600
        raise SelectedPinnedScript("No execution; native guard selected the declared pinned script")

    monkeypatch.setattr(subprocess, "run", prevent_execution)
    return p, spec


def test_protocol_verifier_alias(artifact):
    p, s = artifact
    with pytest.raises(SelectedPinnedScript):
        custom_verify(p, s, [])


def test_canonical_key_still_works(artifact):
    p, s = artifact
    s["verification_entrypoint"] = s.pop("verifier")
    with pytest.raises(SelectedPinnedScript):
        custom_verify(p, s, [])


def test_equal_keys_allowed(artifact):
    p, s = artifact
    s["verification_entrypoint"] = s["verifier"]
    with pytest.raises(SelectedPinnedScript):
        custom_verify(p, s, [])


def test_conflicting_keys_rejected(artifact):
    p, s = artifact
    s["verification_entrypoint"] = "other.py"
    with pytest.raises(LabError, match="Conflicting verification entrypoint declarations"):
        custom_verify(p, s, [])


@pytest.mark.parametrize("name", [None, "foreign.py", "simulator.py"])
def test_missing_unpinned_or_simulator_rejected(artifact, name):
    p, s = artifact
    s["verifier"] = name
    with pytest.raises(LabError, match="distinct independently reviewed verifier pinned"):
        custom_verify(p, s, [])
