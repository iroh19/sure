"""
Figure generation for the S.U.R.E. paper (project_000). Builds all 5 figures directly from raw
experiment data (no plotting code exists anywhere in experiment_workspace/, confirmed by
structure_analysis.txt). Every number here traces to a specific EXPnn/results.md or raw JSON file,
cited in comments.

Run: python3 make_figures.py  (writes PDF figures into this directory)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

plt.rcParams.update({
    "font.size": 10,
    "font.family": "serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

MUTED = ["#6b7a8f", "#8fa39b", "#c9a66b", "#b06a6a"]

# ---------------------------------------------------------------------------
# Figure 1 — EXP03 four-bucket dual-layer classification (n=8)
# Source: experiment_workspace/experiment_runs/EXP03/results.md, g3_results.json
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.0, 3.4))
labels = [
    "unparseable\ndefaulted-to-ok",
    "parseable\nagrees",
    "parseable\nunder-calls\n(escalated)",
    "parseable\nover-calls",
]
counts = [4, 3, 1, 0]
pct = [50, 38, 12, 0]
colors = [MUTED[0], MUTED[1], MUTED[2], MUTED[3]]
bars = ax.bar(labels, counts, color=colors, edgecolor="black", linewidth=0.6, width=0.62)
for b, c, p in zip(bars, counts, pct):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.12, f"{c}/8 ({p}%)",
             ha="center", va="bottom", fontsize=9)
ax.set_ylim(0, 5.4)
ax.set_ylabel("Count (of 8 scenarios)")
ax.set_title("Four-bucket classification of AQUA-1B outputs\nthrough the real apply_rule_override (n=8)", fontsize=10)
ax.annotate("dominant pathway: fail-safe\ndefaulting (50%), not\ncorrection (12%)",
            xy=(0.5, 4.05), xytext=(1.55, 4.55),
            fontsize=8, ha="left",
            arrowprops=dict(arrowstyle="->", lw=0.8, color="black"))
ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
fig.tight_layout()
fig.savefig("fig1_exp03_four_bucket.pdf")
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2 — EXP07 precision-recall tradeoff across confidence thresholds
# Source: experiment_workspace/experiment_runs/EXP07/results.md (coarse 7-point curve table)
# ---------------------------------------------------------------------------
conf = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
prec = [0.564, 0.655, 0.720, 0.776, 0.820, 0.851, 0.881]
rec = [0.847, 0.813, 0.782, 0.761, 0.743, 0.725, 0.704]

fig, ax = plt.subplots(figsize=(5.0, 3.8))
ax.plot(rec, prec, "-o", color=MUTED[0], markersize=4, linewidth=1.3, label="P/R curve (conf 0.10-0.40)")

# deployed point (conf=0.20)
ax.scatter([0.782], [0.720], marker="*", s=220, color=MUTED[3], zorder=5,
           label="deployed (conf=0.20)")
ax.annotate("deployed\nconf=0.20\nP=0.720, R=0.782",
            xy=(0.782, 0.720), xytext=(0.795, 0.68),
            fontsize=8, ha="left",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="none", alpha=0.9),
            arrowprops=dict(arrowstyle="->", lw=0.8, color="black", shrinkA=2, shrinkB=6))

# F1-argmax point (conf=0.341)
ax.scatter([0.730], [0.845], marker="D", s=70, color=MUTED[2], zorder=5,
           label="F1-argmax (conf=0.341)")
ax.annotate("F1-argmax\nconf=0.341\nP=0.845, R=0.730",
            xy=(0.730, 0.845), xytext=(0.605, 0.960),
            fontsize=8, ha="left", va="top",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="none", alpha=0.9),
            arrowprops=dict(arrowstyle="->", lw=0.8, color="black",
                             connectionstyle="arc3,rad=0.15",
                             shrinkA=2, shrinkB=6))

# headline reported point (P=0.858/0.859, R=0.719) -- functionally same as argmax
ax.scatter([0.719], [0.858], marker="s", s=45, facecolors="none", edgecolors="black",
           zorder=5, label="headline reported (R=0.719, P=0.858)")

ax.set_xlim(0.60, 0.90)
ax.set_ylim(0.50, 1.00)
ax.set_xlabel("Recall")
ax.set_ylabel("Precision")
ax.set_title("Vision precision-recall tradeoff across confidence\nthresholds (single val set, n=98 images)", fontsize=10)
ax.legend(fontsize=7.5, loc="lower left", frameon=False)
fig.tight_layout()
fig.savefig("fig2_exp07_pr_tradeoff.pdf")
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 3 — EXP06 latency vs mAP50 across six export configurations
# Source: experiment_workspace/experiment_runs/EXP06/results.md (run1_full_table.json et al.)
# ---------------------------------------------------------------------------
configs = ["pt-mps", "pt-cpu", "onnx", "onnx-int8", "coreml (ANE)", "torchscript"]
latency_p50 = [22.83, 38.62, 44.72, 35.24, 9.03, 45.82]  # coreml = 3-session mean
map50 = [0.8395, 0.8395, 0.8291, 0.8313, 0.8298, 0.8291]
size_mb = [54.5, 54.5, 36.2, 9.4, 18.2, 36.4]
is_deployed = [False, False, False, False, True, False]

fig, ax = plt.subplots(figsize=(5.6, 4.2))
ax.set_xscale("log")
ax.set_xlim(7.5, 62)
ax.set_ylim(0.8265, 0.8420)

label_bbox = dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.85)

# per-point label offsets chosen so no label crosses another marker, the title, or the axes.
# onnx (44.72ms) and torchscript (45.82ms) sit almost exactly on top of each other at the same
# mAP50 (0.8291), so those two get diverging leader-line arrows instead of a plain offset --
# otherwise their labels stack and one shows through the other.
offsets = {
    "pt-mps":       (0, 10, "center", "bottom"),
    "pt-cpu":       (0, 10, "center", "bottom"),
    "onnx-int8":    (0, 11, "center", "bottom"),
    "coreml (ANE)": (10, -3, "left", "center"),
}
leader_offsets = {
    "onnx":        (-28, 14, "right", "bottom"),
    "torchscript": (28, -16, "left", "top"),
}
for i, cfg in enumerate(configs):
    color = MUTED[3] if is_deployed[i] else MUTED[0]
    marker = "*" if is_deployed[i] else "o"
    size = 260 if is_deployed[i] else 90 + size_mb[i] * 2.2
    ax.scatter(latency_p50[i], map50[i], s=size, color=color, edgecolor="black",
               linewidth=0.6, zorder=5, marker=marker)
    if cfg in offsets:
        ox, oy, ha, va = offsets[cfg]
        ax.annotate(cfg, (latency_p50[i], map50[i]), textcoords="offset points",
                    xytext=(ox, oy), fontsize=8, ha=ha, va=va, bbox=label_bbox, zorder=6)
    else:
        ox, oy, ha, va = leader_offsets[cfg]
        ax.annotate(cfg, (latency_p50[i], map50[i]), textcoords="offset points",
                    xytext=(ox, oy), fontsize=8, ha=ha, va=va, bbox=label_bbox, zorder=6,
                    arrowprops=dict(arrowstyle="-", lw=0.6, color="black", shrinkA=1, shrinkB=4))

ax.set_xlabel("Inference latency, p50 (ms), log scale")
ax.set_ylabel("mAP50 (validation, n=98)")
ax.set_title("Latency-accuracy tradeoff across six export\nconfigurations of one YOLOv11s checkpoint", fontsize=10)
ax.annotate("CoreML/ANE: 9.03±0.22ms p50\n(3 independent sessions)",
            xy=(9.03, 0.8298), xytext=(9.7, 0.8272),
            fontsize=7.5, ha="left", va="bottom", bbox=label_bbox,
            arrowprops=dict(arrowstyle="->", lw=0.7, color="black", shrinkA=2, shrinkB=8))
ax.annotate("INT8 loses LESS accuracy\n(-0.0082) than fp32 export\n(-0.0104)",
            xy=(35.24, 0.8313), xytext=(23, 0.8352),
            fontsize=7.5, ha="left", va="bottom", bbox=label_bbox,
            arrowprops=dict(arrowstyle="->", lw=0.7, color="black",
                             connectionstyle="arc3,rad=-0.2", shrinkA=2, shrinkB=8))
fig.tight_layout()
fig.savefig("fig3_exp06_export_latency_map50.pdf")
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 4 — EXP08 PSI quantile vs equal-width across the 16-point severity sweep
# Source: experiment_workspace/experiment_runs/EXP08/exp08_output.json (full sweep)
# ---------------------------------------------------------------------------
delta = [0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.22, 0.24, 0.26, 0.28, 0.30]
quantile_psi = [0.005, 0.1639, 0.7279, 1.4778, 2.1842, 2.652, 3.3716, 3.4993, 3.986, 4.0302,
                4.1238, 4.3192, 4.6096, 4.8597, 4.8228, 4.8444]
equal_width_psi = [0.0049, 0.0776, 0.3059, 0.9057, 2.1412, 3.027, 3.4738, 3.8634, 4.2552, 5.1331,
                   5.9264, 6.2131, 6.3534, 6.7538, 7.3928, 7.6493]

fig, ax = plt.subplots(figsize=(5.2, 3.8))
ax.plot(delta, quantile_psi, "-o", color=MUTED[0], markersize=3.5, linewidth=1.3, label="quantile (decile) binning")
ax.plot(delta, equal_width_psi, "-s", color=MUTED[3], markersize=3.5, linewidth=1.3, label="equal-width binning")
ax.axhline(0.10, color="gray", linestyle=":", linewidth=0.8, zorder=1)
ax.axhline(0.25, color="gray", linestyle=":", linewidth=0.8, zorder=1)
label_bbox = dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85)
# Placed at the right edge, well past where both curves have already risen above y=1.0,
# so the reference-line labels sit in clear space below the curves, not crossed by them.
ax.text(0.298, 0.10, "MODERATE=0.10", fontsize=6.5, color="gray", ha="right", va="center",
        bbox=label_bbox, zorder=4)
ax.text(0.298, 0.25, "SIGNIFICANT=0.25", fontsize=6.5, color="gray", ha="right", va="center",
        bbox=label_bbox, zorder=4)
ax.axvspan(0.06, 0.08, color="gray", alpha=0.12)
ax.annotate("crossover region:\nquantile more sensitive below,\nequal-width overtakes above",
            xy=(0.07, 1.6), xytext=(0.12, 0.35), fontsize=7.5,
            bbox=label_bbox,
            arrowprops=dict(arrowstyle="->", lw=0.7, color="black", shrinkA=2, shrinkB=6))
ax.set_yscale("symlog", linthresh=0.1)
ax.set_xlabel(r"Severity ($\delta$, mean-shift)")
ax.set_ylabel("PSI (log scale)")
ax.set_title("PSI sensitivity: quantile vs. equal-width binning\nacross a 16-point synthetic severity sweep", fontsize=10)
leg = ax.legend(fontsize=8, loc="upper left", frameon=True, framealpha=0.92,
                 facecolor="white", edgecolor="none")
leg.set_zorder(10)
fig.tight_layout()
fig.savefig("fig4_exp08_psi_sweep.pdf")
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 5 (optional) — EXP01 RAG threshold precision/recall/F1 sweep
# Source: experiment_workspace/experiment_runs/EXP01/calibrate_output.log
# ---------------------------------------------------------------------------
thr = [0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90]
p = [0.707, 0.707, 0.763, 0.806, 0.906, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000]
r = [1.000, 1.000, 1.000, 1.000, 1.000, 0.828, 0.655, 0.448, 0.241, 0.069, 0.000]
f1 = [0.829, 0.829, 0.866, 0.892, 0.951, 0.906, 0.792, 0.619, 0.389, 0.129, 0.000]

fig, ax = plt.subplots(figsize=(3.9, 3.6))
ax.plot(thr, p, "-o", color=MUTED[0], markersize=3, label="Precision")
ax.plot(thr, r, "-s", color=MUTED[1], markersize=3, label="Recall")
ax.plot(thr, f1, "-^", color=MUTED[2], markersize=3, label="F1")
# Reference lines are drawn only across the data range (not into the label margin above),
# and the two threshold labels sit in the open margin above the plot at staggered heights so
# neither line pierces through a label and the two labels cannot collide with each other.
ax.plot([0.84, 0.84], [-0.03, 1.0], color="black", linestyle=":", linewidth=0.8, zorder=2)
ax.plot([0.85, 0.85], [-0.03, 1.0], color=MUTED[3], linestyle="--", linewidth=1.0, zorder=2)
label_bbox = dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.9)
ax.annotate("F1-argmax (0.84)", xy=(0.84, 1.0), xytext=(0.822, 1.22),
            fontsize=7, ha="center", va="bottom", bbox=label_bbox,
            arrowprops=dict(arrowstyle="->", lw=0.7, color="black", shrinkA=1, shrinkB=3))
ax.annotate("configured (0.85)", xy=(0.85, 1.0), xytext=(0.878, 1.10),
            fontsize=7, ha="center", va="bottom", color=MUTED[3], bbox=label_bbox,
            arrowprops=dict(arrowstyle="->", lw=0.7, color=MUTED[3], shrinkA=1, shrinkB=3))
ax.set_ylim(-0.03, 1.34)
ax.set_xlabel("Similarity threshold")
ax.set_ylabel("Score")
ax.set_title("RAG threshold sweep\n(29 pos. / 12 hard-neg. queries)", fontsize=9.5)
ax.legend(fontsize=7, loc="lower left", frameon=True, framealpha=0.9,
          facecolor="white", edgecolor="none")
fig.tight_layout()
fig.savefig("fig5_exp01_rag_threshold.pdf")
plt.close(fig)

print("All 5 figures written.")
