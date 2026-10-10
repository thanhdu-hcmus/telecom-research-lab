"""Record bounded public API responses for offline parser tests."""
import json
from pathlib import Path

from lab.io import now, save
from lab.net import Network

ROOT = Path(__file__).resolve().parents[1]
QUERIES = {
    "openalex": ("https://api.openalex.org/works", {"search": "reconfigurable intelligent surface NOMA", "per_page": 3}),
    "arxiv": ("https://export.arxiv.org/api/query", {"search_query": 'all:"reconfigurable intelligent surface" AND all:NOMA', "max_results": 3}),
    "crossref": ("https://api.crossref.org/works", {"query": "reconfigurable intelligent surface NOMA", "rows": 3}),
    "semanticscholar": ("https://api.semanticscholar.org/graph/v1/paper/search", {"query": "reconfigurable intelligent surface NOMA", "limit": 3,
        "fields": "title,authors,year,abstract,venue,externalIds,citationCount,openAccessPdf"}),
}
receipts = []
with Network(ROOT) as net:
    for source, (url, params) in QUERIES.items():
        try:
            response = net.get(url, params=params)
            target = ROOT / "tests/fixtures/http" / (source + (".xml" if source == "arxiv" else ".json"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(response.text, encoding="utf-8")
            receipts.append({"source": source, "url": url, "params": params, "retrieved": now(), "status": "PASS"})
        except ValueError as error:
            receipts.append({"source": source, "status": "FAIL", "error": str(error)})
save(ROOT / "docs/evidence/recorded-sources.json", receipts)
print(json.dumps(receipts))
