import shutil
from pathlib import Path

import pytest

from lab import simulation, state
from lab.io import LabError, git, load, save

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    repo = tmp_path
    shutil.copytree(ROOT / "lab", repo / "lab", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(ROOT / "uv.lock", repo / "uv.lock")
    git(repo, "init")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.test")
    path = repo / "projects/probe"
    (path / "sim").mkdir(parents=True)
    (path / "sim/protocol.md").write_text("# Authored synthetic test protocol\n", newline="\n")
    (repo / "source.py").write_text("# Fixture locked source\n", newline="\n")
    save(
        path / "sim/protocol.yaml",
        {
            "version": 1,
            "language": "python",
            "inputs": ["source.py"],
            "metrics": ["sumrate", "outage"],
            "fairness": dict.fromkeys(
                ["same_power", "same_bandwidth", "same_csi", "common_channels", "same_qos"], True
            ),
            "trial_policy": {"relative_ci_halfwidth": 0.01, "minimum_events": 100},
            "scenarios": [
                {
                    "id": "two-user",
                    "seeds": [1, 2],
                    "trials": 1000,
                    "params": {
                        "rho_linear": 10,
                        "a_weak": 0.8,
                        "target_rate_weak": 1,
                        "target_rate_strong": 1,
                    },
                }
            ],
        },
    )
    save(
        path / "research-state.yaml",
        {"project": "probe", "phase": "P5", "gates": {f"G{i}": {} for i in range(1, 8)}},
    )
    monkeypatch.setattr(
        state, "ensure_phase", lambda *_: None
    )  # Synthetic tests only; no live PI gate approved.
    return path


def commit(path):
    git(path.parents[1], "add", ".")
    git(path.parents[1], "commit", "-m", "Fixture protocol committed before any outputs")


def test_dirty_lock_and_real_ancestry(fixture):
    with pytest.raises(LabError):
        simulation.lock(fixture)
    commit(fixture)
    simulation.lock(fixture)
    (fixture / "sim/protocol.md").write_text("Changed metric", newline="\n")
    with pytest.raises(LabError):
        simulation.locked(fixture)


def test_framework_matlab_sources_are_locked(fixture):
    source = fixture.parents[1] / "matlab/+simkit/example.m"
    source.parent.mkdir(parents=True)
    source.write_text("function y=example(x)\ny=x;\nend\n", newline="\n")
    commit(fixture)
    receipt = simulation.lock(fixture)
    assert source.relative_to(fixture.parents[1]).as_posix() in receipt["input_hashes"]
    source.write_text("function y=example(x)\ny=x+1;\nend\n", newline="\n")
    with pytest.raises(LabError, match="changed"):
        simulation.locked(fixture)


def test_fairness_requires_booleans(fixture):
    spec = load(fixture / "sim/protocol.yaml")
    spec["fairness"]["same_power"] = "false"
    save(fixture / "sim/protocol.yaml", spec)
    with pytest.raises(LabError, match="Fair comparison"):
        simulation.protocol(fixture)


def test_resume_checksums_and_collect(fixture):
    commit(fixture)
    simulation.lock(fixture)
    a = simulation.run(fixture)
    assert len(a["jobs"]) == 2
    assert all(j["resumed"] for j in simulation.run(fixture)["jobs"])
    assert simulation.collect(fixture)["rows"] == 2
    m = next((fixture / "results/runs").glob("*/manifest.json"))
    value = load(m)
    value["protocol_commit"] = "f" * 40
    with pytest.raises(LabError):
        simulation.verify_manifest(fixture, value)
    out = fixture / load(m)["outputs"][0]["path"]
    out.write_text("tampered", newline="\n")
    with pytest.raises(LabError):
        simulation.validate_runs(fixture)


def test_large_results_outside_git_and_claims(fixture):
    import json

    import numpy as np

    from lab.verification import evaluate_claim

    save(
        fixture.parents[1] / "config/lab.config.yaml",
        {"library_root": "library", "large_result_bytes": 100},
    )
    commit(fixture)
    simulation.lock(fixture)
    simulation.run(fixture)
    assert simulation.collect(fixture)["rows"] == 2
    mfile = next((fixture / "results/runs").glob("*/manifest.json"))
    m = load(mfile)
    data = next(o for o in m["outputs"] if o["path"].endswith("metrics.csv"))
    assert data["storage"] == "library"
    values = np.genfromtxt(simulation.output_path(fixture, data), delimiter=",", names=True)
    c = dict(
        key="rate",
        value=float(values["noma_sumrate"].mean()),
        unit="bit/s/Hz",
        source_manifest=mfile.relative_to(fixture).as_posix(),
        computation=json.dumps(
            dict(op="mean", path=data["path"], storage="library", column="noma_sumrate")
        ),
        used_in=["paper/main.tex"],
    )
    assert evaluate_claim(fixture, c)["key"] == "rate"


def test_dl_leakage(fixture):
    spec = load(fixture / "sim/protocol.yaml")
    spec["dl"] = {
        "train_ids": ["same"],
        "validation_ids": ["v"],
        "test_ids": ["same"],
        "training_seeds": [1, 2, 3],
    }
    save(fixture / "sim/protocol.yaml", spec)
    with pytest.raises(LabError):
        simulation.protocol(fixture)


def test_code_relock_archives_old_jobs(fixture):
    commit(fixture)
    simulation.lock(fixture)
    simulation.run(fixture)
    (fixture.parents[1] / "source.py").write_text(
        "# Corrected synthetic implementation\n", newline="\n"
    )
    commit(fixture)
    result = simulation.relock(fixture, "Fix synthetic code without changing protocol")
    assert result["requires_fresh_G5"] and (Path(result["archived"]) / "runs").exists()
    assert not (fixture / "results/runs").exists()
    simulation.run(fixture)
    assert simulation.validate_runs(fixture)["status"] == "PASS"


def test_matlab_dispatch_parameters_and_environment(tmp_path, monkeypatch):
    from lab import matlab

    save(tmp_path / "config/lab.config.yaml", {"matlab_root": "unused", "matlab_route": "mcp"})
    script = tmp_path / "entry.m"
    script.write_text("function entry(seed, output_dir)\nend\n", newline="\n")
    folder = tmp_path / "run"
    folder.mkdir()

    def evaluate(repo, code, timeout):
        assert repo == tmp_path and "entry(42," in code and timeout == 1800
        assert load(folder / "params.json") == {"rho_linear": 10}
        assert "onCleanup" in code and "ver" in code
        save(folder / "matlab-environment.json", {"version": "synthetic unit fixture"})
        return {"result": {"content": []}}

    monkeypatch.setattr(matlab, "evaluate", evaluate)
    assert simulation.matlab_run(tmp_path, script, 42, folder, {"rho_linear": 10}) == {
        "version": "synthetic unit fixture"
    }


def test_custom_verifier_dispatch_and_tamper(fixture):
    import json

    from lab import verification

    repo = fixture.parents[1]
    spec = load(fixture / "sim/protocol.yaml")
    spec.update(entrypoint="source.py", verification_entrypoint="independent.py")
    spec["inputs"].append("independent.py")
    # Unit fixture exercises reviewed script dispatch and evidence binding.
    # It makes no claim that these synthetic checks are scientific verification.
    item = dict(
        id="synthetic-check",
        prediction_ref="T1",
        method="Unit fixture arithmetic",
        metric="sum",
        value=3,
        tolerance={"minimum": 3, "maximum": 3},
        verdict="PASS",
        triage=None,
        evidence_paths=["analysis/verifier-output/checks.yaml"],
    )
    checks = {
        name: {"passed": True, "evidence_paths": item["evidence_paths"]}
        for name in [
            "independent-recomputation",
            "units",
            "constraints",
            "convergence",
            "fairness",
            "statistical-precision",
            "sensitivity",
            "ablations",
        ]
    }
    script = "import argparse,json,pathlib\np=argparse.ArgumentParser();p.add_argument('--project');p.add_argument('--output-dir');a=p.parse_args();d=pathlib.Path(a.output_dir)\nassert 1+2==3\n"
    script += "(d/'verification.yaml').write_text(" + repr(json.dumps([item])) + ")\n"
    script += "(d/'checks.yaml').write_text(" + repr(json.dumps(checks)) + ")\n"
    (repo / "independent.py").write_text(script, newline="\n")
    (repo / "source.py").write_text(
        "import argparse,json,pathlib\nfrom lab.simulation import builtin_run\n"
        "p=argparse.ArgumentParser();p.add_argument('--seed',type=int);p.add_argument('--output-dir');p.add_argument('--params');a=p.parse_args()\n"
        "builtin_run({'trials':1000,'params':json.loads(a.params)},a.seed,pathlib.Path(a.output_dir))\n",
        newline="\n",
    )
    save(fixture / "sim/protocol.yaml", spec)
    save(fixture / "model/predictions.yaml", [{"id": "T1"}])
    commit(fixture)
    simulation.lock(fixture)
    simulation.run(fixture)
    result = verification.custom_verify(fixture, spec, [{"id": "T1"}])
    assert result["status"] == "PASS"
    assert "analysis/verification.yaml" in result["input_hashes"]
    items = load(fixture / "analysis/verification.yaml")
    items[0]["value"] = 999
    save(fixture / "analysis/verification.yaml", items)
    with pytest.raises(LabError, match="changed"):
        verification.validate_verification(fixture)


def test_custom_verifier_rejects_simulator_import(fixture):
    from lab import verification

    spec = load(fixture / "sim/protocol.yaml")
    spec.update(entrypoint="source.py", verification_entrypoint="independent.py")
    spec["inputs"].append("independent.py")
    (fixture.parents[1] / "independent.py").write_text(
        "from lab.simkit import wireless\n", newline="\n"
    )
    save(fixture / "sim/protocol.yaml", spec)
    commit(fixture)
    simulation.lock(fixture)
    with pytest.raises(LabError, match="must not import"):
        verification.custom_verify(fixture, spec, [])
