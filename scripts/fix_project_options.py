"""Normalize CLI project selectors to explicit --project options."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for name in ["cli.py", "cli_state.py", "cli_literature.py"]:
    path = ROOT / "lab" / name
    text = path.read_text(encoding="utf-8")
    if "project: str" in text:
        text = "from typing import Annotated\n" + text if name != "cli.py" else text.replace("from pathlib import Path", "from pathlib import Path\nfrom typing import Annotated")
        text = text.replace("project: str", 'project: Annotated[str, typer.Option("--project")]')
        path.write_text(text, encoding="utf-8")
