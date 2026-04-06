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
"""

import sys
import os
from pathlib import Path

# Add koebepy root to path for imports
koebepy_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(koebepy_root))

from math import *
from random import *
from collections import defaultdict, deque
from statistics import mean, median
import heapq
import time
import argparse
import pickle

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
import join_unfolding_algorithms as join_algs
from WIP.visualize2D import display_dcel_2d
from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.spherical2scene import S2Scene
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


def _assign_search_order_from_tree(unfolding: DCEL, root_idx: int):
    """Assign deterministic BFS search_order values from parent pointers."""
    for v in unfolding.verts:
        v.search_order = -1

    if not unfolding.verts:
        return

    if root_idx < 0 or root_idx >= len(unfolding.verts):
        root_idx = 0

    child_dict = _build_child_dict(unfolding)
    queue = deque([unfolding.verts[root_idx]])
    order = 0

    while queue:
        v = queue.popleft()
        if v.search_order != -1:
            continue
        v.search_order = order
        order += 1
        for child in child_dict[v]:
            if child.search_order == -1:
                queue.append(child)


def _resolve_method_registry():
    """Return unfolding methods that produce (unfolding, root_idx)."""
    return {
        "bfs": generate_spanning_tree_bfs,
        "dfs": generate_spanning_tree_dfs,
        "join_bfs": join_algs.breadth_first_search_unfolding,
        "join_dfs": join_algs.depth_first_search_unfolding,
        "shortest_paths": join_algs.shortest_paths_unfolding,
        "min_degree_shortest_paths": join_algs.min_degree_shortest_paths_unfolding,
        "max_degree_shortest_paths": join_algs.max_degree_shortest_paths_unfolding,
        "shortest_shortest_paths": join_algs.shortest_shortest_paths_unfolding,
        "longest_shortest_paths": join_algs.longest_shortest_paths_unfolding,
        "normal_min": lambda packing: join_algs.normal_order_unfolding(packing, "min"),
        "normal_max": lambda packing: join_algs.normal_order_unfolding(packing, "max"),
        "normal_flat": lambda packing: join_algs.normal_order_unfolding(packing, "flat"),
        "normal_long": lambda packing: join_algs.normal_order_unfolding(packing, "long"),
    }


def _parse_method_selection(methods: list[str] | None):
    """Resolve requested methods, with support for aliases and comma lists."""
    registry = _resolve_method_registry()
    aliases = {
        "all": list(registry.keys()),
        "default": ["bfs", "dfs"],
    }

    if methods is None or len(methods) == 0:
        selected = aliases["default"]
    else:
        expanded = []
        for item in methods:
            for token in item.split(","):
                token = token.strip().lower()
                if token:
                    expanded.append(token)

        selected = []
        for token in expanded:
            if token in aliases:
                selected.extend(aliases[token])
            else:
                selected.append(token)

    unknown = [m for m in selected if m not in registry]
    if unknown:
        valid = ", ".join(sorted(registry.keys()))
        raise ValueError(f"Unknown methods: {unknown}. Valid methods are: {valid}, plus aliases: all, default")

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(selected)), registry


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


def save_overlapping_dcel(
    packing: DCEL,
    unfolding: DCEL,
    mode: str,
    trial_index: int,
    trial_seed: int,
    base_seed: int,
    root_idx: int,
    overlaps: list[tuple[int, int]],
    output_dir: str = "overlapping_packings"
):
    """Save both packing and unfolding DCEL structures when overlapping is detected.
    
    Args:
        packing: The original coin packing (spherical DCEL)
        unfolding: The unfolded plane DCEL with overlaps
        mode: Unfolding method name (e.g., 'bfs', 'dfs')
        trial_index: Trial number
        trial_seed: Random seed for this trial
        base_seed: Base seed for the entire trial run
        root_idx: Root vertex index of the unfolding tree
        overlaps: List of overlapping circle pairs
        output_dir: Directory to store the pickled DCEL files
    
    Returns:
        dict with saved file paths and metadata
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Prepare metadata
    num_overlaps = len(overlaps)
    packing_size = len(packing.verts)
    
    # Create descriptive filenames - include base_seed for unique identification
    base_name = f"base{base_seed}_trial{trial_index:04d}_{mode}_{num_overlaps}overlaps_{packing_size}verts"
    packing_filename = os.path.join(output_dir, f"{base_name}_packing.pkl")
    unfolding_filename = os.path.join(output_dir, f"{base_name}_unfolding.pkl")
    metadata_filename = os.path.join(output_dir, f"{base_name}_metadata.txt")
    
    # Mark indices before pickling (required by DCEL)
    packing.markIndices()
    unfolding.markIndices()
    
    # Save packing DCEL
    with open(packing_filename, 'wb') as f:
        pickle.dump(packing, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    # Save unfolding DCEL
    with open(unfolding_filename, 'wb') as f:
        pickle.dump(unfolding, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    # Save metadata as human-readable text
    with open(metadata_filename, 'w') as f:
        f.write(f"Overlapping DCEL Detection\n")
        f.write(f"==========================\n")
        f.write(f"Base Seed: {base_seed}\n")
        f.write(f"Trial: {trial_index}\n")
        f.write(f"Trial Seed: {trial_seed}\n")
        f.write(f"Method: {mode}\n")
        f.write(f"Root vertex index: {root_idx}\n")
        f.write(f"Number of vertices: {packing_size}\n")
        f.write(f"Number of overlapping pairs detected: {num_overlaps}\n")
        f.write(f"First 5 overlapping pairs: {overlaps[:5]}\n\n")
        f.write(f"To load these DCEL structures:\n")
        f.write(f"  import pickle\n")
        f.write(f"  with open('{packing_filename}', 'rb') as f:\n")
        f.write(f"      packing = pickle.load(f)\n")
        f.write(f"  with open('{unfolding_filename}', 'rb') as f:\n")
        f.write(f"      unfolding = pickle.load(f)\n")
        f.write(f"  packing.markIndices()\n")
        f.write(f"  unfolding.markIndices()\n")
    
    print(f"  Saved overlapping DCEL: {packing_filename}")
    print(f"  Saved overlapping DCEL: {unfolding_filename}")
    print(f"  Saved metadata: {metadata_filename}")
    
    return {
        "packing_file": packing_filename,
        "unfolding_file": unfolding_filename,
        "metadata_file": metadata_filename,
        "trial": trial_index,
        "method": mode,
        "base_seed": base_seed,
        "trial_seed": trial_seed,
        "num_overlaps": num_overlaps,
        "num_verts": packing_size,
        "root_idx": root_idx,
    }


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


def visualize_trial_unfolding(unfolding: DCEL, mode: str, trial_index: int, root_idx: int, overlaps: list[tuple[int, int]]):
    """Visualize one trial unfolding, regardless of overlap status."""
    overlap_vertices = {idx for i, j in overlaps for idx in (i, j)}
    primary_overlap_vertices = set(overlaps[0]) if overlaps else set()

    gray_style = makeStyle(stroke=(130, 130, 130), strokeWeight=1.0, fill=None)
    green_style = makeStyle(stroke=(0, 165, 0), strokeWeight=2.4, fill=None)
    orange_style = makeStyle(stroke=(255, 140, 0), strokeWeight=2.0, fill=None)
    red_style = makeStyle(stroke=(220, 0, 0), strokeWeight=2.4, fill=None)
    purple_style = makeStyle(stroke=(170, 0, 170), strokeWeight=2.7, fill=None)
    tree_style = makeStyle(stroke=(210, 210, 210), strokeWeight=0.6, fill=None)

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

    title_suffix = f"overlap_pairs={len(overlaps)}" if overlaps else "no-overlap"
    print(
        f"Visualizing trial unfolding: mode={mode.upper()} trial={trial_index} "
        f"root={root_idx} {title_suffix}"
    )

    display_dcel_2d(
        unfolding,
        viewer=viewer,
        run=True,
        title=f"Trial unfolding ({mode.upper()} trial {trial_index}, {title_suffix})",
        show_vertices=True,
        vertex_style=vertex_style,
        show_edges=False,
        show_tree=True,
        tree_style=tree_style,
        root_idx=root_idx,
        root_at_origin=True,
        pan_and_zoom=True,
        scale=130,
    )


def visualize_trial_packing(packing: DCEL, trial_index: int, trial_seed: int):
    """Visualize the original spherical circle packing for one trial."""
    print(
        f"Visualizing trial packing: trial={trial_index} seed={trial_seed} "
        f"verts={len(packing.verts)}"
    )
    print("Legend: red=root(idx 0), black=all other circles.")

    black_style = makeStyle(stroke=(0, 0, 0), strokeWeight=1.4, fill=None)
    red_style = makeStyle(stroke=(220, 0, 0), strokeWeight=2.2, fill=None)

    scene_s2 = S2Scene(
        title=f"Trial packing (trial {trial_index}, seed {trial_seed})",
        show_sphere=False,
    )
    scene_s2.addAll([
        (v.data, red_style if v.idx == 0 else black_style)
        for v in packing.verts
        if v.data is not None
    ])

    viewer.add_scene(scene_s2)
    viewer.run()


def evaluate_algorithm(packing: DCEL, mode: str, pair_scope: str = "all", include_tree_edges: bool = False):
    """Run one unfolding method, place geometry, and summarize metrics."""
    registry = _resolve_method_registry()
    if mode not in registry:
        raise ValueError(f"Unknown unfolding method: {mode}")

    unfolding, root_idx = registry[mode](packing)

    if not isinstance(root_idx, int):
        raise ValueError(f"Method '{mode}' did not return an integer root index")
    if root_idx < 0 or root_idx >= len(unfolding.verts):
        raise ValueError(f"Method '{mode}' returned out-of-range root index {root_idx}")

    _assign_search_order_from_tree(unfolding, root_idx)
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


def compare_methods(
        methods: list[str] | None = None,
        n_points: int = 50,
        n_iterations: int = 1000,
        trials: int = 3,
        pair_scope: str = "all",
        include_tree_edges: bool = False,
    visualize_trial_packing_each_trial: bool = False,
    visualize_each_trial: bool = False,
        visualize_first_overlap: bool = True,
        base_seed: int | None = None,
        save_overlapping_decls: bool = True,
        overlapping_output_dir: str = "overlapping_packings",
):
    """Run multiple trials and print summaries for selected unfolding methods."""
    selected_methods, _registry = _parse_method_selection(methods)
    runs_by_method = {name: [] for name in selected_methods}
    profiles_by_method = {name: [] for name in selected_methods}
    has_visualized_overlap = False
    resolved_base_seed = int(time.time_ns()) if base_seed is None else int(base_seed)
    seed_rng = Random(resolved_base_seed)
    trial_seeds = []
    saved_overlapping_decls = []

    print("\nMethods under test:")
    print(", ".join(selected_methods))

    print("\nReproducibility setup")
    print(f"base_seed={resolved_base_seed}")
    print("(reuse this base_seed to reproduce the exact same trial sequence)")

    for t in range(1, trials + 1):
        trial_seed = seed_rng.randrange(0, 2**63)
        trial_seeds.append(trial_seed)
        seed(trial_seed)

        print(f"\nTrial {t}/{trials} seed={trial_seed}")
        packing, _ = generate_coin_polygon(n_points, n_iterations)

        if visualize_trial_packing_each_trial:
            visualize_trial_packing(packing, t, trial_seed)

        for method_name in selected_methods:
            try:
                summary, profile, unfolding, root_idx, overlaps = evaluate_algorithm(
                    packing,
                    method_name,
                    pair_scope,
                    include_tree_edges,
                )
            except Exception as ex:
                print(f"{method_name.upper():<24} ERROR: {ex}")
                continue
            runs_by_method[method_name].append(summary)
            profiles_by_method[method_name].append(profile)

            if visualize_each_trial:
                visualize_trial_unfolding(unfolding, method_name, t, root_idx, overlaps)

            if visualize_first_overlap and not has_visualized_overlap and len(overlaps) > 0:
                visualize_overlapping_unfolding(unfolding, method_name, t, root_idx, overlaps)
                has_visualized_overlap = True

            if save_overlapping_decls and len(overlaps) > 0:
                save_result = save_overlapping_dcel(
                    packing,
                    unfolding,
                    method_name,
                    t,
                    trial_seed,
                    resolved_base_seed,
                    root_idx,
                    overlaps,
                    output_dir=overlapping_output_dir,
                )
                saved_overlapping_decls.append(save_result)

            print(_line(summary))

    print("\nAggregate")
    for method_name in selected_methods:
        print(_aggregate_line(method_name, runs_by_method[method_name]))

    print("\nViolation localization (rate by bin):")
    combined_profiles = {}
    for method_name in selected_methods:
        combined_profiles[method_name] = _combine_profiles(method_name, profiles_by_method[method_name])
        print(_profile_line(combined_profiles[method_name], method_name))

    print("\nReproducibility seed record")
    print(f"base_seed={resolved_base_seed}")
    print(f"trial_seeds={trial_seeds}")

    if save_overlapping_decls and saved_overlapping_decls:
        print(f"\n{len(saved_overlapping_decls)} overlapping DCEL(s) saved to '{overlapping_output_dir}/'")

    return {
        "methods": selected_methods,
        "base_seed": resolved_base_seed,
        "trial_seeds": trial_seeds,
        "runs": runs_by_method,
        "profiles": combined_profiles,
        "saved_overlapping_decls": saved_overlapping_decls,
    }


def compare_bfs_dfs(
        n_points: int = 50,
        n_iterations: int = 1000,
        trials: int = 3,
        pair_scope: str = "all",
        include_tree_edges: bool = False,
    visualize_trial_packing_each_trial: bool = False,
    visualize_each_trial: bool = False,
        visualize_first_overlap: bool = True,
        base_seed: int | None = None,
        save_overlapping_decls: bool = True,
        overlapping_output_dir: str = "overlapping_packings",
):
    """Backward-compatible wrapper: run compare_methods with BFS and DFS.

    Reproducibility model:
    - If base_seed is None, use time.time_ns() for a unique run seed.
    - Per-trial seeds are then deterministically generated from base_seed.
    - The full seed record is printed and returned to allow exact reruns.
    """
    result = compare_methods(
        methods=["bfs", "dfs"],
        n_points=n_points,
        n_iterations=n_iterations,
        trials=trials,
        pair_scope=pair_scope,
        include_tree_edges=include_tree_edges,
        visualize_trial_packing_each_trial=visualize_trial_packing_each_trial,
        visualize_each_trial=visualize_each_trial,
        visualize_first_overlap=visualize_first_overlap,
        base_seed=base_seed,
        save_overlapping_decls=save_overlapping_decls,
        overlapping_output_dir=overlapping_output_dir,
    )

    return {
        "base_seed": result["base_seed"],
        "trial_seeds": result["trial_seeds"],
        "bfs_runs": result["runs"].get("bfs", []),
        "dfs_runs": result["runs"].get("dfs", []),
        "bfs_profile": result["profiles"].get("bfs", {}),
        "dfs_profile": result["profiles"].get("dfs", {}),
        "saved_overlapping_decls": result.get("saved_overlapping_decls", []),
    }


def _build_arg_parser():
    """CLI parser for selecting unfolding methods and run options."""
    parser = argparse.ArgumentParser(description="Inversive-distance analysis across unfolding methods")
    parser.add_argument(
        "--methods",
        nargs="+",
        default=["default"],
        help=(
            "Methods to test (space or comma separated). "
            "Use aliases: default (bfs,dfs), all."
        ),
    )
    parser.add_argument("--n-points", type=int, default=50)
    parser.add_argument("--n-iterations", type=int, default=1000)
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--pair-scope", choices=["all", "neighbors", "non_neighbors"], default="all")
    parser.add_argument("--include-tree-edges", action="store_true")
    parser.add_argument("--no-visualize-first-overlap", action="store_true")
    parser.add_argument("--base-seed", type=int, default=1774411564778725000)
    parser.add_argument("--list-methods", action="store_true", help="Print available method names and exit")
    return parser


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
    result = compare_methods(
        methods=["dfs", "bfs", "shortest_paths", ],
        n_points=50,
        n_iterations=1000,
        trials=250,
        pair_scope="all",
        include_tree_edges=False,
        visualize_trial_packing_each_trial=False,
        visualize_each_trial=False, #this shows the unfolding for each trial
        visualize_first_overlap=True,
        base_seed=1774895576523358000
    )

    # seed with overlap for dfs: 1774895576523358000, this overlapping does not happen every time which is something I need to look into

    # Edit the compare_methods(...) arguments above to choose methods/settings.
    # Available methods:
    # bfs, dfs, join_bfs, join_dfs, shortest_paths,
    # min_degree_shortest_paths, max_degree_shortest_paths,
    # shortest_shortest_paths, longest_shortest_paths,
    # normal_min, normal_max, normal_flat, normal_long
    # ["bfs", "dfs", "shortest_paths", "min_degree_shortest_paths",
    #              "max_degree_shortest_paths", "shortest_shortest_paths",
    #              "longest_shortest_paths", "normal_min", "normal_max",
    #              "normal_flat", "normal_long"]

    print("\nRerun note")
    print(f"To reproduce this run exactly, call compare_methods(..., base_seed={result['base_seed']})")
