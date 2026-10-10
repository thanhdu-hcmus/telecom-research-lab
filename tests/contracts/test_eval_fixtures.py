from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_every_eval_has_named_role_and_nonempty_inputs():
    for folder in (ROOT / "tests/evals").iterdir():
        if not folder.is_dir():
            continue
        assert (folder / "task.md").is_file()
        assert (folder / "grader.py").is_file()
        expected = yaml.safe_load((folder / "expected.yaml").read_text(encoding="utf-8"))
        assert (ROOT / f".codex/agents/{expected['role']}.toml").is_file()
        assert any(p.is_file() for p in (folder / "fixture").rglob("*"))
        assert "fixture" in (folder / "task.md").read_text(
            encoding="utf-8"
        ).lower() or folder.name in {
            "lit-recall",
            "gap-evidence",
            "code-scout-discrimination",
            "card-grounding",
        }
