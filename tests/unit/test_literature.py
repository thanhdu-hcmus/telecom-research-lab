import json
from pathlib import Path

import httpx
import pymupdf
import pytest

from lab import literature, sources, venues
from lab.io import LabError, load, save, write_jsonl

ROOT = Path(__file__).resolve().parents[2]


def toy_pdf(title="Reconfigurable Intelligent Surface NOMA Evaluation", columns=False, pages=1):
    document = pymupdf.open()
    for _ in range(pages):
        page = document.new_page()
        page.insert_text((50, 50), title, fontsize=12)
        page.insert_textbox(pymupdf.Rect(50, 90, 280, 400), "Left column wireless model.\nRayleigh fading.\nNo CSI claim stated.")
        if columns:
            page.insert_textbox(pymupdf.Rect(310, 90, 550, 400), "Right column results.\nNoise measured in watts.")
    data = document.tobytes()
    document.close()
    return data


def test_identifiers_and_dedup_40_to_28():
    assert sources.normalize_doi("https://doi.org/10.1109/TWC.2024.1234") == "10.1109/twc.2024.1234"
    assert sources.normalize_arxiv("http://arxiv.org/abs/2401.12345v3") == "2401.12345"
    items = [sources.record("fixture", f"F{i}", f"Wireless title {i}", ["First Author"], 2024, doi=f"10.1234/{i}") for i in range(28)]
    duplicates = [{**r, "id": "alternative:" + r["id"], "doi": "https://doi.org/" + r["doi"]} for r in items[:12]]
    merged, counts = literature.dedup(items + duplicates)
    assert len(merged) == 28
    assert counts == {"identified": 40, "duplicates_removed": 12, "unique": 28}
    # Weak matches do not merge conflicting DOI records.
    assert len(literature.dedup([items[0], {**items[0], "doi": "10.1234/other", "id": "other"}])[0]) == 2


def test_arxiv_and_title_duplicates():
    left = sources.record("fixture", "a", "RIS-NOMA: Wireless", ["A Author"], 2024, arxiv_id="2401.12345v1")
    right = sources.record("fixture", "b", "RIS NOMA Wireless", ["A. Author"], 2024)
    assert len(literature.dedup([left, right])[0]) == 1
    with pytest.raises(LabError):
        sources.parse_arxiv("<html>wrong</html>")


@pytest.mark.parametrize("columns,pages", [(False, 1), (True, 1), (True, 3)])
def test_three_synthetic_pdf_layouts(columns, pages):
    extracted = literature.pdf_text(toy_pdf(columns=columns, pages=pages))
    assert len(extracted) == pages
    assert "Left column" in extracted[0]
    if columns:
        assert "Right column" in extracted[0]
    assert literature.title_matches("Reconfigurable Intelligent Surface NOMA Evaluation", extracted[0])
    assert not literature.title_matches("Completely Different Optical Network Study", extracted[0])


def configure(tmp_path):
    repo = tmp_path / "repo"
    save(repo / "config/lab.config.yaml", {"library_root": "../library", "contact_email": None})
    save(repo / "config/sources.yaml", load(ROOT / "config/sources.yaml"))
    path = repo / "projects/toy"
    (path / "literature").mkdir(parents=True)
    return repo, path


def test_fetch_arxiv_first_title_rejection_manual_and_cache(tmp_path):
    repo, path = configure(tmp_path)
    item = sources.record("fixture", "1", "Reconfigurable Intelligent Surface NOMA Evaluation", ["A Author"], 2024, arxiv_id="2401.12345")
    calls = []
    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(200, content=toy_pdf(), headers={"content-type": "application/pdf"})
    assert literature.fetch(repo, path, item, httpx.MockTransport(handler))["route"] == "arxiv"
    assert len(calls) == 1
    write_jsonl(path / "literature/candidates.jsonl", [item])
    assert literature.extract(repo, path, item["id"])["pages"] == 1
    assert literature.extract(repo, path, item["id"])["cached"]
    wrong = {**item, "title": "Completely Different Optical Network Study"}
    assert literature.fetch(repo, path, wrong, httpx.MockTransport(handler))["status"] == "FAIL"
    assert (path / "to_human/manual-downloads.csv").exists()


def test_prisma_screening_bookkeeping(tmp_path):
    repo, path = configure(tmp_path)
    items = [sources.record("fixture", str(i), f"Wireless title {i}", ["Author"], 2024) for i in range(3)]
    write_jsonl(path / "literature/candidates.jsonl", items)
    write_jsonl(path / "literature/search-records.jsonl", items + items[:1])
    save(path / "literature/screening.yaml", [{"id": items[0]["id"], "decision": "include", "reason": "matches"},
                                             {"id": items[1]["id"], "decision": "exclude", "reason": "outside scope"}])
    report = literature.prisma(path)
    assert report["duplicates_removed"] == 1
    assert report["included"] + report["excluded"] + report["pending"] == 3
    literature.screen_export(path)
    assert len(load(path / "literature/screening.yaml")) == 3


def test_sjr_communications_quartile(tmp_path):
    save(tmp_path / "config/venues.yaml", load(ROOT / "config/venues.yaml"))
    fixture = tmp_path / "sjr.csv"
    fixture.write_text('Title;Issn;Categories\nFixture Wireless Journal;12345678;"Mathematics (Q1); Computer Networks and Communications (Q3); Signal Processing (Q2)"\n', encoding="utf-8")
    assert venues.lookup(tmp_path, issn="1234-5678", csv_path=fixture)["quartile"] == "Q2"
    assert venues.lookup(tmp_path, title="Missing", csv_path=fixture)["quartile"] is None
    assert venues.lookup(tmp_path, title="Missing")["status"] == "INCONCLUSIVE"


def test_recorded_parsers():
    folder = ROOT / "tests/fixtures/http"
    assert sources.parse_openalex(json.loads((folder / "openalex.json").read_text(encoding="utf-8"))["results"][0])["title"]
    assert sources.parse_arxiv((folder / "arxiv.xml").read_text(encoding="utf-8"))[0]["arxiv_id"]
    assert sources.parse_crossref(json.loads((folder / "crossref.json").read_text(encoding="utf-8"))["message"]["items"][0])["doi"]
    semantic = folder / "semanticscholar.json"
    if semantic.exists():
        assert sources.parse_semantic(json.loads(semantic.read_text(encoding="utf-8"))["data"][0])["id"]
    synthetic = json.loads((folder / "semanticscholar-synthetic.json").read_text())["data"][0]
    assert sources.parse_semantic(synthetic)["abstract"] is None
    assert sources.parse_semantic(synthetic)["id"] == "arxiv:2401.12345"


def test_retrieval_chain_and_untrusted_oa_host(tmp_path):
    repo, path = configure(tmp_path)
    settings = load(repo / "config/lab.config.yaml")
    settings["contact_email"] = "fixture@example.invalid"
    save(repo / "config/lab.config.yaml", settings)
    settings = load(repo / "config/sources.yaml")
    settings["approved_oa_hosts"] = ["oa.fixture.edu"]
    save(repo / "config/sources.yaml", settings)
    item = sources.record("fixture", "1", "Reconfigurable Intelligent Surface NOMA Evaluation", ["A Author"], 2024,
                          doi="10.1234/example", arxiv_id="2401.12345", oa_url="https://unreviewed.example/pdf")
    calls = []
    def handler(request):
        calls.append(request.url.host)
        if request.url.host == "arxiv.org":
            return httpx.Response(200, content=toy_pdf("Wrong Optical Study"))
        if request.url.host == "api.unpaywall.org":
            return httpx.Response(200, json={"best_oa_location": {"url_for_pdf": "https://oa.fixture.edu/paper.pdf"}})
        if request.url.host == "oa.fixture.edu":
            return httpx.Response(200, content=toy_pdf())
        raise AssertionError("Unexpected route")
    result = literature.fetch(repo, path, item, httpx.MockTransport(handler))
    assert result["route"] == "unpaywall"
    assert calls == ["arxiv.org", "api.unpaywall.org", "oa.fixture.edu"]


def test_bad_pdf_rejected_and_cli_unknown_project():
    from typer.testing import CliRunner

    from lab.cli import app
    with pytest.raises(LabError):
        literature.pdf_text(b"not a PDF")
    result = CliRunner().invoke(app, ["lit", "search", "--project", "missing-fixture", "--json"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["status"] == "FAIL"
