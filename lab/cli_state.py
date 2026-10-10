from pathlib import Path

import typer

from lab import state
from lab.cli import app, emit, execute
from lab.io import load, root

project_app = typer.Typer()
phase_app = typer.Typer()
gate_app = typer.Typer()
deviation_app = typer.Typer()
app.add_typer(project_app, name="project")
app.add_typer(phase_app, name="phase")
app.add_typer(gate_app, name="gate")
app.add_typer(deviation_app, name="deviation")


def locate(slug: str) -> Path:
    return state.project(root(), slug)


@project_app.command("init")
def init(slug: str, json_output: bool = typer.Option(False, "--json")):
    execute(state.init, root(), slug)


@project_app.command("status")
def status(project: str, json_output: bool = typer.Option(False, "--json")):
    execute(state.state, locate(project))


@phase_app.command("start")
def phase_start(phase: str, project: str, json_output: bool = typer.Option(False, "--json")):
    execute(state.enter, locate(project), phase)


@phase_app.command("current")
def current(project: str, json_output: bool = typer.Option(False, "--json")):
    emit({"phase": state.state(locate(project))["phase"]})


@gate_app.command("request")
def request(gate: str, project: str, json_output: bool = typer.Option(False, "--json")):
    execute(state.request, locate(project), gate)


@gate_app.command("require")
def require(gate: str, project: str, json_output: bool = typer.Option(False, "--json")):
    execute(state.require, locate(project), gate)


@gate_app.command("status")
def gate_status(project: str, json_output: bool = typer.Option(False, "--json")):
    emit(state.state(locate(project))["gates"])


@gate_app.command("approve")
def approve(gate: str, project: str, note: str, select: str | None = None,
            json_output: bool = typer.Option(False, "--json")):
    execute(state.decide, locate(project), gate, "approve", note, select)


@gate_app.command("revise")
def revise(gate: str, project: str, note: str,
           json_output: bool = typer.Option(False, "--json")):
    execute(state.decide, locate(project), gate, "revise", note)


@gate_app.command("rewind")
def rewind(phase: str, project: str, note: str,
           json_output: bool = typer.Option(False, "--json")):
    execute(state.rewind, locate(project), phase, note)


@deviation_app.command("open")
def deviation_open(project: str, what: str, why: str, proposed_change: str, impact: str,
                   json_output: bool = typer.Option(False, "--json")):
    execute(state.deviation_open, locate(project), what, why, proposed_change, impact)


@deviation_app.command("list")
def deviation_list(project: str, json_output: bool = typer.Option(False, "--json")):
    emit(load(locate(project) / "deviations.yaml", []))


@deviation_app.command("resolve")
def resolve(identifier: str, project: str, decision: str, note: str,
            json_output: bool = typer.Option(False, "--json")):
    execute(state.deviation_resolve, locate(project), identifier, decision, note)
