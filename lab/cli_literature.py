from pathlib import Path
from typing import Annotated

import typer

from lab import literature, state, venues
from lab.cli import app, execute
from lab.io import LabError, read_jsonl, root, write_jsonl

lit_app = typer.Typer()
venue_app = typer.Typer()
app.add_typer(lit_app, name="lit")
app.add_typer(venue_app, name="venue")


def run_for_project(function, slug, *args, **kwargs):
    repo = root()
    path = state.project(repo, slug)
    state.ensure_phase(path, "P2")
    return function(repo, path, *args, **kwargs)


@lit_app.command("search")
def search(project: Annotated[str, typer.Option("--project")], plan: Path | None = None, json_output: bool = typer.Option(False, "--json")):
    def action(repo, path):
        return literature.run_search(repo, path, plan or path / "literature/query-plan.yaml")
    execute(run_for_project, action, project)


@lit_app.command("snowball")
def snowball(project: Annotated[str, typer.Option("--project")], ids: list[str] = typer.Option(..., "--id"), depth: int = 1,
             json_output: bool = typer.Option(False, "--json")):
    execute(run_for_project, literature.snowball, project, ids, depth)


@lit_app.command("dedup")
def dedup(project: Annotated[str, typer.Option("--project")], json_output: bool = typer.Option(False, "--json")):
    def action(repo, path):
        records, counts = literature.dedup(read_jsonl(path / "literature/candidates.jsonl"))
        write_jsonl(path / "literature/candidates.jsonl", records)
        return {"status": "PASS", "counts": counts}
    execute(run_for_project, action, project)


@lit_app.command("screen-export")
def screen_export(project: Annotated[str, typer.Option("--project")], json_output: bool = typer.Option(False, "--json")):
    execute(run_for_project, lambda repo, path: literature.screen_export(path), project)


@lit_app.command("prisma")
def prisma(project: Annotated[str, typer.Option("--project")], json_output: bool = typer.Option(False, "--json")):
    execute(run_for_project, lambda repo, path: literature.prisma(path), project)


@lit_app.command("fetch")
def fetch(identifier: str, project: Annotated[str, typer.Option("--project")], json_output: bool = typer.Option(False, "--json")):
    def action(repo, path):
        item = next((r for r in read_jsonl(path / "literature/candidates.jsonl") if r["id"] == identifier), None)
        if not item:
            raise LabError("Unknown candidate ID")
        result = literature.fetch(repo, path, item)
        if result["status"] == "PASS":
            from lab.io import library
            write_jsonl(path / "literature/library.jsonl", read_jsonl(library(repo) / "library.jsonl"))
        return result
    execute(run_for_project, action, project)


@lit_app.command("ingest")
def ingest(project: Annotated[str, typer.Option("--project")], inbox: Path | None = None, json_output: bool = typer.Option(False, "--json")):
    execute(run_for_project, literature.ingest, project, inbox)


@lit_app.command("extract")
def extract(identifier: str, project: Annotated[str, typer.Option("--project")], json_output: bool = typer.Option(False, "--json")):
    execute(run_for_project, literature.extract, project, identifier)


@lit_app.command("import")
def import_records(source: Path, project: Annotated[str, typer.Option("--project")], json_output: bool = typer.Option(False, "--json")):
    execute(run_for_project, lambda repo, path: literature.import_metadata(path, source), project)


@venue_app.command("lookup")
def venue_lookup(title: str | None = None, issn: str | None = None, csv_path: Path | None = None,
                 json_output: bool = typer.Option(False, "--json")):
    execute(venues.lookup, root(), title, issn, csv_path)


@venue_app.command("quartile")
def quartile(title: str, csv_path: Path | None = None, json_output: bool = typer.Option(False, "--json")):
    execute(venues.lookup, root(), title, None, csv_path)
