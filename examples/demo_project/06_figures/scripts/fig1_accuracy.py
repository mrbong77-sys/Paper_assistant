"""Figure 1: test accuracy of both classifiers and the Bayes-optimal accuracy against the class separation d.

    python examples/demo_project/06_figures/scripts/fig1_accuracy.py      (needs matplotlib)
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT.parents[1]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from pa.figures import apply_style, save  # noqa: E402

r = json.loads((PROJECT / "05_data" / "processed" / "results.json").read_text(encoding="utf-8"))
ds = [float(d) for d in r["summary"]]
apply_style()
fig, ax = plt.subplots(figsize=(3.4, 2.4))
bayes = [100 * 0.5 * (1 + math.erf((d / 2) / math.sqrt(2))) for d in ds]
ax.plot(ds, bayes, color="0.5", linestyle=":", marker="", label="Bayes-optimal")
for m, label in (("logistic", "Logistic regression"), ("centroid", "Nearest centroid")):
    mean = [100 * r["summary"][str(d)][m]["mean"] for d in ds]
    sd = [100 * r["summary"][str(d)][m]["sd"] for d in ds]
    ax.errorbar(ds, mean, yerr=sd, capsize=1.5, elinewidth=0.4, label=label)
ax.set_xlabel("Class separation d (standard deviations)")
ax.set_ylabel("Test accuracy (%)")
ax.legend(loc="lower right")
ax.grid(True)
save(fig, PROJECT / "06_figures" / "out" / "fig1_accuracy")
print("wrote 06_figures/out/fig1_accuracy.pdf and .png")
