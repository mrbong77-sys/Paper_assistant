"""Synthetic benchmark of the example project (no real data; standard library only).

    python examples/demo_project/05_data/scripts/run_benchmark.py            # full run (a few seconds)
    python examples/demo_project/05_data/scripts/run_benchmark.py --check    # small run for a quick test

Two Gaussian classes in 2-D with a mean separation `d` (class overlap falls as d grows). For each d and each of five
fixed seeds, a training set of 200 points and a test set of 1,000 points are drawn; logistic regression (batch
gradient descent) and a nearest-centroid classifier are fitted on the training set and scored on the test set.
Writes 05_data/processed/results.json. Already finished (d, seed) cells are kept when the file exists, so an
interrupted run resumes.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "processed" / "results.json"
SEPARATIONS = [0.5, 1.0, 1.5, 2.0, 3.0]
SEEDS = [0, 1, 2, 3, 4]


def draw(rng: random.Random, n: int, d: float):
    xs, ys = [], []
    for i in range(n):
        y = i % 2
        mu = d / 2 if y else -d / 2
        xs.append((rng.gauss(mu, 1.0), rng.gauss(0.0, 1.0)))
        ys.append(y)
    return xs, ys


def fit_logistic(xs, ys, epochs: int = 300, lr: float = 0.5):
    w0 = w1 = w2 = 0.0
    n = len(xs)
    for _ in range(epochs):
        g0 = g1 = g2 = 0.0
        for (a, b), y in zip(xs, ys):
            p = 1 / (1 + math.exp(-(w0 + w1 * a + w2 * b)))
            g0, g1, g2 = g0 + (p - y), g1 + (p - y) * a, g2 + (p - y) * b
        w0, w1, w2 = w0 - lr * g0 / n, w1 - lr * g1 / n, w2 - lr * g2 / n
    return lambda a, b: int(w0 + w1 * a + w2 * b > 0)


def fit_centroid(xs, ys):
    c = {}
    for k in (0, 1):
        pts = [x for x, y in zip(xs, ys) if y == k]
        c[k] = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    return lambda a, b: int((a - c[1][0]) ** 2 + (b - c[1][1]) ** 2 < (a - c[0][0]) ** 2 + (b - c[0][1]) ** 2)


def accuracy(model, xs, ys) -> float:
    return sum(model(a, b) == y for (a, b), y in zip(xs, ys)) / len(ys)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="two separations, one seed, small sets")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    seps, seeds, n_train, n_test = (SEPARATIONS[:2], SEEDS[:1], 40, 100) if a.check else (SEPARATIONS, SEEDS, 200, 1000)
    res = json.loads(a.out.read_text(encoding="utf-8")) if a.out.exists() and not a.check else {"cells": {}}
    res.update({"n_train": n_train, "n_test": n_test, "separations": seps, "seeds": seeds})
    for d in seps:
        for s in seeds:
            key = f"d{d}_s{s}"
            if key in res["cells"]:
                continue
            rng = random.Random(1000 * s + int(10 * d))
            xtr, ytr = draw(rng, n_train, d)
            xte, yte = draw(rng, n_test, d)
            res["cells"][key] = {"d": d, "seed": s, "logistic": accuracy(fit_logistic(xtr, ytr), xte, yte),
                                 "centroid": accuracy(fit_centroid(xtr, ytr), xte, yte)}
    summary = {}
    for d in seps:
        cells = [c for c in res["cells"].values() if c["d"] == d]
        for m in ("logistic", "centroid"):
            v = [c[m] for c in cells]
            mean = sum(v) / len(v)
            sd = math.sqrt(sum((x - mean) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
            summary.setdefault(str(d), {})[m] = {"mean": mean, "sd": sd, "n": len(v)}
        diffs = [c["logistic"] - c["centroid"] for c in cells]
        summary[str(d)]["diff_mean"] = sum(diffs) / len(diffs)
    res["summary"] = summary
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {a.out}: {len(res['cells'])} cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
