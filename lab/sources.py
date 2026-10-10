"""Normalize public scholarly metadata without manufacturing missing fields."""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote, unquote

from lab.io import LabError, now
from lab.net import Network


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    text = unquote(value.strip()).lower()
    text = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", text).rstrip(".,;")
    return text if re.fullmatch(r"10\.\d{4,9}/\S+", text) else None


def normalize_arxiv(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"^.*arxiv\.org/(abs|pdf)/", "", value).removesuffix(".pdf")
    text = re.sub(r"v\d+$", "", text).strip()
    return text if re.fullmatch(r"\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7}", text) else None


def record(
    source: str,
    identifier: str,
    title: str,
    authors: list[str],
    year: int | None,
    abstract: str | None = None,
    doi: str | None = None,
    arxiv_id: str | None = None,
    venue: str | None = None,
    citations: int | None = None,
    oa_url: str | None = None,
    **extra,
) -> dict:
    title = " ".join(title.split())
    if not identifier or not title:
        raise LabError("Malformed metadata record: title and ID required")
    return {
        "id": f"doi:{normalize_doi(doi)}"
        if normalize_doi(doi)
        else f"arxiv:{normalize_arxiv(arxiv_id)}"
        if normalize_arxiv(arxiv_id)
        else f"{source}:{identifier}",
        "title": title,
        "authors": authors,
        "year": year,
        "abstract": abstract,
        "doi": normalize_doi(doi),
        "arxiv_id": normalize_arxiv(arxiv_id),
        "venue": venue,
        "citations": citations,
        "oa_url": oa_url,
        "sources": [source],
        "retrieved": now(),
        "source_ids": {source: identifier},
        **extra,
    }


def parse_openalex(item: dict) -> dict:
    inverted = item.get("abstract_inverted_index") or {}
    positions = {i: word for word, indexes in inverted.items() for i in indexes}
    abstract = " ".join(positions[i] for i in sorted(positions)) or None
    return record(
        "openalex",
        item["id"].rsplit("/", 1)[-1],
        item.get("title") or item.get("display_name", ""),
        [a["author"]["display_name"] for a in item.get("authorships", [])],
        item.get("publication_year"),
        abstract,
        item.get("doi"),
        venue=((item.get("primary_location") or {}).get("source") or {}).get("display_name"),
        citations=item.get("cited_by_count"),
        oa_url=(item.get("open_access") or {}).get("oa_url"),
        referenced_works=item.get("referenced_works", []),
        ids=item.get("ids", {}),
        publisher_pdf=(item.get("best_oa_location") or {}).get("pdf_url"),
    )


def parse_arxiv(text: str) -> list[dict]:
    try:
        feed = ET.fromstring(text)
    except ET.ParseError:
        raise LabError("Malformed arXiv Atom response") from None
    atom, ax = "{http://www.w3.org/2005/Atom}", "{http://arxiv.org/schemas/atom}"
    if feed.tag != atom + "feed":
        raise LabError("Expected arXiv Atom feed")
    results = []
    for entry in feed.findall(atom + "entry"):
        identifier = normalize_arxiv(entry.findtext(atom + "id"))
        if not identifier:
            if "error" in (entry.findtext(atom + "id") or ""):
                raise LabError(entry.findtext(atom + "summary") or "arXiv query error")
            raise LabError("Malformed arXiv identifier")
        authors = [a.findtext(atom + "name") for a in entry.findall(atom + "author")]
        published = entry.findtext(atom + "published", "")
        results.append(
            record(
                "arxiv",
                identifier,
                entry.findtext(atom + "title", ""),
                authors,
                int(published[:4]) if published else None,
                entry.findtext(atom + "summary"),
                entry.findtext(ax + "doi"),
                identifier,
                entry.findtext(ax + "journal_ref") or "arXiv",
                oa_url=f"https://arxiv.org/pdf/{identifier}",
            )
        )
    return results


def parse_crossref(item: dict) -> dict:
    published = item.get("published", item.get("issued", {})).get("date-parts", [[None]])
    authors = [
        (a.get("given", "") + " " + a.get("family", a.get("name", ""))).strip()
        for a in item.get("author", [])
    ]
    return record(
        "crossref",
        item["DOI"],
        (item.get("title") or [""])[0],
        authors,
        published[0][0],
        item.get("abstract"),
        item["DOI"],
        venue=(item.get("container-title") or [None])[0],
        citations=item.get("is-referenced-by-count"),
        links=item.get("link", []),
    )


def parse_semantic(item: dict) -> dict:
    ids = item.get("externalIds") or {}
    return record(
        "semanticscholar",
        item["paperId"],
        item.get("title", ""),
        [a["name"] for a in item.get("authors", [])],
        item.get("year"),
        item.get("abstract"),
        ids.get("DOI"),
        ids.get("ArXiv"),
        item.get("venue"),
        item.get("citationCount"),
        (item.get("openAccessPdf") or {}).get("url"),
    )


def search(
    net: Network,
    source: str,
    query: str,
    limit: int = 50,
    year_from: int | None = None,
    page: int = 1,
) -> list[dict]:
    if not 1 <= limit <= 100:
        raise LabError("Search page size must be between 1 and 100")
    if source == "openalex":
        params = {"search": query, "per_page": limit, "page": page}
        if year_from:
            params["filter"] = f"from_publication_date:{year_from}-01-01"
        key = os.getenv("OPENALEX_API_KEY")
        if key:
            params["api_key"] = key
        response = net.json("https://api.openalex.org/works", params=params)
        if not isinstance(response.get("results"), list):
            raise LabError("Malformed OpenAlex works response")
        return [parse_openalex(x) for x in response["results"]]
    if source == "arxiv":
        return parse_arxiv(
            net.get(
                "https://export.arxiv.org/api/query",
                params={"search_query": query, "max_results": limit, "start": (page - 1) * limit},
            ).text
        )
    if source == "crossref":
        params = {"query": query, "rows": limit, "offset": (page - 1) * limit}
        if year_from:
            params["filter"] = f"from-pub-date:{year_from}-01-01"
        response = net.json("https://api.crossref.org/works", params=params)
        return [parse_crossref(x) for x in response["message"]["items"]]
    if source == "semanticscholar":
        headers = (
            {"x-api-key": os.environ["SEMANTIC_SCHOLAR_API_KEY"]}
            if os.getenv("SEMANTIC_SCHOLAR_API_KEY")
            else {}
        )
        response = net.json(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": limit,
                "offset": (page - 1) * limit,
                "fields": "title,authors,year,abstract,venue,externalIds,citationCount,openAccessPdf",
            },
            headers=headers,
        )
        return [parse_semantic(x) for x in response["data"]]
    raise LabError(f"Unsupported search source: {source}")


def lookup_doi(net: Network, doi: str) -> dict:
    normalized = normalize_doi(doi)
    if not normalized:
        raise LabError("Invalid DOI")
    return parse_crossref(
        net.json("https://api.crossref.org/works/" + quote(normalized, safe=""))["message"]
    )
