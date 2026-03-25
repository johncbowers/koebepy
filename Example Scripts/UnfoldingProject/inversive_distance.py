"""
IMPORTANT WARNING:
    To get this code running you will need to comment out lines 125 and on of coin_unfolding_modular

Compare BFS and DFS unfolding trees using inversive-distance metrics.

key idea: same packing → two trees → two unfoldings
→ pairwise sphere-vs-plane comparison → trial summaries → cross-trial averages.

Quick use:
1) Run this file from the segmented_approach directory.
2) Adjust parameters in the __main__ block (n_points, n_iterations, trials,
   pair_scope, include_tree_edges).
3) Read per-trial and aggregate BFS/DFS summaries printed to the terminal.

Output format:
- Per-trial lines: one line each for BFS and DFS on the same packing.
- Aggregate lines: average values across all trials for BFS and DFS.

Pair scopes:
- "all": every unordered pair (except tree edges unless enabled)
- "neighbors": only graph-neighbor pairs in the packing
- "non_neighbors": only non-neighbor pairs

Aggregate variables and interpretation:
- avg_pairs: average number of pair comparisons included per trial.
- avg_min_plane: average of the minimum plane inversive distance seen each trial.
    Larger is generally safer (fewer near-overlap pairs in unfolded geometry).
- avg_min_sphere: average of the minimum sphere inversive distance for the same
    tracked pairs in the original packing (baseline reference).
- avg_min_delta: average of minimum (plane - sphere) each trial.
    Less negative (or more positive) is generally better.
- avg_mean_delta: average of per-trial mean (plane - sphere) over all tracked
    pairs. Captures overall unfolding behavior.
    (delta = plane - sphere)
    (Positive delta means that pair is more separated in the unfolding 
    plane than in the spherical packing.)
- avg_median_delta: average of per-trial median (plane - sphere) over all
    tracked pairs. More robust to outlier pairs.
- avg_viol: average count of violations where plane < sphere.
    Smaller is generally better.

Note on startup pause:
This file imports generate_coin_polygon and unfolding_geometry_from_tree from
coin_unfolding_modular.py. That module currently executes visualization code at
import time (including viewer.run()), which can block before trials print.

Aggregate results over 100 trials:
n_points=50,
n_iterations=1000,
trials=1000,
pair_scope="all",
include_tree_edges=False,
Aggregate
BFS  avg_pairs=1176.0 avg_min_plane=1.036876 avg_min_sphere=1.000000 avg_min_delta=0.036876 avg_mean_delta=79.331728 avg_median_delta=25.536828 avg_viol=0.00
DFS  avg_pairs=1176.0 avg_min_plane=1.028056 avg_min_sphere=1.000000 avg_min_delta=-0.041914 avg_mean_delta=149.546968 avg_median_delta=38.704641 avg_viol=0.03

Aggregate results over 1000 trials: 
n_points=50,
n_iterations=1000,
trials=1000,
pair_scope="all",
include_tree_edges=False,
Aggregate
BFS  avg_pairs=1176.0 avg_min_plane=1.033898 avg_min_sphere=1.000000 avg_min_delta=0.033884 avg_mean_delta=82.385332 avg_median_delta=25.631228 avg_viol=0.00
DFS  avg_pairs=1176.0 avg_min_plane=1.026065 avg_min_sphere=1.000000 avg_min_delta=0.020900 avg_mean_delta=154.245335 avg_median_delta=38.896101 avg_viol=0.02

DFS has 0.0017% pair-violation rate over 1000 trials
BFS has 0% pair violation rate trials

Trail of where overlapping occurs (over 1000 trails):
Aggregate
BFS  avg_pairs=1176.0 avg_min_plane=1.034512 avg_min_sphere=0.999999 avg_min_delta=0.034504 avg_mean_delta=81.144180 avg_median_delta=25.711167 avg_viol=0.00
DFS  avg_pairs=1176.0 avg_min_plane=1.023833 avg_min_sphere=0.999999 avg_min_delta=0.012581 avg_mean_delta=151.841945 avg_median_delta=38.574268 avg_viol=0.01

Violation localization (rate by bin):
BFS  depth[early:0/14989(0.0000) mid:0/425520(0.0000) late:0/735491(0.0000)] order[early:0/120000(0.0000) mid:0/376000(0.0000) late:0/680000(0.0000)]
DFS  depth[early:2/160427(0.0000) mid:9/400267(0.0000) late:3/615306(0.0000)] order[early:1/120000(0.0000) mid:6/376000(0.0000) late:7/680000(0.0000)]
"""

from math import *
from random import *
from collections import defaultdict, deque
from statistics import mean, median
import heapq

from koebe.algorithms.circlepackings.layout import canonical_spherical_projection, compute_tangencies
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *

from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

from coin_unfolding_modular import (
    generate_coin_polygon,
    unfolding_geometry_from_tree,
)
from koebepy.WIP.visualize2D import display_dcel_2d
from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.euclidean2scene import makeStyle


def generate_spanning_tree_bfs(packing: DCEL):
    """Build a BFS spanning tree over the packing and store parent pointers.

    Returns a duplicated DCEL (unfolding) with parent links set and root index 0.
    """
    unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
    unfolding.markIndices()

    for v in unfolding.verts:
        v.parent = None

    root_idx = 0
    root = unfolding.verts[root_idx]
    root.search_order = 0
    order_counter = 1

    placed = {root}
    queue = deque(placed)

    while queue:
        v = queue.popleft()
        for neighbor in v.neighbors():
            if neighbor not in placed:
                neighbor.parent = v
                neighbor.search_order = order_counter
                order_counter += 1
                placed.add(neighbor)
                queue.append(neighbor)

    return unfolding, root_idx


def generate_spanning_tree_dfs(packing: DCEL):
    """Build a DFS spanning tree over the packing and store parent pointers.

    Returns a duplicated DCEL (unfolding) with parent links set and root index 0.
    """
    unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
    unfolding.markIndices()

    for v in unfolding.verts:
        v.parent = None

    root_idx = 0
    root = unfolding.verts[root_idx]
    root.search_order = 0
    order_counter = 1

    placed = {root}
    stack = [root]

    while stack:
        v = stack.pop()
        for neighbor in v.neighbors():
            if neighbor not in placed:
                neighbor.parent = v
                neighbor.search_order = order_counter
                order_counter += 1
                placed.add(neighbor)
                stack.append(neighbor)

    return unfolding, root_idx


def _build_child_dict(unfolding: DCEL):
    """Convert vertex.parent links into a parent->children dictionary."""
    child_dict = defaultdict(list)
    for v in unfolding.verts:
        if v.parent is not None:
            child_dict[v.parent].append(v)
    return child_dict


def _neighbor_pair_set(packing: DCEL):
    """Return set of unordered vertex-index pairs that share an edge in packing."""
    pairs = set()
    for v in packing.verts:
        for n in v.neighbors():
            i, j = sorted((v.idx, n.idx))
            pairs.add((i, j))
    return pairs


def _vertex_depths(unfolding: DCEL, root_idx: int):
    """Return dict vertex_idx -> depth in the spanning tree."""
    depths = {root_idx: 0}
    child_dict = _build_child_dict(unfolding)
    queue = deque([unfolding.verts[root_idx]])

    while queue:
        parent = queue.popleft()
        parent_depth = depths[parent.idx]
        for child in child_dict[parent]:
            depths[child.idx] = parent_depth + 1
            queue.append(child)
    return depths


def _tercile_label(value: int, max_value: int):
    """Bin an index-like value into early/mid/late thirds."""
    if max_value <= 0:
        return "early"
    ratio = value / max_value
    if ratio < (1.0 / 3.0):
        return "early"
    if ratio < (2.0 / 3.0):
        return "mid"
    return "late"


def track_inversive_pairs(
    packing: DCEL,
    unfolding: DCEL,
    root_idx: int,
    pair_scope: str = "all",
    include_tree_edges: bool = False,
):
    """Collect pairwise inversive-distance measurements for the chosen pair scope.

    Each row includes indices i, j plus sphere value, plane value, and delta.
    """
    neighbor_pairs = _neighbor_pair_set(packing)
    depths = _vertex_depths(unfolding, root_idx)
    max_depth = max(depths.values()) if depths else 0
    max_order = max(getattr(v, "search_order", 0) for v in unfolding.verts) if unfolding.verts else 0
    rows = []

    for i in range(len(unfolding.verts) - 1):
        for j in range(i + 1, len(unfolding.verts)):
            vi = unfolding.verts[i]
            vj = unfolding.verts[j]

            if vi.data is None or vj.data is None:
                continue

            is_tree_edge = (vi.parent == vj) or (vj.parent == vi)
            if not include_tree_edges and is_tree_edge:
                continue

            is_neighbor = (i, j) in neighbor_pairs
            if pair_scope == "neighbors" and not is_neighbor:
                continue
            if pair_scope == "non_neighbors" and is_neighbor:
                continue

            sphere_id = packing.verts[i].data.inversiveDistTo(packing.verts[j].data)
            plane_id = vi.data.inversiveDistTo(vj.data)
            depth_pair = max(depths.get(i, 0), depths.get(j, 0))
            order_pair = max(getattr(vi, "search_order", 0), getattr(vj, "search_order", 0))
            rows.append({
                "i": i,
                "j": j,
                "sphere": sphere_id,
                "plane": plane_id,
                "delta": plane_id - sphere_id,
                "depth_bin": _tercile_label(depth_pair, max_depth),
                "order_bin": _tercile_label(order_pair, max_order),
            })

    return rows


def summarize_inversive_rows(rows, label: str):
    """Summarize pairwise rows into aggregate statistics for one algorithm run."""
    if len(rows) == 0:
        return {
            "label": label,
            "pair_count": 0,
            "min_sphere": float("nan"),
            "min_plane": float("nan"),
            "min_delta": float("nan"),
            "max_delta": float("nan"),
            "mean_delta": float("nan"),
            "median_delta": float("nan"),
            "violations_plane_lt_sphere": 0,
        }

    sphere_vals = [r["sphere"] for r in rows]
    plane_vals = [r["plane"] for r in rows]
    deltas = [r["delta"] for r in rows]
    return {
        "label": label,
        "pair_count": len(rows),
        "min_sphere": min(sphere_vals),
        "min_plane": min(plane_vals),
        "min_delta": min(deltas),
        "max_delta": max(deltas),
        "mean_delta": mean(deltas),
        "median_delta": median(deltas),
        "violations_plane_lt_sphere": sum(1 for r in rows if r["plane"] < r["sphere"]),
    }


def summarize_violation_profile(rows, label: str):
    """Summarize where violations occur by depth and search-order terciles."""
    bins = ("early", "mid", "late")
    profile = {
        "label": label,
        "total_pairs": len(rows),
        "total_violations": 0,
        "depth": {b: {"pairs": 0, "viol": 0} for b in bins},
        "order": {b: {"pairs": 0, "viol": 0} for b in bins},
    }

    for row in rows:
        is_viol = row["plane"] < row["sphere"]
        if is_viol:
            profile["total_violations"] += 1

        depth_bin = row["depth_bin"]
        order_bin = row["order_bin"]

        profile["depth"][depth_bin]["pairs"] += 1
        profile["order"][order_bin]["pairs"] += 1

        if is_viol:
            profile["depth"][depth_bin]["viol"] += 1
            profile["order"][order_bin]["viol"] += 1

    return profile


def _combine_profiles(label: str, profiles: list[dict]):
    """Aggregate multiple profile dictionaries into one combined profile."""
    bins = ("early", "mid", "late")
    combined = {
        "label": label,
        "total_pairs": 0,
        "total_violations": 0,
        "depth": {b: {"pairs": 0, "viol": 0} for b in bins},
        "order": {b: {"pairs": 0, "viol": 0} for b in bins},
    }

    for profile in profiles:
        combined["total_pairs"] += profile["total_pairs"]
        combined["total_violations"] += profile["total_violations"]
        for b in bins:
            combined["depth"][b]["pairs"] += profile["depth"][b]["pairs"]
            combined["depth"][b]["viol"] += profile["depth"][b]["viol"]
            combined["order"][b]["pairs"] += profile["order"][b]["pairs"]
            combined["order"][b]["viol"] += profile["order"][b]["viol"]

    return combined


def _profile_line(profile: dict, mode: str):
    """Format one profile line with violation rates by early/mid/late bins."""
    def fmt(section: str, bin_name: str):
        pairs = profile[section][bin_name]["pairs"]
        viol = profile[section][bin_name]["viol"]
        rate = (viol / pairs) if pairs > 0 else 0.0
        return f"{bin_name}:{viol}/{pairs}({rate:.4f})"

    return (
        f"{mode.upper():<4} depth[{fmt('depth', 'early')} {fmt('depth', 'mid')} {fmt('depth', 'late')}] "
        f"order[{fmt('order', 'early')} {fmt('order', 'mid')} {fmt('order', 'late')}]"
    )


def find_overlapping_pairs(unfolding: DCEL, tol: float = 1e-10):
    """Return list of overlapping circle pairs (i, j) in the unfolded plane."""
    overlaps = []
    for i in range(len(unfolding.verts) - 1):
        for j in range(i + 1, len(unfolding.verts)):
            vi = unfolding.verts[i]
            vj = unfolding.verts[j]
            if vi.data is None or vj.data is None:
                continue
            distance = vi.data.center.distTo(vj.data.center)
            sum_radii = vi.data.radius + vj.data.radius
            if sum_radii - tol > distance:
                overlaps.append((i, j))
    return overlaps


def visualize_overlapping_unfolding(unfolding: DCEL, mode: str, trial_index: int, root_idx: int, overlaps: list[tuple[int, int]]):
    """Visualize one unfolding that contains overlaps."""
    print(
        f"\nFirst overlapping unfolding found: mode={mode.upper()} trial={trial_index} "
        f"overlap_pairs={len(overlaps)}"
    )
    print(f"Example overlapping pair indices: {overlaps[:5]}")
    print(f"Unfolding root vertex index: {root_idx}")
    print("Use trackpad/mousewheel to zoom and drag to pan in the overlap scene.")
    print("Legend: red=primary overlap pair, orange=other overlap circles, green=root, purple=root+overlap, gray=other circles.")

    overlap_vertices = {idx for i, j in overlaps for idx in (i, j)}
    primary_overlap_vertices = set(overlaps[0]) if overlaps else set()
    focus_idx = overlaps[0][0] if overlaps else root_idx
    gray_style = makeStyle(stroke=(185, 185, 185), strokeWeight=1, fill=None)
    red_style = makeStyle(stroke=(255, 0, 0), strokeWeight=2.25, fill=None)
    orange_style = makeStyle(stroke=(255, 140, 0), strokeWeight=1.8, fill=None)
    green_style = makeStyle(stroke=(0, 170, 0), strokeWeight=2.6, fill=None)
    purple_style = makeStyle(stroke=(190, 0, 190), strokeWeight=2.8, fill=None)
    tree_style = makeStyle(stroke=(220, 220, 220), strokeWeight=0.6, fill=None)

    def vertex_style(vertex, _depth=0):
        if vertex.idx == root_idx and vertex.idx in overlap_vertices:
            return purple_style
        if vertex.idx == root_idx:
            return green_style
        if vertex.idx in primary_overlap_vertices:
            return red_style
        if vertex.idx in overlap_vertices:
            return orange_style
        return gray_style

    display_dcel_2d(
        unfolding,
        viewer=viewer,
        run=True,
        title=f"First overlapping unfolding ({mode.upper()} trial {trial_index})",
        show_vertices=True,
        vertex_style=vertex_style,
        show_edges=False,
        show_tree=True,
        tree_style=tree_style,
        root_idx=focus_idx,
        root_at_origin=True,
        pan_and_zoom=True,
        scale=130,
    )


def evaluate_algorithm(packing: DCEL, mode: str, pair_scope: str = "all", include_tree_edges: bool = False):
    """Run one algorithm (BFS or DFS), place unfolding geometry, and summarize metrics."""
    if mode == "bfs":
        unfolding, root_idx = generate_spanning_tree_bfs(packing)
    elif mode == "dfs":
        unfolding, root_idx = generate_spanning_tree_dfs(packing)
    else:
        raise ValueError(f"mode must be 'bfs' or 'dfs', got {mode}")

    child_dict = _build_child_dict(unfolding)
    unfolding_geometry_from_tree(packing, unfolding, root_idx)

    rows = track_inversive_pairs(
        packing,
        unfolding,
        root_idx,
        pair_scope=pair_scope,
        include_tree_edges=include_tree_edges,
    )
    overlaps = find_overlapping_pairs(unfolding)
    return summarize_inversive_rows(rows, mode), summarize_violation_profile(rows, mode), unfolding, root_idx, overlaps


def compare_bfs_dfs(
        n_points: int = 50,
        n_iterations: int = 1000,
        trials: int = 3,
        pair_scope: str = "all",
        include_tree_edges: bool = False,
    visualize_first_overlap: bool = True,
):
    """Run multiple trials and print side-by-side BFS/DFS inversive summaries."""
    bfs_runs = []
    dfs_runs = []
    bfs_profiles = []
    dfs_profiles = []
    has_visualized_overlap = False

    for t in range(1, trials + 1):
        print(f"\nTrial {t}/{trials}")
        packing = generate_coin_polygon(n_points, n_iterations)

        bfs_summary, bfs_profile, bfs_unfolding, bfs_root_idx, bfs_overlaps = evaluate_algorithm(
            packing, "bfs", pair_scope, include_tree_edges
        )
        dfs_summary, dfs_profile, dfs_unfolding, dfs_root_idx, dfs_overlaps = evaluate_algorithm(
            packing, "dfs", pair_scope, include_tree_edges
        )
        bfs_runs.append(bfs_summary)
        dfs_runs.append(dfs_summary)
        bfs_profiles.append(bfs_profile)
        dfs_profiles.append(dfs_profile)

        if visualize_first_overlap and not has_visualized_overlap:
            if len(bfs_overlaps) > 0:
                visualize_overlapping_unfolding(bfs_unfolding, "bfs", t, bfs_root_idx, bfs_overlaps)
                has_visualized_overlap = True
            elif len(dfs_overlaps) > 0:
                visualize_overlapping_unfolding(dfs_unfolding, "dfs", t, dfs_root_idx, dfs_overlaps)
                has_visualized_overlap = True

        print(_line(bfs_summary))
        print(_line(dfs_summary))

    print("\nAggregate")
    print(_aggregate_line("bfs", bfs_runs))
    print(_aggregate_line("dfs", dfs_runs))

    print("\nViolation localization (rate by bin):")
    print(_profile_line(_combine_profiles("bfs", bfs_profiles), "bfs"))
    print(_profile_line(_combine_profiles("dfs", dfs_profiles), "dfs"))


def _line(summary: dict):
    """Format one per-trial summary line for terminal output."""
    return (
        f"{summary['label'].upper():<4} pairs={summary['pair_count']:<6} "
        f"min_plane={summary['min_plane']:.6f} min_sphere={summary['min_sphere']:.6f} "
        f"min_delta={summary['min_delta']:.6f} mean_delta={summary['mean_delta']:.6f} "
        f"median_delta={summary['median_delta']:.6f} viol(plane<sphere)={summary['violations_plane_lt_sphere']}"
    )


def _aggregate_line(label: str, summaries: list[dict]):
    """Format aggregate averages across multiple trials."""
    if len(summaries) == 0:
        return f"{label.upper():<4} no data"

    return (
        f"{label.upper():<4} "
        f"avg_pairs={mean(s['pair_count'] for s in summaries):.1f} "
        f"avg_min_plane={mean(s['min_plane'] for s in summaries):.6f} "
        f"avg_min_sphere={mean(s['min_sphere'] for s in summaries):.6f} "
        f"avg_min_delta={mean(s['min_delta'] for s in summaries):.6f} "
        f"avg_mean_delta={mean(s['mean_delta'] for s in summaries):.6f} "
        f"avg_median_delta={mean(s['median_delta'] for s in summaries):.6f} "
        f"avg_viol={mean(s['violations_plane_lt_sphere'] for s in summaries):.2f}"
    )


if __name__ == "__main__":
    compare_bfs_dfs(
        n_points=50,
        n_iterations=1000,
        trials=1000,
        pair_scope="all",
        include_tree_edges=False,
    )
