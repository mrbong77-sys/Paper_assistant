"""Figures: one house style for every plot, and a check of the files a journal will receive.

    from pa.figures import apply_style, save
    apply_style()                 # thin lines, small markers, one font size, colour-blind-safe cycle
    ...plot...
    save(fig, "06_figures/out/fig2_accuracy")   # writes .pdf (vector) and .png at 600 dpi

    python -m pa fig check 06_figures/out [--min-dpi 300] [--width-in 7.0]

The style follows the rules DI-06 to DI-09 of docs/style/core_rules.md: data lines thin enough that overlapping
series stay apart, markers small, colour never the only cue (line styles and markers differ too), text readable at
print size. matplotlib is needed only for apply_style/save; the check uses the standard library.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

# Okabe–Ito colour-blind-safe palette
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442", "#000000"]
LINESTYLES = ["-", "--", "-.", ":"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]

RC = {
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "lines.linewidth": 0.6, "lines.markersize": 3, "lines.markeredgewidth": 0.4,
    "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.major.size": 2.5,
    "ytick.major.size": 2.5, "grid.linewidth": 0.3, "grid.alpha": 0.4, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42, "ps.fonttype": 42, "figure.dpi": 150,
}


def apply_style(extra: dict | None = None):
    import matplotlib as mpl
    from cycler import cycler
    rc = dict(RC)
    rc["axes.prop_cycle"] = (cycler(color=PALETTE[:4]) + cycler(linestyle=LINESTYLES) + cycler(marker=MARKERS[:4]))
    rc.update(extra or {})
    mpl.rcParams.update(rc)
    return rc


def save(fig, stem: str | Path, dpi: int = 600) -> list[Path]:
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    out = []
    for ext in ("pdf", "png"):
        p = stem.with_suffix("." + ext)
        fig.savefig(p, dpi=dpi)
        out.append(p)
    return out


def png_info(path: Path) -> dict:
    """Width, height and dpi (from the pHYs chunk; None when absent) of a PNG, without third-party packages."""
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    i, info = 8, {"dpi": None}
    while i < len(data):
        n, typ = struct.unpack(">I4s", data[i:i + 8])
        chunk = data[i + 8:i + 8 + n]
        if typ == b"IHDR":
            info["width"], info["height"] = struct.unpack(">II", chunk[:8])
        elif typ == b"pHYs":
            px, py, unit = struct.unpack(">IIB", chunk)
            if unit == 1:
                info["dpi"] = round(px * 0.0254)
        elif typ == b"IEND":
            break
        i += 12 + n
    return info


def check(folder: Path, min_dpi: int = 300, width_in: float | None = None) -> list[str]:
    """Problems with the figure files of a folder (DI-08, PK-04)."""
    problems = []
    folder = Path(folder)
    pngs = sorted(folder.glob("*.png"))
    if not pngs and not list(folder.glob("*.pdf")):
        return [f"no figure files in {folder}"]
    for p in pngs:
        info = png_info(p)
        if info["dpi"] is None:
            problems.append(f"{p.name}: no dpi stored; save with dpi={min_dpi} or more")
        elif info["dpi"] < min_dpi:
            problems.append(f"{p.name}: {info['dpi']} dpi < {min_dpi}")
        if width_in and info["dpi"]:
            w = info["width"] / info["dpi"]
            if w > width_in + 0.05:
                problems.append(f"{p.name}: {w:.2f} in wide at its dpi, wider than the {width_in} in text width")
        if not p.with_suffix(".pdf").exists() and not p.with_suffix(".svg").exists():
            problems.append(f"{p.name}: no vector copy (.pdf or .svg) next to it")
    return problems


def tiny_png(path: Path, w: int = 4, h: int = 4, dpi: int = 600) -> None:
    """Write a small grey PNG with a dpi chunk (used by the tests and the example)."""
    raw = b"".join(b"\x00" + b"\x80" * w for _ in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    ppm = round(dpi / 0.0254)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
                           + chunk(b"pHYs", struct.pack(">IIB", ppm, ppm, 1)) + chunk(b"IDAT", zlib.compress(raw))
                           + chunk(b"IEND", b""))
