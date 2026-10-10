"""Provision only the M0 tools inside the checkout; never change user PATH.

Downloads use official release endpoints. MATLAB release digests are checked
against the GitHub release metadata. TeX Live bootstrap files are recorded with
their SHA-256 digest and final TLS download URL before use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / ".tools"


def fetch(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "telecom-research-lab/M0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), response.url


def receipt(name: str, data: dict) -> None:
    target = ROOT / "docs" / "evidence" / (name + ".json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def matlab() -> None:
    # Deliberately pinned, rather than silently updating on each execution.
    metadata, _ = fetch(
        "https://api.github.com/repos/matlab/matlab-mcp-server/releases/tags/v0.14.0"
    )
    release = json.loads(metadata)
    asset = next(a for a in release["assets"] if a["name"] == "matlab-mcp-server-windows-x64.exe")
    url = asset["browser_download_url"]
    if not url.startswith("https://github.com/matlab/matlab-mcp-server/releases/download/v0.14.0/"):
        raise ValueError("Unexpected release asset URL")
    payload, final_url = fetch(url)
    digest = "sha256:" + hashlib.sha256(payload).hexdigest()
    if digest != asset.get("digest"):
        raise ValueError("Release asset SHA-256 mismatch or missing official digest")
    target = TOOLS / "matlab-mcp-server" / asset["name"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    receipt(
        "matlab-mcp-install",
        {
            "release": release["tag_name"],
            "source": url,
            "final_url": final_url,
            "sha256": digest[7:],
            "digest_verified": True,
            "path": str(target),
            "size_bytes": len(payload),
        },
    )
    print(f"Installed MATLAB MCP {release['tag_name']} with verified digest")


def tex_bootstrap() -> None:
    url = "https://mirror.ctan.org/systems/texlive/tlnet/install-tl.zip"
    payload, final_url = fetch(url)
    archive = TOOLS / "install-tl.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(payload)
    extracted = TOOLS / "texlive-installer"
    extracted.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            resolved = (extracted / entry.filename).resolve()
            if not resolved.is_relative_to(extracted.resolve()):
                raise ValueError("Unsafe ZIP member")
            if ((entry.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError("Installer archive contains a symbolic link")
        bundle.extractall(extracted)
    install_root = TOOLS / "texlive"
    root_path = install_root.as_posix()
    profile = TOOLS / "texlive.profile"
    profile.write_text(
        "selected_scheme scheme-small\n"
        f"TEXDIR {root_path}\n"
        f"TEXMFLOCAL {root_path}/texmf-local\n"
        f"TEXMFSYSVAR {root_path}/texmf-var\n"
        f"TEXMFSYSCONFIG {root_path}/texmf-config\n"
        f"TEXMFHOME {root_path}/texmf-home\n"
        f"TEXMFVAR {root_path}/texmf-user-var\n"
        f"TEXMFCONFIG {root_path}/texmf-user-config\n"
        "instopt_portable 1\n"
        "instopt_adjustpath 0\n"
        "instopt_adjustrepo 0\n"
        "tlpdbopt_install_docfiles 0\n"
        "tlpdbopt_install_srcfiles 0\n"
        "tlpdbopt_autobackup 0\n",
        encoding="utf-8",
        newline="\n",
    )
    installer = next(extracted.rglob("install-tl-windows.bat"))
    receipt(
        "texlive-bootstrap",
        {
            "source": url,
            "final_url": final_url,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
            "installer": str(installer),
            "profile": str(profile),
            "portable": True,
            "changes_system_path": False,
        },
    )
    print(f"TeX Live installer: {installer}")
    print(f"Profile: {profile}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool", choices=["matlab", "tex-bootstrap"])
    option = parser.parse_args()
    matlab() if option.tool == "matlab" else tex_bootstrap()
