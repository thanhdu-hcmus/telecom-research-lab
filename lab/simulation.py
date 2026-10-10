"""Immutable protocol receipts, resumable seed jobs and checksum manifests."""

from __future__ import annotations

import csv
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from filelock import FileLock

from lab import state
from lab.io import LabError, git, library, load, now, safe_id, save, sha256, within
from lab.models import RunManifest
from lab.simkit import wireless as w


def protocol(path):
    spec = load(path / "sim/protocol.yaml")
    required = ["version", "scenarios", "metrics", "fairness", "trial_policy", "inputs", "language"]
    if any(not spec.get(k) for k in required) or spec["language"] not in {"python", "matlab"}:
        raise LabError("Protocol needs scenarios, metrics, fairness, trials, inputs and language")
    fair = spec["fairness"]
    if not all(
        fair.get(k) is True
        for k in ["same_power", "same_bandwidth", "same_csi", "common_channels", "same_qos"]
    ):
        raise LabError("Fair comparison contract missing")
    policy = spec["trial_policy"]
    if policy.get("relative_ci_halfwidth", 1) > 0.01 or policy.get("minimum_events", 0) < 100:
        raise LabError("Default trial policy: <=1% average halfwidth and >=100 outage events")
    ids = []
    for scenario in spec["scenarios"]:
        ids.append(scenario["id"])
        seeds = scenario.get("seeds", [])
        if (
            not seeds
            or len(set(seeds)) != len(seeds)
            or any(type(s) is not int or s < 0 for s in seeds)
        ):
            raise LabError("Unique nonnegative integer seeds required")
        if scenario.get("trials", 0) < 100:
            raise LabError("Scenario needs at least 100 trials")
        if not scenario.get("params"):
            raise LabError("Explicit scenario parameters required")
    if len(set(ids)) != len(ids):
        raise LabError("Duplicate scenarios")
    if spec.get("dl"):
        dl = spec["dl"]
        splits = [set(dl.get(k, [])) for k in ["train_ids", "validation_ids", "test_ids"]]
        if (
            not all(splits)
            or any(splits[i] & splits[j] for i, j in [(0, 1), (0, 2), (1, 2)])
            or len(set(dl.get("training_seeds", []))) < 3
        ):
            raise LabError("DL requires disjoint splits and at least three training seeds")
    return spec


def inputs(path, spec):
    repo = path.parents[1]
    names = [
        path / "sim/protocol.yaml",
        path / "sim/protocol.md",
        *[within(repo, n) for n in spec["inputs"]],
    ]
    names.extend(sorted((repo / "lab").rglob("*.py")))
    names.extend(sorted((repo / "matlab").rglob("*.m")))
    names.append(repo / "uv.lock")
    if not (repo / "lab/simulation.py").exists():
        raise LabError("Framework source must be included in the project Git repository")
    return {p.relative_to(repo).as_posix(): sha256(p) for p in names}


def locked(path):
    repo = path.parents[1]
    spec = protocol(path)
    lock = load(path / "sim/lock.json")
    if (
        inputs(path, spec) != lock["input_hashes"]
        or sha256(path / "sim/protocol.yaml") != lock["protocol_hash"]
    ):
        raise LabError(
            "Locked protocol/input changed: file a PI deviation and request fresh review"
        )
    commit = lock["protocol_commit"]
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise LabError("Malformed protocol commit")
    # Require a real ancestor and byte-identical committed inputs, not a supplied SHA string.
    git(repo, "merge-base", "--is-ancestor", commit, "HEAD")
    for name, digest in lock["input_hashes"].items():
        blob = git(repo, "rev-parse", f"{commit}:{name}")
        actual = git(repo, "hash-object", str(repo / name))
        if blob != actual:
            raise LabError("Protocol commit does not contain current locked input")
        if git(repo, "status", "--porcelain", "--", name):
            raise LabError("Locked input is dirty")
    return spec, lock


def lock(path):
    state.ensure_phase(path, "P5")
    if (path / "sim/lock.json").exists():
        locked(path)
        return {"status": "PASS", "already_locked": True}
    spec = protocol(path)
    repo = path.parents[1]
    hashes = inputs(path, spec)
    for name in hashes:
        if git(repo, "status", "--porcelain", "--", name):
            raise LabError(
                "Commit the reviewed protocol and input sources before locking; dirty/untracked input refused"
            )
        git(repo, "ls-files", "--error-unmatch", name)
    commit = git(repo, "rev-parse", "HEAD")
    value = {
        "protocol_commit": commit,
        "protocol_hash": sha256(path / "sim/protocol.yaml"),
        "input_hashes": hashes,
        "locked_at": now(),
    }
    save(path / "sim/lock.json", value)
    st = state.state(path)
    st["protocol_hash"] = value["protocol_hash"]
    st["protocol_commit"] = commit
    state.update(path, st)
    return {"status": "PASS", **value}


def relock(path, reason, deviation=None):
    """Archive old runs, then lock a committed code fix or PI-approved protocol change."""
    state.ensure_phase(path, "P5")
    if not reason.strip():
        raise LabError("Explain the code fix or approved change")
    old = load(path / "sim/lock.json")
    repo = path.parents[1]
    spec = protocol(path)
    current = inputs(path, spec)
    changed = {
        name
        for name in set(current) | set(old["input_hashes"])
        if current.get(name) != old["input_hashes"].get(name)
    }
    if not changed:
        raise LabError("No changed input to relock")
    code_only = all(Path(name).suffix in {".py", ".m"} for name in changed)
    if not code_only:
        approved = [
            d
            for d in load(path / "deviations.yaml", [])
            if d.get("id") == deviation and d.get("status") == "approved"
        ]
        if len(approved) != 1:
            raise LabError(
                "Changed protocol, data, environment or metrics need an approved PI deviation"
            )
    for name in current:
        if git(repo, "status", "--porcelain", "--", name):
            raise LabError("Commit reviewed changed inputs before relocking")
    archive = within(path, "results/archive/" + safe_id(now() + old["protocol_hash"]))
    archive.mkdir(parents=True)
    for name in ["results/runs", "results/summary.csv", "results/collection.json", "sim/lock.json"]:
        source = within(path, name)
        if source.exists():
            target = within(archive, Path(name).name)
            source.rename(target)
    save(
        archive / "change.json",
        {
            "reason": reason,
            "deviation": deviation,
            "code_only": code_only,
            "changed": sorted(changed),
            "old_input_hashes": old["input_hashes"],
        },
    )
    state.invalidate(path, state.state(path), 5, "Relock: " + reason)
    result = lock(path)
    state.log(path, "Archived previous runs before relock; " + reason)
    return {**result, "archived": str(archive), "requires_fresh_G5": True}


def output_path(path, output):
    storage = output.storage if hasattr(output, "storage") else output.get("storage", "project")
    name = output.path if hasattr(output, "path") else output["path"]
    return within(library(path.parents[1]) if storage == "library" else path, name)


def manifest_output(path, manifest, filename):
    matches = [o for o in manifest.outputs if Path(o.path).name == filename]
    if len(matches) != 1:
        raise LabError("Expected exactly one manifest output named " + filename)
    return output_path(path, matches[0])


def verify_manifest(path, manifest):
    m = RunManifest.model_validate(manifest)
    spec, lock = locked(path)
    if (
        m.status != "complete"
        or m.protocol_hash != lock["protocol_hash"]
        or m.protocol_commit != lock["protocol_commit"]
        or m.input_hashes != lock["input_hashes"]
    ):
        raise LabError("Manifest does not match locked protocol")
    git(path.parents[1], "merge-base", "--is-ancestor", m.protocol_commit, m.git_sha)
    git(path.parents[1], "merge-base", "--is-ancestor", m.git_sha, "HEAD")
    scenarios = [s for s in spec["scenarios"] if s["id"] == m.scenario]
    if (
        len(scenarios) != 1
        or len(m.seeds) != 1
        or m.seeds[0] not in scenarios[0]["seeds"]
        or m.params != scenarios[0]["params"]
        or m.language != spec["language"]
    ):
        raise LabError("Manifest parameters/seeds/language differ from planned scenario")
    if len({(o.path, o.storage) for o in m.outputs}) != len(m.outputs):
        raise LabError("Duplicate manifest outputs")
    for output in m.outputs:
        p = output_path(path, output)
        if not p.is_file() or sha256(p) != output.sha256 or p.stat().st_size != output.bytes:
            raise LabError("Run output missing or changed")
    return m


def builtin_run(scenario, seed, folder):
    def write_csv(name, values, header):
        with (folder / name).open("w", encoding="utf-8", newline="\n") as stream:
            np.savetxt(stream, values, delimiter=",", header=header, comments="")

    gains = np.sort(w.streams(seed)["channel"].exponential(size=(scenario["trials"], 2)), axis=1)
    write_csv("channels.csv", gains, "weak,strong")
    params = scenario["params"]
    rho = params["rho_linear"]
    a = params["a_weak"]
    weak, sic, strong = w.noma_sinr(gains[:, 0], gains[:, 1], rho, a, params.get("sic_residual", 0))
    rw = w.rates(weak)
    rs = w.rates(strong)
    # Same total power and full bandwidth split evenly in time for OMA.
    oma = 0.5 * w.rates(rho * gains[:, 0]) + 0.5 * w.rates(rho * gains[:, 1])
    gamma_weak = 2 ** params["target_rate_weak"] - 1
    gamma_strong = 2 ** params["target_rate_strong"] - 1
    raw = np.column_stack(
        [
            rw + rs,
            oma,
            (weak < gamma_weak).astype(int),
            ((sic < gamma_weak) | (strong < gamma_strong)).astype(int),
        ]
    )
    write_csv("metrics.csv", raw, "noma_sumrate,oma_sumrate,weak_outage,strong_outage")
    grid = np.linspace(0, float(np.max(raw[:, :2])), 200)
    cdfs = np.column_stack(
        [
            grid,
            np.searchsorted(np.sort(raw[:, 0]), grid, side="right") / len(raw),
            np.searchsorted(np.sort(raw[:, 1]), grid, side="right") / len(raw),
        ]
    )
    write_csv("cdf.csv", cdfs, "rate,nomacdf,omacdf")


def matlab_run(repo, script, seed, folder, params):
    config = load(repo / "config/lab.config.yaml")
    executable = Path(config["matlab_root"]) / "bin/matlab.exe"
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", script.stem):
        raise LabError("MATLAB entry must be a function with a plain identifier")

    def q(p):
        return p.resolve().as_posix().replace("'", "''")

    save(folder / "params.json", params)
    code = f"p=path; c=onCleanup(@()path(p)); addpath('{q(script.parent)}'); addpath('{q(repo / 'matlab')}'); {script.stem}({seed},'{q(folder)}'); info=struct('version',version,'release',version('-release'),'toolboxes',ver); fid=fopen('{q(folder / 'matlab-environment.json')}','w'); assert(fid~=-1); fwrite(fid,jsonencode(info),'char'); fclose(fid);"
    route = config.get("matlab_route", "mcp")
    if route == "mcp":
        from lab.matlab import evaluate

        save(folder / "matlab-mcp.json", evaluate(repo, code, timeout=1800))
        if not (folder / "matlab-environment.json").is_file():
            raise LabError("MATLAB MCP did not finish the run; inspect saved response")
        return load(folder / "matlab-environment.json")
    if route != "batch":
        raise LabError("matlab_route must be mcp or batch")
    result = subprocess.run(
        [str(executable), "-batch", code], cwd=folder, capture_output=True, text=True, timeout=1800
    )
    (folder / "matlab-stdout.txt").write_text(result.stdout, encoding="utf-8", newline="\n")
    (folder / "matlab-stderr.txt").write_text(result.stderr, encoding="utf-8", newline="\n")
    if result.returncode:
        raise LabError(f"MATLAB batch failed, exit {result.returncode}; inspect saved logs")
    return load(folder / "matlab-environment.json")


def run(path):
    state.ensure_phase(path, "P5")
    spec, lock_value = locked(path)
    repo = path.parents[1]
    results = []
    with FileLock(str(path / "sim/.run.lock"), timeout=1):
        for scenario in spec["scenarios"]:
            for seed in scenario["seeds"]:
                run_id = safe_id(
                    f"{scenario['id']}-{seed}-{lock_value['protocol_hash'][:12]}-{lock_value['protocol_commit'][:12]}"
                )
                folder = path / "results/runs" / run_id
                manifest_file = folder / "manifest.json"
                if manifest_file.exists():
                    verify_manifest(path, load(manifest_file))
                    results.append({"id": run_id, "resumed": True})
                    continue
                if folder.exists() and any(folder.iterdir()):
                    raise LabError(
                        "Incomplete job directory retained; inspect and archive before retry"
                    )
                folder.mkdir(parents=True, exist_ok=True)
                started = now()
                tick = time.monotonic()
                script = spec.get("entrypoint")
                matlab_environment = None
                if not script:
                    if spec["language"] != "python":
                        raise LabError("MATLAB protocol requires entrypoint")
                    builtin_run(scenario, seed, folder)
                else:
                    script = within(repo, script)
                    if script.relative_to(repo).as_posix() not in lock_value["input_hashes"]:
                        raise LabError("Entrypoint must be a locked input")
                    if spec["language"] == "matlab":
                        matlab_environment = matlab_run(
                            repo, script, seed, folder, scenario["params"]
                        )
                    else:
                        env = os.environ.copy()
                        env["PYTHONPATH"] = str(repo)
                        completed = subprocess.run(
                            [
                                sys.executable,
                                str(script),
                                "--seed",
                                str(seed),
                                "--output-dir",
                                str(folder),
                                "--params",
                                json.dumps(scenario["params"]),
                            ],
                            cwd=folder,
                            env=env,
                            capture_output=True,
                            text=True,
                            timeout=1800,
                        )
                        (folder / "stdout.txt").write_text(
                            completed.stdout, encoding="utf-8", newline="\n"
                        )
                        (folder / "stderr.txt").write_text(
                            completed.stderr, encoding="utf-8", newline="\n"
                        )
                        if completed.returncode:
                            raise LabError(
                                "Simulation failed; saved outputs/logs retained, no complete manifest"
                            )
                locked(path)  # Inputs must also be unchanged at completion.
                outputs = []
                limit = load(repo / "config/lab.config.yaml", {"large_result_bytes": 52428800}).get(
                    "large_result_bytes", 52428800
                )
                for p in sorted(folder.rglob("*")):
                    if not p.is_file():
                        continue
                    digest = sha256(p)
                    size = p.stat().st_size
                    if size > limit:
                        base = library(repo)
                        destination = within(
                            base,
                            Path("results") / safe_id(path.name) / run_id / p.relative_to(folder),
                        )
                        if destination.exists():
                            raise LabError(
                                "Large-result destination already exists; never replace evidence"
                            )
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        # Libraries can live on another filesystem; verify before removing source.
                        shutil.copyfile(p, destination)
                        if sha256(destination) != digest or sha256(p) != digest:
                            raise LabError(
                                "Large-result copy changed; preserve both files for review"
                            )
                        p.unlink()
                        outputs.append(
                            {
                                "path": destination.relative_to(base).as_posix(),
                                "storage": "library",
                                "sha256": digest,
                                "bytes": size,
                            }
                        )
                    else:
                        outputs.append(
                            {
                                "path": p.relative_to(path).as_posix(),
                                "storage": "project",
                                "sha256": digest,
                                "bytes": size,
                            }
                        )
                manifest = RunManifest(
                    run_id=run_id,
                    git_sha=git(repo, "rev-parse", "HEAD"),
                    protocol_commit=lock_value["protocol_commit"],
                    protocol_hash=lock_value["protocol_hash"],
                    input_hashes=lock_value["input_hashes"],
                    scenario=scenario["id"],
                    params=scenario["params"],
                    seeds=[seed],
                    language=spec["language"],
                    env={
                        **({"matlab": matlab_environment} if matlab_environment else {}),
                        "python": sys.version,
                        "numpy": np.__version__,
                        "packages": {
                            n: importlib.metadata.version(n) for n in ["scipy", "sympy", "cvxpy"]
                        },
                    },
                    host={"platform": platform.platform(), "machine": platform.machine()},
                    start=started,
                    end=now(),
                    runtime_s=time.monotonic() - tick,
                    outputs=outputs,
                    status="complete",
                )
                save(manifest_file, manifest.model_dump(mode="json"))
                results.append({"id": run_id, "resumed": False})
    return {"status": "PASS", "jobs": results}


def validate_runs(path):
    spec, lock_value = locked(path)
    expected = {(s["id"], seed) for s in spec["scenarios"] for seed in s["seeds"]}
    actual = set()
    for p in (path / "results/runs").glob("*/manifest.json"):
        m = verify_manifest(path, load(p))
        if (m.scenario, m.seeds[0]) in actual:
            raise LabError("Duplicate planned seed job manifests")
        actual.add((m.scenario, m.seeds[0]))
    if expected != actual:
        raise LabError(f"Missing or extra planned jobs: {expected ^ actual}")
    return {"status": "PASS", "completed": len(actual)}


def status(path):
    try:
        return validate_runs(path)
    except LabError as e:
        return {"status": "FAIL", "error": str(e)}


def collect(path):
    validate_runs(path)
    rows = []
    for p in sorted((path / "results/runs").glob("*/manifest.json")):
        m = verify_manifest(path, load(p))
        for out in m.outputs:
            if out.path.endswith("metrics.csv"):
                raw = np.genfromtxt(output_path(path, out), delimiter=",", names=True)
                rows.append(
                    {
                        "run_id": m.run_id,
                        "scenario": m.scenario,
                        "seed": m.seeds[0],
                        **{k: float(np.mean(raw[k])) for k in raw.dtype.names},
                    }
                )
    if not rows:
        raise LabError("No metrics.csv outputs to collect")
    dest = path / "results/summary.csv"
    with dest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    save(
        path / "results/collection.json",
        {
            "summary_sha256": sha256(dest),
            "manifests": {
                p.relative_to(path).as_posix(): sha256(p)
                for p in sorted((path / "results/runs").glob("*/manifest.json"))
            },
        },
    )
    return {"status": "PASS", "rows": len(rows), "summary": str(dest)}
