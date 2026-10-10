"""Generate schema contracts from the runtime models."""
import json
from pathlib import Path

from lab.models import MODELS

ROOT = Path(__file__).resolve().parents[1]
for name, model in MODELS.items():
    path = ROOT / f"schemas/{name}.schema.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(model.model_json_schema(by_alias=True), indent=2) + "\n", encoding="utf-8")
