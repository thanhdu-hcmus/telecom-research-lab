"""Vector IEEE-sized figures from checksum-verified manifest outputs."""

import os
from pathlib import Path

import numpy as np

from lab.io import LabError, load, save, sha256, within
from lab.simulation import output_path, verify_manifest


def make(path, spec_file: Path):
    cache = path.parents[1] / ".cache/matplotlib"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    spec = load(spec_file)
    width = spec.get("width_inches", 3.5)
    if width not in {3.5, 7.16} or not spec.get("xlabel") or not spec.get("ylabel"):
        raise LabError("IEEE width 3.5/7.16 inches and labels with units required")
    fig, ax = plt.subplots(figsize=(width, spec.get("height_inches", 2.6)))
    provenance = []
    for i, curve in enumerate(spec["curves"]):
        mf = within(path, curve["manifest"])
        m = verify_manifest(path, load(mf))
        matches = [
            o
            for o in m.outputs
            if o.path == curve["data"] and o.storage == curve.get("storage", "project")
        ]
        if len(matches) != 1:
            raise LabError("Figure needs a unique manifest data output")
        data_file = output_path(path, matches[0])
        if sha256(data_file) != matches[0].sha256:
            raise LabError("Figure data not bound to valid manifest")
        data = np.genfromtxt(data_file, delimiter=",", names=True)
        ax.plot(
            data[curve["x"]],
            data[curve["y"]],
            marker=["o", "s", "^", "d"][i % 4],
            markevery=max(1, len(data) // 8),
            linestyle=["-", "--", "-.", ":"][i % 4],
            label=curve["label"],
            linewidth=1,
        )
        provenance.append(
            {
                "manifest": curve["manifest"],
                "manifest_sha256": sha256(mf),
                "data": curve["data"],
                "sha256": sha256(data_file),
            }
        )
    ax.set(
        xlabel=spec["xlabel"],
        ylabel=spec["ylabel"],
        xscale=spec.get("xscale", "linear"),
        yscale=spec.get("yscale", "linear"),
    )
    ax.legend(fontsize=8)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    destination = within(path / "paper", spec["output"])
    if destination.suffix != ".pdf":
        raise LabError("Figures must be vector PDF")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination)
    plt.close(fig)
    save(
        destination.with_suffix(".manifest.json"),
        {
            "figure_sha256": sha256(destination),
            "spec_sha256": sha256(spec_file),
            "sources": provenance,
            "generator": "lab.figures.make",
            "width_inches": width,
        },
    )
    return {"status": "PASS", "figure": str(destination)}
