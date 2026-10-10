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
