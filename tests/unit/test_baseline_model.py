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
