"""Commands for idea, model, baseline and simulation artifacts."""

from pathlib import Path
from typing import Annotated

import typer

from lab import baseline, ideas
from lab.cli import app, execute
from lab.io import root
from lab.state import project

idea_app = typer.Typer(no_args_is_help=True)
app.add_typer(idea_app, name="ideas")


@idea_app.command("rank")
def rank(project_name: Annotated[str, typer.Option("--project")]):
    execute(ideas.ranking, project(root(), project_name))


@idea_app.command("sensitivity")
def sensitivity(project_name: Annotated[str, typer.Option("--project")]):
    execute(ideas.ranking, project(root(), project_name), True)


baseline_app = typer.Typer(no_args_is_help=True)
app.add_typer(baseline_app, name="baseline")


@baseline_app.command("clone")
def clone(owner_repo: str, commit: str, project_name: Annotated[str, typer.Option("--project")]):
    from lab.state import ensure_phase

    path = project(root(), project_name)
    ensure_phase(path, "P5")
    execute(baseline.clone, root(), owner_repo, commit)


@baseline_app.command("scan")
def scan(folder: Path):
    from lab.io import within

    execute(baseline.scan, within(root(), folder))


@baseline_app.command("score")
def score(record: Path, project_name: Annotated[str | None, typer.Option("--project")] = None):
    from lab.io import load, within

    execute(
        baseline.score,
        load(within(root(), record)),
        evidence_root=project(root(), project_name) if project_name else None,
    )


@baseline_app.command("env")
def env(folder: Path, review: Path, project_name: Annotated[str, typer.Option("--project")]):
    from lab.io import within
    from lab.state import ensure_phase

    ensure_phase(project(root(), project_name), "P5")
    execute(baseline.environment, within(root(), folder), within(root(), review))


model_app = typer.Typer(no_args_is_help=True)
app.add_typer(model_app, name="model")


@model_app.command("check")
def model_check(project_name: Annotated[str, typer.Option("--project")]):
    from lab import modeling

    execute(modeling.check, project(root(), project_name))


@app.command("review-packet")
def review_packet(phase: str, project_name: Annotated[str, typer.Option("--project")]):
    from lab import modeling

    execute(modeling.review_packet, project(root(), project_name), phase)


sim_app = typer.Typer(no_args_is_help=True)
app.add_typer(sim_app, name="sim")
for _command in ["lock", "run", "status", "collect"]:

    def _sim(project_name: Annotated[str, typer.Option("--project")], _action=_command):
        from lab import simulation

        execute(getattr(simulation, _action), project(root(), project_name))

    # Avoid an accidental public _action parameter in Typer's signature.
    import inspect

    _sim.__signature__ = inspect.Signature(
        [
            inspect.Parameter(
                "project_name",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Annotated[str, typer.Option("--project")],
            )
        ]
    )
    sim_app.command(_command)(_sim)


@sim_app.command("relock")
def relock(
    project_name: Annotated[str, typer.Option("--project")],
    reason: str,
    deviation: str | None = None,
):
    from lab import simulation

    execute(simulation.relock, project(root(), project_name), reason, deviation)


@app.command("verify")
def verify(project_name: Annotated[str, typer.Option("--project")]):
    from lab import verification

    execute(verification.verify, project(root(), project_name))
