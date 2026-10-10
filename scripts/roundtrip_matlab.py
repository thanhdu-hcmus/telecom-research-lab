"""Actual MAT v7 data exchange through MCP and batch; never pretend a tool ran."""

import json
import subprocess
import shutil
import uuid
from pathlib import Path
import numpy as np
from scipy.io import savemat, loadmat
from lab.io import load, save, sha256
from lab.matlab import evaluate
from lab.simulation import matlab_run

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / (".cache/matlab-roundtrip-" + uuid.uuid4().hex[:8])
folder.mkdir(parents=True, exist_ok=True)
x = np.array([[1.0, 2.0], [3.0, 4.0]])
savemat(folder / "input.mat", {"x": x})
reports = {}
for route in ["mcp", "batch"]:
    target = folder / (route + ".mat")
    code = f"s=load('{(folder / 'input.mat').as_posix()}'); y=s.x.^2+eye(2); save('{target.as_posix()}','y','-v7'); fprintf('MATLAB_ROUNDTRIP_PASS\\n');"
    if route == "mcp":
        receipt = evaluate(ROOT, code)
    else:
        executable = Path(load(ROOT / "config/lab.config.yaml")["matlab_root"]) / "bin/matlab.exe"
        result = subprocess.run(
            [str(executable), "-batch", code], capture_output=True, text=True, timeout=180
        )
        receipt = {"exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        if result.returncode:
            raise RuntimeError("MATLAB batch nonzero exit; retained data is not acceptance")
    actual = loadmat(target)["y"]
    reports[route] = {
        "passed": bool(np.array_equal(actual, x**2 + np.eye(2))),
        "output_sha256": sha256(target),
        "runtime": receipt,
    }
    isolated = folder / (route + "-repo")
    (isolated / ".codex").mkdir(parents=True)
    shutil.copyfile(ROOT / ".codex/config.toml", isolated / ".codex/config.toml")
    config = load(ROOT / "config/lab.config.yaml")
    config["matlab_route"] = route
    save(isolated / "config/lab.config.yaml", config)
    output = isolated / "run"
    output.mkdir()
    savemat(output / "input.mat", {"x": x})
    script = isolated / "bridge_fixture.m"
    script.write_text(
        "function bridge_fixture(seed, output_dir)\nparams=jsondecode(fileread(fullfile(output_dir,'params.json')));\ns=load(fullfile(output_dir,'input.mat')); y=s.x.^2+params.offset*eye(2);\nassert(seed==42);save(fullfile(output_dir,'result.mat'),'y','-v7');\nend\n",
        encoding="utf-8",
        newline="\n",
    )
    environment = matlab_run(isolated, script, 42, output, {"offset": 1})
    assert np.array_equal(loadmat(output / "result.mat")["y"], x**2 + np.eye(2))
    assert environment["release"] == "2021b" and environment["toolboxes"]
    reports[route]["dispatch"] = {
        "passed": True,
        "environment": environment,
        "output_sha256": sha256(output / "result.mat"),
    }
save(
    ROOT / "docs/evidence/m8-matlab-roundtrip.json",
    {
        "status": "PASS" if all(r["passed"] for r in reports.values()) else "FAIL",
        "routes": reports,
        "source_sha256": sha256(Path(__file__)),
    },
)
print(
    json.dumps(
        {
            "status": "PASS" if all(r["passed"] for r in reports.values()) else "FAIL",
            "routes": {k: v["passed"] for k, v in reports.items()},
        }
    )
)
