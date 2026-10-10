from pathlib import Path
from typing import Annotated

import typer

from lab import citations, figures, paper
from lab.cli import app, execute
from lab.io import root, within
from lab.state import ensure_phase, project

cite_app = typer.Typer(no_args_is_help=True)
paper_app = typer.Typer(no_args_is_help=True)
fig_app = typer.Typer(no_args_is_help=True)
app.add_typer(cite_app, name="cite")
app.add_typer(paper_app, name="paper")
app.add_typer(fig_app, name="fig")


@cite_app.command("verify")
def cite_verify(project_name: Annotated[str, typer.Option("--project")]):
    execute(citations.verify, project(root(), project_name))


@cite_app.command("bib-from")
def bib_from(ids: list[str], project_name: Annotated[str, typer.Option("--project")]):
    path = project(root(), project_name)
    ensure_phase(path, "P7")
    execute(citations.bib_from, path, ids)


@fig_app.command("make")
def fig_make(spec: Path, project_name: Annotated[str, typer.Option("--project")]):
    path = project(root(), project_name)
    ensure_phase(path, "P7")
    execute(figures.make, path, within(path, spec))


@paper_app.command("init")
def paper_init(project_name: Annotated[str, typer.Option("--project")], style: str = "journal"):
    execute(paper.init, project(root(), project_name), style)


@paper_app.command("build")
def build(project_name: Annotated[str, typer.Option("--project")]):
    execute(paper.build, project(root(), project_name))


@paper_app.command("trace")
def trace(project_name: Annotated[str, typer.Option("--project")]):
    execute(paper.trace, project(root(), project_name))


@paper_app.command("overlap")
def overlap(project_name: Annotated[str, typer.Option("--project")]):
    execute(paper.overlap, project(root(), project_name))


@paper_app.command("export")
def export(project_name: Annotated[str, typer.Option("--project")]):
    path = project(root(), project_name)
    ensure_phase(path, "P7")
    execute(paper.export, path)


@paper_app.command("disclosure")
def disclosure(project_name: Annotated[str, typer.Option("--project")]):
    path = project(root(), project_name)
    ensure_phase(path, "P7")
    execute(paper.disclosure, path)
