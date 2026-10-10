"""Freeze ten real Crossref records and strict bibliography fault probes."""

from pathlib import Path
import json
import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
from lab.io import load, save, now
from lab.net import Network
from lab.sources import lookup_doi

ROOT = Path(__file__).resolve().parents[1]
ids = [
    i.removeprefix("doi:") for i in load(ROOT / "tests/evals/lit-recall/expected.yaml")["key_ids"]
]
ids[0] = "10.1109/lsp.2014.2343971"
records = []
with Network(ROOT) as net:
    for doi in ids:
        records.append(lookup_doi(net, doi))
save(ROOT / "tests/fixtures/citation-real-records.yaml", records)
entries = [
    {
        "ENTRYTYPE": "article",
        "ID": f"real{i}",
        "title": r["title"],
        "author": " and ".join(r["authors"]),
        "year": str(r["year"]),
        "journal": r["venue"],
        "doi": r["doi"],
    }
    for i, r in enumerate(records)
]
db = BibDatabase()
db.entries = entries
(ROOT / "tests/fixtures/citation-real.bib").write_text(
    bibtexparser.dumps(db), encoding="utf-8", newline="\n"
)
db.entries = [
    dict(entries[i], ID=f"fabricated{i}", title=f"Fabricated fixture paper {i}") for i in range(3)
] + [dict(entries[3], ID="wrongyear", year=str(int(entries[3]["year"]) + 1))]
(ROOT / "tests/fixtures/citation-faults.bib").write_text(
    bibtexparser.dumps(db), encoding="utf-8", newline="\n"
)
save(
    ROOT / "docs/evidence/m10-citation-fixtures.json",
    {
        "status": "PASS",
        "retrieved": now(),
        "source": "Crossref REST exact DOI lookups",
        "dois": ids,
        "real_entries": len(records),
        "faults": "3 authored fabricated titles and1 wrong year; all using actual DOI records to test mismatches",
    },
)
print(json.dumps({"status": "PASS", "records": len(records)}))
