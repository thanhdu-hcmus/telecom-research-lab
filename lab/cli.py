"""Small JSON outputs and consistent nonzero failures for agent-facing commands."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from lab import doctor
from lab.io import LabError, root

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)


@app.callback()
def main():
    """Telecom Research Lab: deterministic tooling with PI research gates."""


def emit(value):
    typer.echo(json.dumps(value, ensure_ascii=False, default=str))


def execute(function, *args, **kwargs):
    try:
        result = function(*args, **kwargs)
        emit(result)
        if isinstance(result, dict) and result.get("status") == "FAIL":
            raise typer.Exit(1)
        return result
    except (LabError, OSError, ValueError) as error:
        emit({"status": "FAIL", "error": str(error)})
        raise typer.Exit(1) from error


@app.command()
def doctor_command(full: bool = False, repo: Path | None = typer.Option(None, "--root"),
                   json_output: bool = typer.Option(False, "--json")):
    """Check tooling and schema alignment; --full repeats M0 integrations."""
    execute(doctor.check, repo.resolve() if repo else root(), full)


# Keep the public command name independent of the Python implementation name.
app.registered_commands[-1].name = "doctor"

from lab import cli_literature as cli_literature  # noqa: E402
from lab import cli_state as cli_state  # noqa: E402


@app.command("eval")
def evaluate(name: str, json_output: bool = typer.Option(False, "--json")):
    """Run three real Codex trials and deterministic grading; uses Plus login."""
    from lab.evaluation import run
    execute(run, root(), name)


@app.command("provenance")
def provenance(project: Annotated[str, typer.Option("--project")], summary: str, file: list[str] = typer.Option([], "--file"),
               tag: str = "ai", json_output: bool = typer.Option(False, "--json")):
    from lab import state
    execute(state.provenance, state.project(root(), project), summary, file, tag)
