"""Run the actual MATLAB mirror; nonzero MATLAB exits are failures."""

import subprocess
from pathlib import Path
from lab.io import load, save, sha256, now

ROOT = Path(__file__).resolve().parents[1]
matlab = Path(load(ROOT / "config/lab.config.yaml")["matlab_root"]) / "bin/matlab.exe"
code = f"addpath('{(ROOT / 'matlab').as_posix()}'); addpath('{(ROOT / 'tests/matlab').as_posix()}'); physics_suite;"
result = subprocess.run([str(matlab), "-batch", code], capture_output=True, text=True, timeout=240)
passed = result.returncode == 0 and "MATLAB_PHYSICS_PASS" in result.stdout
save(
    ROOT / "docs/evidence/m8-matlab-physics.json",
    {
        "status": "PASS" if passed else "FAIL",
        "timestamp": now(),
        "exit": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "source_hashes": {
            p.relative_to(ROOT).as_posix(): sha256(p)
            for p in [ROOT / "tests/matlab/physics_suite.m", *(ROOT / "matlab/+simkit").glob("*.m")]
        },
    },
)
print({"status": "PASS" if passed else "FAIL", "exit": result.returncode})
raise SystemExit(not passed)
