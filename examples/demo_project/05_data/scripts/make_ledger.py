"""Write 05_data/numbers.csv from 05_data/processed/results.json (every manuscript number comes from here).

    python examples/demo_project/05_data/scripts/make_ledger.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT.parents[1]))          # the Paper_assistant repository root
from pa import numbers as N  # noqa: E402

RES = PROJECT / "05_data" / "processed" / "results.json"
LEDGER = PROJECT / "05_data" / "numbers.csv"
SRC = "05_data/processed/results.json"


def sign_test(diffs: list[float]) -> tuple[int, int, float]:
    """Exact two-sided sign test over the non-zero paired differences."""
    pos, neg = sum(x > 0 for x in diffs), sum(x < 0 for x in diffs)
    n, k = pos + neg, min(pos, neg)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return pos, neg, p


def main() -> int:
    r = json.loads(RES.read_text(encoding="utf-8"))
    if LEDGER.exists():
        LEDGER.unlink()
    N.add(LEDGER, "n_train", str(r["n_train"]), "", f"{SRC}:n_train", "training points per cell")
    N.add(LEDGER, "n_test", f"{r['n_test']:,}", "", f"{SRC}:n_test", "test points per cell")
    N.add(LEDGER, "n_seeds", str(len(r["seeds"])), "", f"{SRC}:seeds", "")
    N.add(LEDGER, "n_cells", str(len(r["cells"])), "", f"{SRC}:cells", "separations x seeds")
    for d, s in r["summary"].items():
        tag = d.replace(".", "p")
        for m, short in (("logistic", "lr"), ("centroid", "nc")):
            N.add(LEDGER, f"acc_{short}_d{tag}", f"{100 * s[m]['mean']:.1f}", "%", f"{SRC}:summary.{d}.{m}.mean",
                  f"mean over {s[m]['n']} seeds")
            N.add(LEDGER, f"sd_{short}_d{tag}", f"{100 * s[m]['sd']:.1f}", "%", f"{SRC}:summary.{d}.{m}.sd", "SD over seeds")
        bayes = 0.5 * (1 + math.erf((float(d) / 2) / math.sqrt(2)))
        N.add(LEDGER, f"acc_bayes_d{tag}", f"{100 * bayes:.1f}", "%", f"Phi(d/2) with d={d}", "Bayes-optimal accuracy")
        N.add(LEDGER, f"diff_d{tag}", f"{100 * s['diff_mean']:+.1f}", "points", f"{SRC}:summary.{d}.diff_mean",
              "logistic minus centroid, before rounding")
    diffs = [c["logistic"] - c["centroid"] for c in r["cells"].values()]
    pos, neg, p = sign_test(diffs)
    N.add(LEDGER, "sign_pos", str(pos), "", f"sign test over {SRC}:cells", "cells where logistic > centroid")
    N.add(LEDGER, "sign_neg", str(neg), "", f"sign test over {SRC}:cells", "cells where logistic < centroid")
    N.add(LEDGER, "sign_ties", str(len(diffs) - pos - neg), "", f"sign test over {SRC}:cells", "ties")
    N.add(LEDGER, "sign_p", f"{p:.3f}", "", "exact two-sided sign test (make_ledger.py:sign_test)", "")
    gap = max(abs(100 * (s[m]["mean"] - 0.5 * (1 + math.erf((float(d) / 2) / math.sqrt(2)))))
              for d, s in r["summary"].items() for m in ("logistic", "centroid"))
    N.add(LEDGER, "max_gap_bayes", f"{gap:.1f}", "points", "max |mean accuracy - Bayes| over all d and both models", "")
    print(f"wrote {LEDGER}: {len(N.load(LEDGER))} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
