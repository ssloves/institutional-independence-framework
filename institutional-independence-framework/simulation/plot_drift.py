#!/usr/bin/env python3
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

with open("sim_results.json") as f:
    results = json.load(f)

fig, ax = plt.subplots(figsize=(7.5, 4.4), dpi=150)

colors = {
    "no_selection (control)": "#888888",
    "weak_selection": "#7FB3D5",
    "moderate_selection": "#2E86C1",
    "strong_selection": "#1B4F72",
}
labels = {
    "no_selection (control)": "No selection (control)",
    "weak_selection": "Weak selection",
    "moderate_selection": "Moderate selection",
    "strong_selection": "Strong selection",
}
styles = {
    "no_selection (control)": "--",
    "weak_selection": "-",
    "moderate_selection": "-",
    "strong_selection": "-",
}

for k, series in results.items():
    x = np.arange(len(series))
    ax.plot(x, series, styles[k], color=colors[k], lw=2.2,
            label=labels[k])

ax.set_xlabel("Decision turn", fontsize=11)
ax.set_ylabel("Recommendation entropy  H(R)", fontsize=11)
ax.set_title("Governance drift emerges from institutional selection alone\n"
             "(advisor's decision function is identical in every condition)",
             fontsize=11.5)
ax.legend(frameon=False, fontsize=9.5, loc="lower left")
ax.grid(True, alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_ylim(0.85, 1.55)

plt.tight_layout()
plt.savefig("drift_plot.png", dpi=150, bbox_inches="tight")
print("saved drift_plot.png")
