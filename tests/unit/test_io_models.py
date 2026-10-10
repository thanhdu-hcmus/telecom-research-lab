import pytest
from typer.testing import CliRunner

from lab.cli import app
from lab.io import LabError, load, safe_id, save, within
from lab.models import ResearchState


def test_path_escape_and_windows_names(tmp_path):
    with pytest.raises(LabError):
        within(tmp_path, "../outside")
    assert safe_id("doi:10.1/a/b") != safe_id("doi:10.1/a:b")
    assert safe_id("CON").startswith("r_")


def test_serialization(tmp_path):
    for name in ["a.yaml", "a.json"]:
        path = tmp_path / name
        save(path, {"text": "RIS λ", "count": 3})
        assert load(path) == {"text": "RIS λ", "count": 3}


def test_state_rejects_unknown_fields():
    with pytest.raises(ValueError):
        ResearchState(project="test", gates={}, secretly_approved=True)


def test_cli_help():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "doctor" in result.stdout
