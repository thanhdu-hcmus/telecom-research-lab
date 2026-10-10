"""Small JSON outputs and consistent nonzero failures for agent-facing commands."""

from __future__ import annotations

import inspect
import json
import subprocess
from functools import wraps
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
    except (
        LabError,
        OSError,
        ValueError,
        KeyError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as error:
        emit({"status": "FAIL", "error": str(error)})
        raise typer.Exit(1) from error


@app.command()
def doctor_command(
    full: bool = False,
    repo: Path | None = typer.Option(None, "--root"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Check tooling and schema alignment; --full repeats M0 integrations."""
    execute(doctor.check, repo.resolve() if repo else root(), full)


# Keep the public command name independent of the Python implementation name.
app.registered_commands[-1].name = "doctor"

from lab import cli_literature as cli_literature  # noqa: E402
from lab import cli_paper as cli_paper  # noqa: E402
from lab import cli_research as cli_research  # noqa: E402
from lab import cli_state as cli_state  # noqa: E402


@app.command("eval")
def evaluate(name: str, json_output: bool = typer.Option(False, "--json")):
    """Run three real Codex trials and deterministic grading; uses Plus login."""
    from lab.evaluation import run

    execute(run, root(), name)


@app.command("provenance")
def provenance(
    project: Annotated[str, typer.Option("--project")],
    summary: str,
    file: list[str] = typer.Option([], "--file"),
    tag: str = "ai",
    json_output: bool = typer.Option(False, "--json"),
):
    from lab import state

    execute(state.provenance, state.project(root(), project), summary, file, tag)


def install_json_options(group):
    """All leaf commands accept --json and preserve their typed public signature."""
    for command in group.registered_commands:
        original = command.callback
        signature = inspect.signature(original)
        needs_flag = "json_output" not in signature.parameters

        def wrap(callback, needs):
            @wraps(callback)
            def invoke(*args, **kwargs):
                if needs:
                    kwargs.pop("json_output", None)
                try:
                    return callback(*args, **kwargs)
                except (
                    LabError,
                    OSError,
                    ValueError,
                    KeyError,
                    subprocess.CalledProcessError,
                    subprocess.TimeoutExpired,
                ) as error:
                    emit({"status": "FAIL", "error": str(error)})
                    raise typer.Exit(1) from error

            return invoke

        callback = wrap(original, needs_flag)
        if needs_flag:
            callback.__signature__ = signature.replace(
                parameters=[
                    *signature.parameters.values(),
                    inspect.Parameter(
                        "json_output",
                        inspect.Parameter.KEYWORD_ONLY,
                        annotation=bool,
                        default=typer.Option(False, "--json"),
                    ),
                ]
            )
        command.callback = callback
    for child in group.registered_groups:
        install_json_options(child.typer_instance)


install_json_options(app)
