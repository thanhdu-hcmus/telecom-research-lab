import pytest

from lab.baseline import agreement, scan, score
from lab.io import LabError
from lab.modeling import expression, symbolic_checks


def test_baseline_scan_and_agreement(tmp_path):
    (tmp_path / "evil.py").write_text(
        "import requests, subprocess\nimport os\nos.remove('/outside')\neval('x')\nopen('.aws/config')\n",
        newline="\n",
    )
    (tmp_path / "plugin.dll").write_bytes(b"synthetic")
    assert {x["category"] for x in scan(tmp_path)["findings"]} == {
        "network",
        "process",
        "delete",
        "dynamic-code",
        "credential-access",
        "binary",
    }
    assert agreement([1, 2, 3], [1.01, 2.01, 3.01])["passed"]
    assert not agreement([1, 2, 3], [1, 2, 4])["passed"]
    assert agreement([1, 2, 3], [1.1, 2.1, 3.1], "db")["passed"]
    assert not score({"tutorial": True, "venue_tier": "transactions_jsac", "citations": 1000})[
        "accepted"
    ]
    assert (
        score({"venue_tier": "transactions_jsac", "citations": 20, "paper_year": 2020}, 2026)[
            "points"
        ]["citations"]
        == 1
    )


def test_baseline_configuration_controls_scores_and_agreement():
    from lab.baseline import baseline_policy

    policy = baseline_policy().copy()
    policy["venue_points"] = {"transactions_jsac": 7}
    policy["citation_thresholds"] = [{"per_year": 2, "points": 4}]
    policy["official_repo_points"] = 3
    policy["license_points"] = 2
    policy["maintained_or_selfcontained_points"] = 4
    result = score(
        dict(
            venue_tier="transactions_jsac",
            citations=20,
            paper_year=2020,
            official_link_evidence="source",
            license_permits_research=True,
            license_evidence="MIT",
            self_contained_evidence="No data needed",
        ),
        2026,
        policy=policy,
    )
    assert result["points"] == dict(venue=7, citations=4, official=3, license=2, maintenance=4)
    assert not result["accepted"]  # A preview still cannot replace executed evidence.
    policy["agreement"] = dict(relative=0.2, absolute_db=0.01, require_same_ordering=False)
    assert agreement([1, 2], [1.1, 2.3], policy=policy)["passed"]
    assert not agreement([1, 2], [1.1, 2.1], "db", policy=policy)["passed"]
    assert agreement([1, 1.01], [1.01, 1], policy=policy)["passed"]
    policy["agreement"]["require_same_ordering"] = True
    assert not agreement([1, 1.01], [1.01, 1], policy=policy)["passed"]
    policy["agreement"]["relative"] = float("nan")
    with pytest.raises(LabError, match="finite"):
        agreement([1, 2], [1, 2], policy=policy)


def test_baseline_environment_records_resolved_versions_and_runtime(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace

    from lab import baseline
    from lab.io import load, save, sha256

    folder = tmp_path / "baseline"
    folder.mkdir()
    (folder / "requirements.txt").write_text("numpy>=2\n", encoding="utf-8")
    review = tmp_path / "review.yaml"
    save(
        review,
        dict(
            reviewed_files={"requirements.txt": sha256(folder / "requirements.txt")},
            source_reviewed=True,
            dependencies_reviewed=True,
            license_permits_research=True,
            data_permitted=True,
            uv_executable="fixture-uv",
        ),
    )
    commands = []

    def run(argv, **kwargs):
        commands.append(argv)
        if argv[1:3] == ["pip", "freeze"]:
            return SimpleNamespace(stdout="numpy==2.4.0\n")
        if "-c" in argv:
            return SimpleNamespace(
                stdout=json.dumps(dict(python="synthetic runtime", platform="fixture"))
            )
        if argv[1] == "venv":
            (folder / ".venv").mkdir()
        return SimpleNamespace(stdout="")

    monkeypatch.setattr(baseline.subprocess, "run", run)
    result = baseline.environment(folder, review)
    receipt = load(folder / ".venv/lab-environment.json")
    assert receipt["resolved_sha256"] == sha256(folder / ".venv/lab-resolved-requirements.txt")
    assert receipt["runtime"]["python"] == "synthetic runtime"
    assert result["receipt_sha256"] == sha256(folder / ".venv/lab-environment.json")
    assert any(c[1:3] == ["pip", "freeze"] and "--python" in c for c in commands)


def test_safe_symbolic_checks():
    assert (
        symbolic_checks(
            {
                "symbols": {"x": {"real": True}},
                "checks": [
                    {
                        "id": "a",
                        "kind": "identity",
                        "expression": "(x+1)**2",
                        "expected": "x**2+2*x+1",
                    },
                    {
                        "id": "b",
                        "kind": "hessian",
                        "expression": "x**2",
                        "variables": ["x"],
                        "curvature": "convex",
                    },
                ],
            }
        )["status"]
        == "PASS"
    )
    assert (
        symbolic_checks(
            {
                "symbols": {"x": {"real": True}, "y": {"real": True}},
                "checks": [
                    {
                        "id": "b",
                        "kind": "hessian",
                        "expression": "x*y",
                        "variables": ["x", "y"],
                        "curvature": "convex",
                    }
                ],
            }
        )["status"]
        == "FAIL"
    )
    for bad in ["__import__('os').system('dir')", "x.__class__", "2**99999999"]:
        with pytest.raises(LabError):
            expression(bad, {})


@pytest.mark.parametrize("filename", ["repo/../../escape.py", "repo/../escape.py"])
def test_baseline_archive_escape_refused(tmp_path, monkeypatch, filename):
    import io
    import zipfile

    from lab import baseline

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr(filename, "# untrusted fixture")
    commit = "a" * 40

    class Network:
        def __init__(self, *_):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def get(self, url):
            from types import SimpleNamespace

            return SimpleNamespace(content=buffer.getvalue(), json=lambda: {"sha": commit})

    monkeypatch.setattr(baseline, "Network", Network)
    with pytest.raises(LabError, match="escapes"):
        baseline.clone(tmp_path, "fixture/repo", commit)
    assert not list(tmp_path.rglob("escape.py"))
