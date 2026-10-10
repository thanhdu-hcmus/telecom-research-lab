"""SJR classification from a PI-supplied CSV; unknown remains unknown."""

import csv
import re
from pathlib import Path

from lab.io import load
from lab.literature import normalized


def lookup(
    repo: Path, title: str | None = None, issn: str | None = None, csv_path: Path | None = None
) -> dict:
    config = load(repo / "config/venues.yaml")
    configured = config.get("sjr_csv")
    csv_path = csv_path or (repo / configured if configured else None)
    if csv_path is None or not csv_path.exists():
        return {"status": "INCONCLUSIVE", "quartile": None, "reason": "PI has not supplied SJR CSV"}
    text = csv_path.read_text(encoding="utf-8-sig")
    delimiter = ";" if text.splitlines()[0].count(";") > text.splitlines()[0].count(",") else ","
    records = list(csv.DictReader(text.splitlines(), delimiter=delimiter))
    match = []
    issn_digits = re.sub(r"\D", "", issn or "")
    for row in records:
        numbers = re.findall(r"\d{8}", re.sub(r"-", "", row.get("Issn", row.get("ISSN", ""))))
        if (issn_digits and issn_digits in numbers) or (
            title and normalized(title) == normalized(row.get("Title", ""))
        ):
            match.append(row)
    if len(match) != 1:
        return {"status": "INCONCLUSIVE", "quartile": None, "reason": "No unique title/ISSN match"}
    categories = match[0].get("Categories", "")
    quartiles = []
    evidence = []
    for category in categories.split(";"):
        for approved in config["communications_categories"]:
            if normalized(approved) in normalized(category):
                found = re.search(r"\bQ([1-4])\b", category)
                if found:
                    quartiles.append(int(found[1]))
                    evidence.append(category.strip())
    return {
        "status": "PASS" if quartiles else "INCONCLUSIVE",
        "title": match[0].get("Title"),
        "quartile": f"Q{min(quartiles)}" if quartiles else None,
        "category_evidence": evidence,
        "source_csv": str(csv_path),
        "scopus_indexed": None,
        "note": "Quartile is for communications-related categories only; verify CSV year and Scopus separately.",
    }
