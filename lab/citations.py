"""Metadata-generated BibTeX and independent primary-source verification."""

import html
import re
import unicodedata
from pathlib import Path

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase

from lab.io import LabError, read_jsonl, safe_id, save, sha256
from lab.net import Network
from lab.sources import lookup_doi, normalize_arxiv, normalize_doi, parse_arxiv


def normalize(text):
    plain = unicodedata.normalize("NFKD", html.unescape(re.sub(r"<[^>]+>", "", text)))
    return " ".join(re.findall(r"[a-z0-9]+", plain.lower()))


def bib_from(path, ids):
    records = {r["id"]: r for r in read_jsonl(path / "literature/candidates.jsonl")}
    entries = []
    for id in ids:
        if id not in records:
            raise LabError("Citation ID absent from library metadata")
        r = records[id]
        if not r.get("title") or not r.get("authors") or not r.get("year"):
            raise LabError("Incomplete metadata cannot generate a citation")
        entry = {
            "ENTRYTYPE": "article",
            "ID": safe_id(id),
            "title": r["title"],
            "author": " and ".join(r["authors"]),
            "year": str(r["year"]),
        }
        if r.get("venue"):
            entry["journal"] = r["venue"]
        if r.get("doi"):
            entry["doi"] = r["doi"]
        elif r.get("arxiv_id"):
            entry.update(eprint=r["arxiv_id"], archiveprefix="arXiv", journal="arXiv preprint")
        else:
            raise LabError("DOI or arXiv ID required")
        entries.append(entry)
    db = BibDatabase()
    db.entries = entries
    dest = path / "paper/refs.bib"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(bibtexparser.dumps(db), encoding="utf-8", newline="\n")
    save(
        path / "paper/bib-provenance.json",
        {
            "ids": ids,
            "metadata_sha256": sha256(path / "literature/candidates.jsonl"),
            "bib_sha256": sha256(dest),
        },
    )
    return {"status": "PASS", "entries": len(entries), "path": str(dest)}


def author_match(bib_names, source_names):
    actual = bib_names.split(" and ")
    if len(actual) != len(source_names):
        return False

    def parts(name):
        if "," in name:
            last, first = name.split(",", 1)
            return normalize(last), normalize(first).split()
        tokens = normalize(name).split()
        return tokens[-1] if tokens else "", tokens[:-1]

    for a, b in zip(actual, source_names):
        la, fa = parts(a)
        lb, fb = parts(b)
        if (
            la != lb
            or len(fa) != len(fb)
            or any(x != y and not (len(x) == 1 and x == y[:1]) for x, y in zip(fa, fb))
        ):
            return False
    return True


def compare(entry, record):
    problems = []
    if normalize(entry.get("title", "")) != normalize(record.get("title", "")):
        problems.append("title")
    if entry.get("year") != str(record.get("year")):
        problems.append("year")
    if not author_match(entry.get("author", ""), record.get("authors", [])):
        problems.append("authors")
    venue = entry.get("journal") or entry.get("booktitle")
    source_venue = record.get("venue")
    if record.get("arxiv_id") and not source_venue:
        if not venue or "arxiv" not in venue.lower():
            problems.append("venue")
    elif not venue or not source_venue or normalize(venue) != normalize(source_venue):
        problems.append("venue")
    if normalize_doi(entry.get("doi")) != normalize_doi(record.get("doi")):
        problems.append("doi")
    return problems


def verify_bib(bib: Path, lookup):
    db = bibtexparser.loads(bib.read_text(encoding="utf-8"))
    results = []
    if not db.entries:
        raise LabError("Empty bibliography")
    if len({e["ID"] for e in db.entries}) != len(db.entries):
        raise LabError("Duplicate BibTeX keys")
    for entry in db.entries:
        try:
            doi = normalize_doi(entry.get("doi"))
            arxiv = normalize_arxiv(entry.get("eprint"))
            if not doi and not arxiv:
                raise LabError("Missing DOI/arXiv ID")
            record = lookup(doi, arxiv)
            problems = compare(entry, record)
            results.append(
                {
                    "key": entry["ID"],
                    "passed": not problems,
                    "problems": problems,
                    "source_record": record,
                }
            )
        except (ValueError, OSError, KeyError) as e:
            results.append({"key": entry["ID"], "passed": False, "problems": [str(e)]})
    return {
        "status": "PASS" if all(r["passed"] for r in results) else "FAIL",
        "entries": results,
        "bib_sha256": sha256(bib),
    }


def verify(path):
    repo = path.parents[1]
    with Network(repo) as net:

        def lookup(doi, arxiv):
            if doi:
                return lookup_doi(net, doi)
            records = parse_arxiv(
                net.get("https://export.arxiv.org/api/query", params={"id_list": arxiv}).text
            )
            if len(records) != 1 or records[0].get("arxiv_id") != arxiv:
                raise LabError("arXiv lookup did not return exact ID")
            return records[0]

        report = verify_bib(path / "paper/refs.bib", lookup)
    save(path / "paper/citation-check.json", report)
    return report
