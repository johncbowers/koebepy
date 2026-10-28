"""
Analytics over the scaling-sweep trial CSVs (scaling_sweep_data/*_trials.csv).

Produces:
  1. scaling_sweep_data/summary_table.csv -- one row per (n_points, method):
     trial count, certified-overlap rate, margin stats, noise-floor
     (packing_residual) stats, and the margin/residual ratio that tells you
     how close a given n is to the noise floor.
  2. scaling_sweep_data/summary_table.png -- that same table rendered as an
     image (matplotlib table), so it's a standalone file to view/share
     instead of terminal output.
  3. scaling_sweep_data/overlap_rate_by_method.png -- grouped bar chart of
     % of trials with a CERTIFIED overlap, by method, grouped by n.
  4. scaling_sweep_data/steepest_edge_avg_inversive_distance.png -- avg
     min_plane vs n for steepest_edge only (zoomed in, since it's flat at
     the scale of the other methods), showing the decreasing trend.
  5. scaling_sweep_data/avg_inversive_distance_vs_n.png -- avg min_plane vs
     n for all methods together, with a dashed reference line at 1.0 (the
     touching threshold: below it is overlap).
  6. scaling_sweep_data/margin_decay_loglog.png -- log-log plot of
     avg_margin = avg_min_plane - 1 vs n for steepest_edge, with a fitted
     slope (compares against the audit's pre-fix n^-2 finding).

"Real" vs "noise" throughout follows the audit's rule: a deficit only counts
as a real overlap if it exceeds 10x that trial's own packing_residual
(num_overlappings_certified, already computed by compare_methods). Run
check_overlap_certification.py separately to inspect the actual saved
packing/unfolding pairs behind any certified overlap.

Usage:
    python analyze_sweep_results.py [csv1.csv csv2.csv ...]

With no args, uses every scaling_sweep_data/*_trials.csv with a
num_overlappings_certified column (older pre-audit CSVs are skipped).
"""

import csv
import glob
import math
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = "scaling_sweep_data"

METHOD_COLORS = {
    "steepest_edge": "#1b6ca8",
    "dfs": "#d9534f",
    "bfs": "#5cb85c",
    "shortest_paths": "#8e44ad",
    "min_degree_shortest_paths": "#e67e22",
    "max_degree_shortest_paths": "#16a085",
}


def load_rows(csv_paths):
    rows = []
    for path in csv_paths:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            if "num_overlappings_certified" not in (reader.fieldnames or []):
                print(f"(skipping {path}: pre-audit CSV, no certified-overlap column)")
                continue
            for row in reader:
                rows.append(row)
    return rows


def build_summary(rows):
    """Group rows by (n_points, method) and compute summary stats."""
    groups = defaultdict(list)
    for row in rows:
        key = (int(row["n_points"]), row["method"])
        groups[key].append(row)

    summary = []
    for (n_points, method), group in groups.items():
        min_planes = [float(r["min_plane"]) for r in group]
        residuals = [float(r["packing_residual"]) for r in group]
        margins = [mp - 1.0 for mp in min_planes]
        certified_flags = [int(r["num_overlappings_certified"]) > 0 for r in group]
        n_certified_trials = sum(certified_flags)
        total_certified_overlaps = sum(int(r["num_overlappings_certified"]) for r in group)

        # Worst-case certified deficit (biggest real overlap depth), if any.
        certified_deficits = [1.0 - mp for mp, c in zip(min_planes, certified_flags) if c]
        worst_certified_deficit = max(certified_deficits) if certified_deficits else None

        # margin / residual ratio per trial -- how close to the noise floor.
        ratios = [m / r for m, r in zip(margins, residuals) if r > 0]

        summary.append({
            "n_points": n_points,
            "method": method,
            "trials": len(group),
            "pct_trials_certified_overlap": 100.0 * n_certified_trials / len(group),
            "total_certified_overlaps": total_certified_overlaps,
            "worst_certified_deficit": worst_certified_deficit,
            "avg_min_plane": sum(min_planes) / len(min_planes),
            "median_min_plane": sorted(min_planes)[len(min_planes) // 2],
            "worst_min_plane": min(min_planes),
            "avg_margin": sum(margins) / len(margins),
            "avg_packing_residual": sum(residuals) / len(residuals),
            "worst_packing_residual": max(residuals),
            "min_margin_over_residual_ratio": min(ratios) if ratios else None,
        })

    summary.sort(key=lambda s: (s["method"], s["n_points"]))
    return summary


def write_summary_csv(summary):
    path = f"{OUT_DIR}/summary_table.csv"
    fieldnames = list(summary[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary)
    print(f"Wrote {path}")


def _format_ratio(ratio):
    if ratio is None:
        return "-"
    if abs(ratio) > 1000:
        return "(overlapping)"
    return f"{ratio:.2f}x"


def render_table_image(summary):
    """Render the summary table as a standalone image file."""
    col_labels = ["method", "n", "trials", "certified %", "#certified",
                  "worst deficit", "avg min_plane", "avg residual", "min margin/residual"]
    cell_text = []
    for s in summary:
        worst_deficit = f"{s['worst_certified_deficit']:.3e}" if s["worst_certified_deficit"] is not None else "-"
        cell_text.append([
            s["method"],
            str(s["n_points"]),
            str(s["trials"]),
            f"{s['pct_trials_certified_overlap']:.1f}%",
            str(s["total_certified_overlaps"]),
            worst_deficit,
            f"{s['avg_min_plane']:.6f}",
            f"{s['avg_packing_residual']:.3e}",
            _format_ratio(s["min_margin_over_residual_ratio"]),
        ])

    fig_height = 0.45 * len(cell_text) + 1.0
    fig, ax = plt.subplots(figsize=(13, fig_height))
    ax.axis("off")
    table = ax.table(cellText=cell_text, colLabels=col_labels, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)
    table.auto_set_column_width(col=list(range(len(col_labels))))

    # Header styling.
    for col in range(len(col_labels)):
        cell = table[0, col]
        cell.set_facecolor("#2c3e50")
        cell.set_text_props(color="white", weight="bold")

    # Highlight steepest_edge rows and zebra-stripe the rest.
    for row_idx, s in enumerate(summary, start=1):
        color = "#dbe9f6" if s["method"] == "steepest_edge" else ("#f7f7f7" if row_idx % 2 == 0 else "white")
        for col in range(len(col_labels)):
            table[row_idx, col].set_facecolor(color)

    plt.title("Unfolding method scaling-sweep summary", fontsize=13, weight="bold", pad=14)
    plt.tight_layout()
    out = f"{OUT_DIR}/summary_table.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Wrote {out}")


def plot_overlap_rate_by_method(summary):
    """Grouped bar chart: % of trials with a CERTIFIED overlap, by method, grouped by n."""
    ns = sorted(set(s["n_points"] for s in summary))
    methods = sorted(set(s["method"] for s in summary))
    rate = {(s["n_points"], s["method"]): s["pct_trials_certified_overlap"] for s in summary}

    x = range(len(ns))
    width = 0.8 / len(methods)

    plt.figure(figsize=(8, 5.5))
    for i, method in enumerate(methods):
        ys = [rate.get((n, method), 0.0) for n in ns]
        xs = [xi + i * width for xi in x]
        bars = plt.bar(xs, ys, width=width, label=method, color=METHOD_COLORS.get(method))
        for bar, y in zip(bars, ys):
            plt.text(bar.get_x() + bar.get_width() / 2, y + 1, f"{y:.0f}%",
                      ha="center", va="bottom", fontsize=8)

    plt.xticks([xi + width * (len(methods) - 1) / 2 for xi in x], [str(n) for n in ns])
    plt.xlabel("number of faces (n)")
    plt.ylabel("% of trials with a CERTIFIED overlap")
    plt.ylim(0, 115)
    plt.title("Certified overlap rate by method")
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=len(methods))
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    out = f"{OUT_DIR}/overlap_rate_by_method.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Wrote {out}")


def plot_steepest_edge_only(summary):
    """avg_min_plane vs n for steepest_edge only, zoomed in on the fine trend."""
    points = sorted((s["n_points"], s["avg_min_plane"]) for s in summary if s["method"] == "steepest_edge")
    if not points:
        return
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    plt.figure(figsize=(8, 5.5))
    plt.plot(xs, ys, marker="o", color=METHOD_COLORS["steepest_edge"], linewidth=2)
    for x, y in zip(xs, ys):
        plt.annotate(f"{y:.6f}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9)

    plt.xlabel("number of faces (n)")
    plt.ylabel("avg min_plane (tightest-pair inversive distance)")
    plt.title("steepest_edge: average inversive distance vs. face count")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out = f"{OUT_DIR}/steepest_edge_avg_inversive_distance.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Wrote {out}")


def plot_avg_inversive_distance(summary):
    by_method = defaultdict(list)
    for s in summary:
        by_method[s["method"]].append((s["n_points"], s["avg_min_plane"]))

    plt.figure(figsize=(8, 5.5))
    for method, points in sorted(by_method.items()):
        points.sort()
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        plt.plot(xs, ys, marker="o", label=method, color=METHOD_COLORS.get(method))

    plt.axhline(1.0, color="black", linestyle="--", linewidth=1, label="touching threshold (overlap below this)")
    plt.xlabel("number of faces (n)")
    plt.ylabel("avg min_plane (tightest-pair inversive distance)")
    plt.title("Average inversive distance of the tightest pair vs. face count")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out = f"{OUT_DIR}/avg_inversive_distance_vs_n.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Wrote {out}")


def plot_margin_decay_loglog(summary):
    by_method = defaultdict(list)
    for s in summary:
        if s["avg_margin"] > 0:  # log scale needs positive margin
            by_method[s["method"]].append((s["n_points"], s["avg_margin"]))

    plt.figure(figsize=(8, 5.5))
    for method, points in sorted(by_method.items()):
        points.sort()
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        plt.plot(xs, ys, marker="o", label=method, color=METHOD_COLORS.get(method))

        if len(xs) >= 2:
            log_x = [math.log(x) for x in xs]
            log_y = [math.log(y) for y in ys]
            n = len(log_x)
            mean_x = sum(log_x) / n
            mean_y = sum(log_y) / n
            slope = (sum((lx - mean_x) * (ly - mean_y) for lx, ly in zip(log_x, log_y))
                     / sum((lx - mean_x) ** 2 for lx in log_x))
            print(f"log-log slope for {method}: {slope:.3f}  (audit's pre-fix steepest_edge slope was -1.996)")

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("number of faces (n, log scale)")
    plt.ylabel("avg margin = avg_min_plane - 1 (log scale)")
    plt.title("Margin decay vs. face count (log-log)")
    plt.legend()
    plt.grid(alpha=0.3, which="both")
    plt.tight_layout()
    out = f"{OUT_DIR}/margin_decay_loglog.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Wrote {out}\n")


def main():
    csv_paths = sys.argv[1:] or glob.glob(f"{OUT_DIR}/*_trials.csv")
    if not csv_paths:
        print(f"No trial CSVs found under {OUT_DIR}/")
        return

    rows = load_rows(csv_paths)
    if not rows:
        print("No usable rows (all CSVs pre-audit or empty).")
        return

    summary = build_summary(rows)
    write_summary_csv(summary)
    render_table_image(summary)
    plot_overlap_rate_by_method(summary)
    plot_steepest_edge_only(summary)
    plot_avg_inversive_distance(summary)
    plot_margin_decay_loglog(summary)


if __name__ == "__main__":
    main()
