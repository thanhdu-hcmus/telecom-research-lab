import json
import re
import tomllib
from pathlib import Path

import jsonschema
import yaml

from lab.models import MODELS

ROOT = Path(__file__).resolve().parents[2]


def test_schemas_match_runtime_and_are_valid():
    for name, model in MODELS.items():
        schema = json.loads((ROOT / f"schemas/{name}.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        assert schema == model.model_json_schema(by_alias=True)


def test_agents_and_skill_references():
    agents = list((ROOT / ".codex/agents").glob("*.toml"))
    assert len(agents) == 11
    for path in agents:
        config = tomllib.loads(path.read_text(encoding="utf-8"))
        assert {"name", "description", "developer_instructions"} <= config.keys()
        assert config["model_reasoning_effort"] in {"medium", "high"}
        assert "model" not in config
        for name in re.findall(r"`([a-z][a-z-]+)`", config["developer_instructions"]):
            assert (ROOT / f".agents/skills/{name}/SKILL.md").exists(), name


def test_skill_frontmatter_and_size():
    for path in (ROOT / ".agents/skills").glob("*/SKILL.md"):
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        data = yaml.safe_load(text.split("---", 2)[1])
        assert data["name"] == path.parent.name
        assert len(data["description"]) > 20
        assert len(text.splitlines()) < 400
    assert len((ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()) < 300


def test_config_and_vendor_integrity():
    import hashlib

    tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    ranking = yaml.safe_load((ROOT / "config/ranking.yaml").read_text())
    assert sum(ranking["weights"].values()) == 10
    manifest = yaml.safe_load((ROOT / "vendor/MANIFEST.yaml").read_text())
    assert re.fullmatch("[a-f0-9]{40}", manifest["commit"])
    for record in manifest["files"]:
        assert (
            hashlib.sha256((ROOT / "vendor/orchestra" / record["path"]).read_bytes()).hexdigest()
            == record["sha256"]
        )
        assert record["review"] != "pending"


def test_m4_gold_cards_validate_against_schema_and_runtime():
    from lab.models import PaperCard

    cards = yaml.safe_load((ROOT / "tests/fixtures/m4-gold-cards.yaml").read_text())
    schema = json.loads((ROOT / "schemas/paper_card.schema.json").read_text())
    for card in cards:
        jsonschema.validate(card, schema)
        PaperCard.model_validate(card)
