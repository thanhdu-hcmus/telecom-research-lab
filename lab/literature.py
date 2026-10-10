"""Search, dedup, retrieval and screening bookkeeping with retained provenance."""

from __future__ import annotations

import csv
import difflib
import os
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote

import pymupdf

from lab import sources
from lab.io import LabError, library, load, now, read_jsonl, safe_id, save, sha256, write_jsonl
from lab.models import PaperCard
from lab.net import Network


def normalized(text: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower(),
    ).strip()


def duplicate_keys(item: dict) -> set[tuple]:
    keys = set()
    if doi := sources.normalize_doi(item.get("doi")):
        keys.add(("doi", doi))
    if arxiv := sources.normalize_arxiv(item.get("arxiv_id")):
        keys.add(("arxiv", arxiv))
    if item.get("title") and item.get("authors") and item.get("year"):
        keys.add(("title", normalized(item["title"]), normalized(item["authors"][0]), item["year"]))
    return keys


def dedup(records: list[dict]) -> tuple[list[dict], dict]:
    parents = list(range(len(records)))

    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    seen = {}
    for i, item in enumerate(records):
        for key in duplicate_keys(item):
            if key in seen:
                j = seen[key]
                left = {
                    sources.normalize_doi(records[k].get("doi"))
                    for k in range(len(records))
                    if find(k) == find(i)
                } - {None}
                right = {
                    sources.normalize_doi(records[k].get("doi"))
                    for k in range(len(records))
                    if find(k) == find(j)
                } - {None}
                # A weak title match may not override conflicting DOI identities.
                if key[0] != "title" or not (left and right and left != right):
                    parents[find(i)] = find(j)
            else:
                seen[key] = i
    groups = {}
    for i in range(len(records)):
        groups.setdefault(find(i), []).append(records[i])
    merged = []
    for group in groups.values():
        best = sorted(
            group, key=lambda x: (not bool(x.get("doi")), not bool(x.get("abstract")), x["id"])
        )[0].copy()
        best["aliases"] = sorted(
            {x["id"] for x in group} | {a for x in group for a in x.get("aliases", [])}
        )
        best["sources"] = sorted({s for x in group for s in x.get("sources", [])})
        best["source_ids"] = {
            s: identifier for x in group for s, identifier in x.get("source_ids", {}).items()
        }
        best["query_evidence"] = [q for x in group for q in x.get("query_evidence", [])]
        for key in [
            "doi",
            "arxiv_id",
            "abstract",
            "oa_url",
            "year",
            "venue",
            "citations",
            "publisher_pdf",
        ]:
            if best.get(key) is None:
                best[key] = next((x[key] for x in group if x.get(key) is not None), None)
        best["id"] = (
            f"doi:{best['doi']}"
            if best.get("doi")
            else f"arxiv:{best['arxiv_id']}"
            if best.get("arxiv_id")
            else best["id"]
        )
        merged.append(best)
    return sorted(merged, key=lambda x: x["id"]), {
        "identified": len(records),
        "duplicates_removed": len(records) - len(merged),
        "unique": len(merged),
    }


def run_search(repo: Path, path: Path, plan_path: Path, transport=None) -> dict:
    plan = load(plan_path)
    if not isinstance(plan.get("queries"), list) or not plan["queries"]:
        raise LabError("Query plan needs a nonempty queries list")
    records, failures = [], []
    with Network(repo, transport) as net:
        for query in plan["queries"]:
            try:
                if not 1 <= query.get("pages", 1) <= 20:
                    raise LabError("Query pages must be between 1 and 20")
                for page in range(1, query.get("pages", 1) + 1):
                    items = sources.search(
                        net,
                        query["source"],
                        query["query"],
                        query.get("limit", 50),
                        plan.get("year_from"),
                        page,
                    )
                    for item in items:
                        item["query_evidence"] = [
                            {
                                "source": query["source"],
                                "query": query["query"],
                                "page": page,
                                "retrieved": now(),
                            }
                        ]
                    records += items
                    if len(items) < query.get("limit", 50):
                        break
            except (ValueError, KeyError) as error:
                failures.append(
                    {
                        "source": query.get("source"),
                        "query": query.get("query"),
                        "error": str(error),
                    }
                )
    existing_raw = read_jsonl(path / "literature/search-records.jsonl")
    write_jsonl(path / "literature/search-records.jsonl", existing_raw + records)
    merged, counts = dedup(existing_raw + records)
    write_jsonl(path / "literature/candidates.jsonl", merged)
    report = {
        "status": "FAIL" if failures else "PASS",
        "queries": len(plan["queries"]),
        "new_records": len(records),
        "counts": counts,
        "failures": failures,
        "coverage_note": "Each query is bounded by its limit and pages; absence from these results does not establish novelty.",
    }
    save(path / "literature/search-report.json", report)
    return report


def snowball(repo: Path, path: Path, ids: list[str], depth: int = 1) -> dict:
    if depth != 1:
        raise LabError("Snowball is intentionally limited to depth one")
    candidates = read_jsonl(path / "literature/candidates.jsonl")
    selected = [r for r in candidates if r["id"] in ids]
    if len(selected) != len(set(ids)):
        raise LabError("Seed IDs must exist in candidates")
    additions = []
    with Network(repo) as net:
        for item in selected:
            identifier = item.get("source_ids", {}).get("openalex")
            if not identifier and item.get("doi"):
                work = net.json(
                    "https://api.openalex.org/works/https://doi.org/" + quote(item["doi"], safe="")
                )
                identifier = work["id"].rsplit("/", 1)[-1]
            if not identifier:
                continue
            work = net.json(f"https://api.openalex.org/works/{identifier}")
            for ref in work.get("referenced_works", [])[:100]:
                additions.append(
                    sources.parse_openalex(
                        net.json("https://api.openalex.org/works/" + ref.rsplit("/", 1)[-1])
                    )
                )
            citing = net.json(
                "https://api.openalex.org/works",
                params={"filter": f"cites:{identifier}", "per_page": 100},
            )
            additions.extend(sources.parse_openalex(r) for r in citing["results"])
    merged, counts = dedup(candidates + additions)
    raw_path = path / "literature/search-records.jsonl"
    write_jsonl(raw_path, read_jsonl(raw_path) + additions)
    write_jsonl(path / "literature/candidates.jsonl", merged)
    save(
        path / "literature/snowball-report.json",
        {
            "seeds": ids,
            "depth": depth,
            "counts": counts,
            "bounded": "At most 100 backward and 100 forward records per seed; expand explicitly if coverage is insufficient.",
        },
    )
    return {"status": "PASS", "added": len(additions), "counts": counts}


def prisma(path: Path) -> dict:
    records = read_jsonl(path / "literature/candidates.jsonl")
    raw = read_jsonl(path / "literature/search-records.jsonl")
    screening = load(path / "literature/screening.yaml", [])
    identifiers = {r["id"] for r in records}
    if len({r["id"] for r in screening}) != len(screening) or any(
        r["id"] not in identifiers for r in screening
    ):
        raise LabError("Screening IDs must be unique and present in candidates")
    for entry in screening:
        if entry.get("decision") not in {"include", "exclude", "pending"} or not entry.get(
            "reason"
        ):
            raise LabError("Every screening decision needs a valid decision and reason")
    included = sum(r["decision"] == "include" for r in screening)
    excluded = sum(r["decision"] == "exclude" for r in screening)
    report = {
        "identified": len(raw) if raw else len(records),
        "duplicates_removed": max(0, len(raw) - len(records)),
        "screened": included + excluded,
        "excluded": excluded,
        "included": included,
        "pending": len(records) - included - excluded,
    }
    save(path / "literature/prisma.json", report)
    return {"status": "PASS", **report}


def screen_export(path: Path) -> dict:
    records = read_jsonl(path / "literature/candidates.jsonl")
    existing = {r["id"]: r for r in load(path / "literature/screening.yaml", [])}
    save(
        path / "literature/screening.yaml",
        [
            existing.get(r["id"], {"id": r["id"], "decision": "pending", "reason": "not screened"})
            for r in records
        ],
    )
    with (path / "literature/screening.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "title", "authors", "year", "abstract"])
        writer.writeheader()
        writer.writerows({k: r.get(k) for k in writer.fieldnames} for r in records)
    return {"status": "PASS", "records": len(records)}


def title_matches(title: str, text: str, threshold: float = 0.95) -> bool:
    wanted = normalized(title).split()
    got = normalized(text).split()
    if len(wanted) < 3:
        return normalized(title) in normalized(text)
    for width in {len(wanted), len(wanted) + 2, max(3, len(wanted) - 2)}:
        for i in range(max(1, len(got) - width + 1)):
            if (
                difflib.SequenceMatcher(
                    None, " ".join(wanted), " ".join(got[i : i + width])
                ).ratio()
                >= threshold
            ):
                return True
    return False


def pdf_text(data: bytes) -> list[str]:
    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            if document.is_encrypted or document.page_count == 0:
                raise LabError("Encrypted or empty PDF")
            return [page.get_text(sort=True) for page in document]
    except (RuntimeError, pymupdf.FileDataError) as error:
        raise LabError("Malformed or unreadable PDF") from error


def store_pdf(repo: Path, item: dict, data: bytes, source: str) -> dict:
    pages = pdf_text(data)
    if not title_matches(item["title"], pages[0]):
        raise LabError("PDF first-page title does not match the metadata record")
    lib = library(repo)
    if lib.is_relative_to(repo.resolve()):
        raise LabError("PDF library must be outside the Git repository")
    destination = lib / "pdfs" / (safe_id(item["id"]) + ".pdf")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    entry = {
        "id": item["id"],
        "title": item["title"],
        "path": str(destination),
        "sha256": sha256(destination),
        "source": source,
        "retrieved": now(),
        "pages": len(pages),
    }
    index = lib / "library.jsonl"
    entries = [r for r in read_jsonl(index) if r["id"] != item["id"]]
    write_jsonl(index, entries + [entry])
    return entry


def manual(path: Path, item: dict, failures: list[str]) -> dict:
    destination = path / "to_human/manual-downloads.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "doi", "title", "link", "hint", "failures"]
    previous = (
        list(csv.DictReader(destination.open(encoding="utf-8", newline="")))
        if destination.exists()
        else []
    )
    row = {
        "id": item["id"],
        "doi": item.get("doi"),
        "title": item["title"],
        "link": "https://doi.org/" + item["doi"] if item.get("doi") else "",
        "hint": "Use institutional access or ask the author; ingest a legitimately downloaded PDF.",
        "failures": "; ".join(failures),
    }
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows([r for r in previous if r["id"] != item["id"]] + [row])
    return {
        "status": "FAIL",
        "id": item["id"],
        "manual_download": str(destination),
        "failures": failures,
    }


def fetch(repo: Path, path: Path, item: dict, transport=None) -> dict:
    failures = []
    config = load(repo / "config/lab.config.yaml")
    with Network(repo, transport) as net:

        def download(url, route):
            if not url:
                return None
            try:
                data = net.get(url).content
                return {
                    "status": "PASS",
                    "route": route,
                    "record": store_pdf(repo, item, data, url),
                }
            except (LabError, OSError) as error:
                failures.append(f"{route}: {error}")
                return None

        arxiv_id = item.get("arxiv_id")
        if not arxiv_id:
            try:
                hits = sources.search(
                    net, "arxiv", 'ti:"' + item["title"].replace('"', "") + '"', 5
                )
                surname = (
                    normalized(item["authors"][0]).split()[-1] if item.get("authors") else None
                )
                hit = next(
                    (
                        r
                        for r in hits
                        if title_matches(item["title"], r["title"])
                        and surname
                        and r["authors"]
                        and normalized(r["authors"][0]).split()[-1] == surname
                    ),
                    None,
                )
                arxiv_id = hit.get("arxiv_id") if hit else None
            except LabError as error:
                failures.append(f"arxiv title search: {error}")
        if arxiv_id:
            result = download(f"https://arxiv.org/pdf/{sources.normalize_arxiv(arxiv_id)}", "arxiv")
            if result:
                return result
        doi = item.get("doi")
        if doi and config.get("contact_email"):
            try:
                data = net.json(
                    "https://api.unpaywall.org/v2/" + quote(doi, safe=""),
                    params={"email": config["contact_email"]},
                )
                result = download(
                    (data.get("best_oa_location") or {}).get("url_for_pdf"), "unpaywall"
                )
                if result:
                    return result
            except LabError as error:
                failures.append(f"unpaywall: {error}")
        result = download(item.get("oa_url"), "openalex")
        if result:
            return result
        if doi:
            try:
                headers = (
                    {"x-api-key": os.getenv("SEMANTIC_SCHOLAR_API_KEY")}
                    if os.getenv("SEMANTIC_SCHOLAR_API_KEY")
                    else {}
                )
                data = net.json(
                    "https://api.semanticscholar.org/graph/v1/paper/DOI:" + quote(doi, safe=""),
                    params={"fields": "openAccessPdf"},
                    headers=headers,
                )
                result = download((data.get("openAccessPdf") or {}).get("url"), "semanticscholar")
                if result:
                    return result
            except LabError as error:
                failures.append(f"semanticscholar: {error}")
        if os.getenv("CORE_API_KEY") and doi:
            try:
                data = net.json(
                    "https://api.core.ac.uk/v3/search/works",
                    params={"q": f'doi:"{doi}"', "limit": 3},
                    headers={"Authorization": "Bearer " + os.environ["CORE_API_KEY"]},
                )
                for record in data.get("results", []):
                    result = download(record.get("downloadUrl"), "core")
                    if result:
                        return result
            except LabError as error:
                failures.append(f"core: {error}")
        result = download(item.get("publisher_pdf"), "publisher-oa")
        if result:
            return result
    return manual(path, item, failures)


def ingest(repo: Path, path: Path, inbox: Path | None = None) -> dict:
    lib = library(repo)
    inbox = inbox or lib / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    records = read_jsonl(path / "literature/candidates.jsonl")
    outcomes = []
    for pdf in sorted(inbox.glob("*.pdf")):
        try:
            data = pdf.read_bytes()
            text = pdf_text(data)[0]
            doi_hits = {sources.normalize_doi(d) for d in re.findall(r"10\.\d{4,9}/[^\s<>]+", text)}
            matches = [
                r
                for r in records
                if (r.get("doi") and r["doi"] in doi_hits) or title_matches(r["title"], text)
            ]
            if len(matches) != 1:
                raise LabError("Inbox PDF needs exactly one DOI/title match")
            outcomes.append(
                {
                    "status": "PASS",
                    "record": store_pdf(repo, matches[0], data, f"manual:{pdf.name}"),
                }
            )
        except (ValueError, OSError) as error:
            outcomes.append({"status": "FAIL", "file": pdf.name, "error": str(error)})
    write_jsonl(path / "literature/library.jsonl", read_jsonl(lib / "library.jsonl"))
    return {
        "status": "FAIL" if any(r["status"] == "FAIL" for r in outcomes) else "PASS",
        "files": outcomes,
    }


def extract(repo: Path, path: Path, identifier: str) -> dict:
    lib = library(repo)
    entry = next((r for r in read_jsonl(lib / "library.jsonl") if r["id"] == identifier), None)
    if not entry:
        raise LabError("Paper not present in library")
    pdf = Path(entry["path"]).resolve()
    if not pdf.is_relative_to(lib) or sha256(pdf) != entry["sha256"]:
        raise LabError("Library file escaped storage or its checksum changed")
    destination = lib / "text" / (safe_id(identifier) + ".json")
    if destination.exists() and load(destination).get("pdf_sha256") == entry["sha256"]:
        return {"status": "PASS", "cached": True, "path": str(destination)}
    pages = pdf_text(pdf.read_bytes())
    save(
        destination,
        {
            "id": identifier,
            "pdf_sha256": entry["sha256"],
            "untrusted": True,
            "pages": [{"page": i + 1, "text": text} for i, text in enumerate(pages)],
        },
    )
    text_path = destination.with_suffix(".txt")
    text_path.write_text(
        "\n".join(
            f"<UNTRUSTED_PAPER_PAGE page='{i + 1}'>\n{text}\n</UNTRUSTED_PAPER_PAGE>"
            for i, text in enumerate(pages)
        ),
        encoding="utf-8",
    )
    return {"status": "PASS", "cached": False, "path": str(destination), "pages": len(pages)}


def import_metadata(path: Path, source: Path) -> dict:
    import bibtexparser

    if source.suffix == ".bib":
        bib = bibtexparser.loads(source.read_text(encoding="utf-8"))
        records = [
            sources.record(
                "import",
                e["ID"],
                e.get("title", ""),
                e.get("author", "").split(" and "),
                int(e["year"]) if e.get("year") else None,
                doi=e.get("doi"),
                venue=e.get("journal") or e.get("booktitle"),
            )
            for e in bib.entries
        ]
    elif source.suffix == ".jsonl":
        records = read_jsonl(source)
    else:
        data = load(source)
        records = data if isinstance(data, list) else data["records"]
    raw_path = path / "literature/search-records.jsonl"
    write_jsonl(raw_path, read_jsonl(raw_path) + records)
    merged, counts = dedup(read_jsonl(path / "literature/candidates.jsonl") + records)
    write_jsonl(path / "literature/candidates.jsonl", merged)
    return {
        "status": "PASS",
        "counts": counts,
        "note": "Imported metadata is unverified until cite verify.",
    }


def validate_review(path: Path) -> None:
    counts = prisma(path)
    if counts["pending"] or not counts["included"]:
        raise LabError("Screen every candidate and include at least one paper")
    included = {
        r["id"] for r in load(path / "literature/screening.yaml") if r["decision"] == "include"
    }
    cards = [PaperCard.model_validate(load(p)) for p in (path / "literature/cards").glob("*.yaml")]
    if {c.id for c in cards} != included:
        raise LabError("Every included paper needs exactly one grounded card")
    if len(cards) != len(included):
        raise LabError("Duplicate paper cards")
    entries = {r["id"]: r for r in read_jsonl(path / "literature/library.jsonl")}
    lib = library(path.parents[1])
    for card in cards:
        if card.id not in entries:
            raise LabError(f"Included paper lacks legitimate full text: {card.id}")
        entry = entries[card.id]
        pdf = Path(entry["path"]).resolve()
        if not pdf.is_relative_to(lib) or not pdf.is_file() or sha256(pdf) != entry["sha256"]:
            raise LabError(f"Included PDF missing, changed or outside library: {card.id}")
        for evidence in card.grounding.values():
            if any(ref.page is not None and ref.page > entry["pages"] for ref in evidence):
                raise LabError(f"Card cites a nonexistent page: {card.id}")
    with (path / "literature/gap-matrix.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or not {"gap_id", "dimension", "near_miss_ids", "missing"} <= rows[0].keys():
        raise LabError("Gap matrix needs gap_id, dimension, near_miss_ids, missing")
    for row in rows:
        near = row["near_miss_ids"].split(";")
        if len(set(near)) < 2 or any(i not in included for i in near) or not row["missing"]:
            raise LabError(
                "Each gap needs two existing near-miss cards and a precise missing element"
            )
