import json

from typer.testing import CliRunner

from lab.cli import app


def test_new_commands_support_json_and_clear_errors():
    runner = CliRunner()
    for group, command in [
        ("ideas", "rank"),
        ("model", "check"),
        ("sim", "status"),
        ("paper", "trace"),
        ("cite", "verify"),
    ]:
        result = runner.invoke(app, [group, command, "--project", "missing-project", "--json"])
        assert result.exit_code == 1
        assert json.loads(result.output)["status"] == "FAIL"


def test_documented_required_flags_parse_without_executing_a_decision(monkeypatch):
    from pathlib import Path

    from lab import cli_state, state

    runner = CliRunner()
    path = Path("fixture-project")
    monkeypatch.setattr(cli_state, "locate", lambda _: path)
    calls = []

    def capture(*args):
        calls.append(args)
        return {"status": "PASS"}

    monkeypatch.setattr(state, "decide", capture)
    result = runner.invoke(
        app,
        ["gate", "approve", "G3", "--project", "fixture", "--note", "Reviewed", "--select", "R1"],
    )
    assert result.exit_code == 0, result.output
    assert calls[-1] == (path, "G3", "approve", "Reviewed", "R1")
    monkeypatch.setattr(state, "deviation_open", capture)
    result = runner.invoke(
        app,
        [
            "deviation",
            "open",
            "--project",
            "fixture",
            "--what",
            "Metric",
            "--why",
            "Review",
            "--proposed-change",
            "New metric",
            "--impact",
            "Fresh gate",
        ],
    )
    assert result.exit_code == 0, result.output
    monkeypatch.setattr(state, "project", lambda *_: path)
    monkeypatch.setattr(state, "provenance", capture)
    result = runner.invoke(
        app,
        ["provenance", "--project", "fixture", "--summary", "AI scope draft", "--file", "scope.md"],
    )
    assert result.exit_code == 0, result.output
    assert calls[-1] == (path, "AI scope draft", ["scope.md"], "ai")
