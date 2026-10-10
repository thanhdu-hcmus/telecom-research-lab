"""Build-time helpers: operational skill rewrites and explicit synthetic evals."""

import json
from pathlib import Path
from lab.io import save

ROOT = Path(__file__).resolve().parents[1]


def skill(name, description, body):
    p = ROOT / f".agents/skills/{name}/SKILL.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n{body.strip()}\n",
        encoding="utf-8",
        newline="\n",
    )


def role(name, body):
    p = ROOT / f".codex/agents/{name}.toml"
    text = p.read_text(encoding="utf-8")
    text = text.replace(
        "M1 contract stub: substantive role workflows are enabled in their implementation milestone.",
        body,
    )
    p.write_text(text, encoding="utf-8", newline="\n")


def evaluation(name, agent, task, fixture, expected):
    folder = ROOT / f"tests/evals/{name}"
    folder.mkdir(parents=True, exist_ok=True)
    for path, value in fixture.items():
        dest = folder / "fixture" / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, str):
            dest.write_text(value, encoding="utf-8", newline="\n")
        else:
            save(dest, value)
    save(folder / "expected.yaml", {"role": agent, **expected})
    (folder / "task.md").write_text(task, encoding="utf-8", newline="\n")
    (folder / "grader.py").write_text(
        f"from lab.eval_graders import grade_task\n\ndef grade(output, workspace, expected):\n    return grade_task({json.dumps(name)}, output, workspace, expected)\n",
        encoding="utf-8",
        newline="\n",
    )
