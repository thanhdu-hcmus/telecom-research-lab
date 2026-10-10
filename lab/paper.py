"""IEEE compilation, numeric lineage, overlap review and clean handoff archives."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from lab.io import LabError, library, load, save, sha256, within
from lab.verification import evaluate_claim


def tex_sources(folder):
    return sorted(p for p in folder.rglob("*.tex") if p.name != "claims-generated.tex")


def hashes(folder):
    return {
        p.relative_to(folder).as_posix(): sha256(p)
        for p in sorted(folder.rglob("*"))
        if p.is_file()
        and p.suffix in {".tex", ".bib", ".cls", ".bst", ".sty", ".pdf"}
        and p.name != "main.pdf"
    }


def claim_macros(claims):
    lines = [r"\newcommand{\res}[1]{\csname result#1\endcsname}"]
    for c in claims:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", c["key"]):
            raise LabError("Invalid result macro key")
        lines.append(
            r"\expandafter\def\csname result"
            + c["key"]
            + r"\endcsname{"
            + format(c["value"], ".8g")
            + "}"
        )
    return "\n".join(lines) + "\n"


def trace_documents(folder, claims, validate):
    ledger = {c["key"]: c for c in claims}
    if len(ledger) != len(claims):
        raise LabError("Duplicate claim keys")
    validated = {key: validate(c) for key, c in ledger.items()}
    uses = []
    errors = []
    sensitive = False
    stack = set()

    def lines(p):
        nonlocal sensitive
        if p in stack or len(stack) > 20:
            raise LabError("Recursive/deep TeX input refused")
        stack.add(p)
        for lineno, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            line = re.split(r"(?<!\\)%", line)[0]
            match = re.search(r"\\section\*?\{([^}]+)\}", line)
            if match:
                sensitive = bool(re.search(r"results|discussion", match[1], re.I))
            if r"\begin{abstract}" in line:
                sensitive = True
            if re.search(r"\\(?:def|newcommand|renewcommand)\s*(?:\{\s*)?\\res\b", line):
                errors.append(f"Result macro override at {p.name}:{lineno}")
            yield p, lineno, line, sensitive
            for include in re.finditer(r"\\(?:input|include)\{([^}]+)\}", line):
                target = within(
                    folder, include[1] if Path(include[1]).suffix else include[1] + ".tex"
                )
                if target.name == "claims-generated.tex":
                    continue
                if not target.is_file():
                    raise LabError("Missing included TeX source")
                yield from lines(target)
            if r"\end{abstract}" in line:
                sensitive = False
        stack.remove(p)

    for p, lineno, line, sensitive_here in lines(folder / "main.tex"):
        # Every result macro is validated, even outside the three sensitive sections.
        for m in re.finditer(r"\\res\{([^}]+)\}", line):
            key = m[1]
            if key not in validated:
                errors.append(f"Unknown claim {key} at {p.name}:{lineno}")
            else:
                uses.append(
                    {
                        "file": p.relative_to(folder).as_posix(),
                        "line": lineno,
                        "claim": key,
                        **validated[key],
                    }
                )
        if sensitive_here:
            cleaned = re.sub(r"\\(?:res|cite|ref|eqref|label)\{[^}]*\}", "", line)
            cleaned = re.sub(r"\\(?:input|include)\{[^}]*\}", "", cleaned)
            for number in re.finditer(
                r"(?<![A-Za-z_])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", cleaned
            ):
                errors.append(f"Untraced literal {number[0]} at {p.relative_to(folder)}:{lineno}")
    return {
        "status": "FAIL" if errors else "PASS",
        "uses": uses,
        "errors": errors,
        "manuscript_hashes": hashes(folder),
    }


def trace(path):
    claims = load(path / "results/claims.json")
    for c in claims:
        evaluate_claim(path, c)
    folder = path / "paper"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "claims-generated.tex").write_text(
        claim_macros(claims), encoding="utf-8", newline="\n"
    )
    result = trace_documents(folder, claims, lambda c: evaluate_claim(path, c))
    save(folder / "number-map.yaml", result["uses"])
    save(folder / "trace-check.json", result)
    return result


def overlap_text(text, sources, threshold=12):
    words = re.findall(r"[a-z]+", text.lower())
    spans = {tuple(words[i : i + threshold]): i for i in range(max(0, len(words) - threshold + 1))}
    matches = []
    for source, content in sources.items():
        sw = re.findall(r"[a-z]+", content.lower())
        for i in range(max(0, len(sw) - threshold + 1)):
            if tuple(sw[i : i + threshold]) in spans:
                matches.append(
                    {
                        "source": source,
                        "source_word": i,
                        "draft_word": spans[tuple(sw[i : i + threshold])],
                        "length_at_least": threshold,
                    }
                )
    return matches


def overlap(path):
    folder = path / "paper"
    sources = {}
    cache = library(path.parents[1]) / "text"
    for p in cache.rglob("*.txt"):
        if p.stat().st_size < 10_000_000:
            sources[str(p)] = p.read_text(encoding="utf-8")
    text = "\n".join(
        re.sub(r"(?m)(?<!\\)%.*$", "", p.read_text(encoding="utf-8")) for p in tex_sources(folder)
    )
    matches = overlap_text(text, sources)
    result = {
        "status": "FAIL" if matches else "PASS",
        "matches": matches,
        "sources_checked": len(sources),
        "limitation": "Local >=12-word self-check against cached full text; not a comprehensive plagiarism service",
        "manuscript_hashes": hashes(folder),
    }
    if not sources:
        result.update(status="FAIL", error="No cached source text available for overlap check")
    save(folder / "overlap-check.json", result)
    return result


def compile_folder(repo, folder):
    config = load(repo / "config/lab.config.yaml")
    bin_dir = repo / config["latex_bin"]
    command = bin_dir / ("latexmk.exe" if os.name == "nt" else "latexmk")
    if not command.exists():
        fallback = shutil.which("latexmk")
        if not fallback:
            raise LabError("latexmk unavailable")
        command = Path(fallback)
    env = os.environ.copy()
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    env["openout_any"] = "p"
    env["openin_any"] = "p"
    # Never execute a manuscript-supplied Perl rc or shell escape.
    result = subprocess.run(
        [
            str(command),
            "-norc",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            "-pdflatex=pdflatex -no-shell-escape %O %S",
            "main.tex",
        ],
        cwd=folder,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    (folder / "build-output.txt").write_text(
        result.stdout + result.stderr, encoding="utf-8", newline="\n"
    )
    log = (
        (folder / "main.log").read_text(encoding="utf-8", errors="replace")
        if (folder / "main.log").exists()
        else ""
    )
    bad = re.findall(
        r"(?:LaTeX Warning: (?:Citation|Reference).*undefined|There were undefined references|! LaTeX Error|! Undefined control sequence)",
        log,
    )
    success = result.returncode == 0 and (folder / "main.pdf").exists() and not bad
    return {
        "status": "PASS" if success else "FAIL",
        "exit": result.returncode,
        "undefined_or_errors": bad,
        "pdf_sha256": sha256(folder / "main.pdf") if (folder / "main.pdf").exists() else None,
        "manuscript_hashes": hashes(folder),
    }


def init(path, style="journal"):
    from lab.state import ensure_phase

    ensure_phase(path, "P7")
    if style not in {"journal", "conference"}:
        raise LabError("Style must be journal or conference")
    folder = path / "paper"
    if (folder / "main.tex").exists():
        raise LabError("Paper already initialized")
    shutil.copytree(path.parents[1] / "templates/paper" / style, folder, dirs_exist_ok=True)
    return {"status": "PASS", "paper": str(folder)}


def build(path):
    result = compile_folder(path.parents[1], path / "paper")
    save(path / "paper/build-check.json", result)
    return result


def disclosure(path):
    sessions = load(path / "ara/trace/sessions/session_index.yaml", [])
    records = [
        load(within(path / "ara/trace/sessions", identifier + ".yaml")) for identifier in sessions
    ]
    tags = {
        tag: sum(s.get("provenance") == tag for s in records) for tag in ["user", "ai", "joint"]
    }
    text = (
        "# AI assistance disclosure draft\n\nAutomated assistants supported research workflow tasks recorded in the provenance index.\n\nRecorded contributions: "
        + ", ".join(f"{k}: {v} sessions" for k, v in tags.items())
        + ".\n\nThe authors must review the record, describe actual tool usage and responsibilities, and adapt this disclosure to the target venue policy. This draft is not an assertion of PI approval or authorship by an AI.\n"
    )
    (path / "paper/ai-disclosure.md").write_text(text, encoding="utf-8", newline="\n")
    return {"status": "PASS", "contributions": tags, "pi_review_required": True}


def validate_paper(path):
    from lab.verification import validate_verification

    validate_verification(path)
    folder = path / "paper"
    cite = load(folder / "citation-check.json")
    if cite.get("status") != "PASS" or cite.get("bib_sha256") != sha256(folder / "refs.bib"):
        raise LabError("Current bibliography must be primary-source verified")
    if trace(path)["status"] != "PASS":
        raise LabError("Numeric trace failed")
    for name in ["overlap-check.json", "build-check.json"]:
        check = load(folder / name)
        if check.get("status") != "PASS" or check.get("manuscript_hashes") != hashes(folder):
            raise LabError(f"Current {name} must pass")
        if name == "build-check.json" and check.get("pdf_sha256") != sha256(folder / "main.pdf"):
            raise LabError("Compiled PDF changed after successful build")
    review = load(folder / "review.yaml")
    if (
        not review.get("reviewer")
        or not review.get("independent")
        or not review.get("findings_reviewed")
    ):
        raise LabError("Independent paper review required")
    if any(
        f.get("severity") in {"critical", "major"} and f.get("status") not in {"fixed", "rebutted"}
        for f in review.get("findings", [])
    ):
        raise LabError("Unresolved major/critical paper findings")
    if not (folder / "response.md").is_file() or not (folder / "ai-disclosure.md").is_file():
        raise LabError("Review response and AI disclosure draft required")
    return {"status": "PASS"}


def export(path):
    validate_paper(path)
    folder = path / "paper"
    dest = path / "to_human/overleaf.zip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    selected = [
        p
        for p in folder.rglob("*")
        if p.is_file()
        and p.suffix in {".tex", ".bib", ".cls", ".bst", ".sty", ".pdf"}
        and p.name != "main.pdf"
    ]
    with tempfile.TemporaryDirectory(prefix="lab-paper-") as temp:
        clean = Path(temp)
        for p in selected:
            target = clean / p.relative_to(folder)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
        test = compile_folder(path.parents[1], clean)
        if test["status"] != "PASS":
            raise LabError("Export failed clean-folder compilation")
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as archive:
            for p in selected:
                archive.write(p, p.relative_to(folder))
    result = {
        "status": "PASS",
        "zip": str(dest),
        "sha256": sha256(dest),
        "clean_compile": test,
        "overleaf_confirmation": "PI must upload and confirm once",
    }
    save(path / "to_human/export-receipt.json", result)
    return result
