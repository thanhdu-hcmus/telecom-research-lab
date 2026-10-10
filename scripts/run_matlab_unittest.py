"""Run R2021b's standard test runner and retain a separate acceptance receipt."""

import subprocess
from pathlib import Path

from lab.io import load, now, save, sha256

ROOT = Path(__file__).resolve().parents[1]
matlab = Path(load(ROOT / "config/lab.config.yaml")["matlab_root"]) / "bin/matlab.exe"
code = (
    f"addpath('{(ROOT / 'matlab').as_posix()}'); "
    f"addpath('{(ROOT / 'tests/matlab').as_posix()}'); "
    "results=runtests('test_simkit_physics.m'); "
    "assert(numel(results)==8 && all([results.Passed]) && ~any([results.Incomplete])); "
    "fprintf('MATLAB_UNITTEST_PASS tests=%d release=%s\\n',numel(results),version('-release'));"
)
result = subprocess.run([str(matlab), "-batch", code], capture_output=True, text=True, timeout=240)
passed = result.returncode == 0 and "MATLAB_UNITTEST_PASS tests=8 release=2021b" in result.stdout
save(
    ROOT / "docs/evidence/post-m10-matlab-unittest.json",
    {
        "status": "PASS" if passed else "FAIL",
        "timestamp": now(),
        "exit": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": [str(matlab), "-batch", code],
        "tests_passed": 8 if passed else 0,
        "source_hashes": {
            p.relative_to(ROOT).as_posix(): sha256(p)
            for p in [
                Path(__file__),
                ROOT / "tests/matlab/test_simkit_physics.m",
                *(ROOT / "matlab/+simkit").glob("*.m"),
            ]
        },
    },
)
print({"status": "PASS" if passed else "FAIL", "exit": result.returncode})
raise SystemExit(not passed)
