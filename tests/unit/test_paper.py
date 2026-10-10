from pathlib import Path

import pytest

from lab.citations import author_match, verify_bib
from lab.io import load
from lab.paper import claim_macros, overlap_text, trace_documents

ROOT = Path(__file__).resolve().parents[2]


def test_real_and_fake_citations():
    file = ROOT / "tests/fixtures/citation-real-records.yaml"
    if not file.exists():
        pytest.fail("Record the ten actual primary-source citation fixtures before acceptance")
    records = {r["doi"]: r for r in load(file)}

    def lookup(doi, arxiv):
        return records[doi]

    good = verify_bib(ROOT / "tests/fixtures/citation-real.bib", lookup)
    assert good["status"] == "PASS" and len(good["entries"]) == 10
    bad = verify_bib(ROOT / "tests/fixtures/citation-faults.bib", lookup)
    assert bad["status"] == "FAIL" and sum(not e["passed"] for e in bad["entries"]) == 4


def test_trace_and_overlap(tmp_path):
    claims = [{"key": "rate", "value": 3}]
    (tmp_path / "main.tex").write_text(
        r"\begin{abstract}Mean is \res{rate}.\end{abstract}"
        + "\n"
        + r"\section{Results} Gain is 20 percent.",
        newline="\n",
    )
    check = trace_documents(tmp_path, claims, lambda c: {"value": 3})
    assert check["status"] == "FAIL" and "20" in check["errors"][0]
    (tmp_path / "main.tex").write_text(
        r"\begin{abstract}Mean is \res{rate}.\end{abstract}", newline="\n"
    )
    assert trace_documents(tmp_path, claims, lambda c: {"value": 3})["status"] == "PASS"
    sentence = "These twenty words are deliberately planted to verify that the local overlap checker detects copied research prose from source documents"
    assert overlap_text(sentence, {"source": sentence})
    assert not overlap_text("A short independent description.", {"source": sentence})
    assert "result" in claim_macros(claims)


def test_author_names():
    assert author_match("Ding, Z. and H. Vincent Poor", ["Zhiguo Ding", "H. Vincent Poor"])
    assert not author_match("Invented Author", ["Zhiguo Ding"])


def test_trace_includes_and_subsections(tmp_path):
    (tmp_path / "main.tex").write_text(
        r"\section{Results}\input{sub}" + "\n" + r"\section{Conclusion} No numeric result.",
        newline="\n",
    )
    (tmp_path / "sub.tex").write_text(
        r"\subsection{Sensitivity} Untraced 55 percent.", newline="\n"
    )
    check = trace_documents(tmp_path, [], lambda c: c)
    assert check["status"] == "FAIL" and "55" in check["errors"][0]
