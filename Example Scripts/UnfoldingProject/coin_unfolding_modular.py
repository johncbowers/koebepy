# Import geometries
import argparse
import json
import math
import time
import sys
import io
from pathlib import Path

from koebe.algorithms.circlepackings.layout import canonical_spherical_projection, compute_tangencies, canonical_spherical_layout
from koebe.algorithms.circlepackings.newton_packing import newton_packing
from koebe.datastructures.dcel import _restore_dcel
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *

# Import convex hull, circle packing, and tutte embedding algorithms
from koebe.algorithms.incrementalConvexHull import randomConvexHullE3
from koebe.algorithms.hypPacker import *

# General imports

# Scene and Visualization libraries
from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle
from koebe.graphics.scenes.euclidean2scene import E2Scene

from cut_unfolding_algorithms import *
from join_unfolding_algorithms import *
from cut_graph_construction import *
from build_unfolding import *
from unfolding_testing import *

# Optional MATLAB support - only needed for build_dcel_with_gop functions
try:
    from matlab_packing_generation import *
except ModuleNotFoundError:
    # MATLAB Engine not installed - generate_coin_polygon will still work
    # but build_dcel_with_gop functions will fail if called
    pass


n_points = 100
n_iterations = 1000


def generate_coin_polygon(n_points, n_iterations, seed=42):
    """
    Generates a coin polygon. Returns tuple of (join_graph, cut_graph).
    :param n_points:
    :param n_iterations:
    :return: ()
    """
    start_time = time.time()
    convex_hull = randomConvexHullE3(n_points)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time for computing randomConvexHullE3: {elapsed_time}")
    convex_hull.outerFace = convex_hull.faces[0]  # Arbitrarily select an outer face.

    start_time = time.time()
    hyp_packing, _ = maximalPacking(
        convex_hull,
        num_passes=n_iterations,
        tolerance=float(3e-8)
    )
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time for computing maximalPacking: {elapsed_time}")
    # Suppress verbose output from canonical_spherical_projection computation
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    start_time = time.time()
    try:
        packing = canonical_spherical_projection(hyp_packing)
    finally:
        end_time = time.time()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    elapsed_time = end_time - start_time
    print(f"Elapsed time for computing canonical_spherical_projection: {elapsed_time}")
    packing.markIndices()

    compute_tangencies(packing)
    return packing, convex_hull

def generate_coin_polygon_orick(n_points, n_iterations, seed=42):
    """
    Generates a coin polygon using Orick's Newton method (faster packing algorithm).
    Returns tuple of (packing, convex_hull).
    :param n_points: Number of points for convex hull
    :param n_iterations: Number of iterations for canonical layout refinement
    :param seed: Random seed (default 42)
    :return: (packing, convex_hull) tuple
    """
    start_time = time.time()
    convex_hull = randomConvexHullE3(n_points)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time for computing randomConvexHullE3: {elapsed_time}")
    convex_hull.outerFace = convex_hull.faces[0]  # Arbitrarily select an outer face.

    start_time = time.time()
    packing = newton_packing(convex_hull, tol=3e-8, quiet=True)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time for computing newton_packing (Orick's Newton method): {elapsed_time}")

    # Suppress verbose output from canonical_spherical_projection computation
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    start_time = time.time()
    try:
        packing = canonical_spherical_layout(packing, n_iterations=20)
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    print(f"Elapsed time for computing canonical_spherical_layout: {elapsed_time}")
    packing.markIndices()

    compute_tangencies(packing)
    return packing, convex_hull


def packing_from_state_json(state_json_path, n_iterations=1000, tol=3e-12, max_iter=1000, boundary_radius=1.0):
    """Load a koebepy DCEL state JSON and build a packing via Orick's Newton method."""
    state_path = Path(state_json_path)
    with state_path.open("r", encoding="utf-8") as f:
        state = json.load(f)

    dcel = _restore_dcel(state)
    outer_idx = state.get("outer_face_idx")
    if outer_idx is not None and 0 <= outer_idx < len(dcel.faces):
        dcel.outerFace = dcel.faces[outer_idx]
    elif dcel.outerFace is None and len(dcel.faces) > 0:
        dcel.outerFace = dcel.faces[0]

    packing = newton_packing(dcel, tol=tol, max_iter=max_iter, boundary_radius=boundary_radius, quiet=True)
    packing = canonical_spherical_layout(packing, n_iterations=n_iterations)
    packing.markIndices()
    compute_tangencies(packing)
    return packing

def visualize_unfolding(unfolding, packing, nbsE2, root_idx, cuts=None, title_suffix="", method_label=None):
    """
    Visualizes a coin polyhedron unfolding.

    :param unfolding:
    :param packing:
    :param nbsE2: Neighbors of the root vertex.
    :param root_idx:
    :param cuts: Either None or a (cut_graph, cut_tree) tuple
    :return:
    """
    # Create segments for the child-parent relationships:
    segsE2 = []
    for v in unfolding.verts:
        if v.parent is not None:
            segsE2.append(SegmentE2(v.data.center, v.parent.data.center))

    segsE3 = []
    for v in unfolding.verts:
        if v.parent is not None:
            segsE3.append(SegmentE3(packing.verts[v.idx].data.basis3.normalize().toPointE3(),
                                    packing.verts[v.parent.idx].data.basis3.normalize().toPointE3()))

    # Put together the visualization

    blackStyle = makeStyle(stroke=(0, 0, 0))
    redStyle = makeStyle(stroke=(255, 0, 0), strokeWeight=2, fill=None)
    greenStyle = makeStyle(stroke=(0, 255, 0), strokeWeight=2, fill=None)
    blueStyle = makeStyle(stroke=(0, 0, 255), strokeWeight=2, fill=None)

    #yellowStyle = makeStyle(stroke=(255, 255, 0), strokeWeight=2, fill=None)
    boldStyle = makeStyle(stroke=(0, 0, 0), strokeWeight=2, fill=None)
    grayStyle = makeStyle(stroke=(128, 128, 128), strokeWeight=0.5, fill=None)

    title_suffix = f" ({title_suffix})" if title_suffix else ""

    sceneS2 = S2Scene(title=f"Coin polyhedron{title_suffix}", show_sphere=False)
    size = 800
    method_suffix = f" [{method_label}]" if method_label else ""
    sceneE2 = E2Scene(title=f"Proposed unfolding{method_suffix}{title_suffix}", scale=1.0, height=size, width=size, pan_and_zoom=True)

    sceneS2.addAll([(v.data,
                     redStyle if v.idx == root_idx else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[
                         1].idx else blackStyle) for v in packing.verts])
    sceneS2.addAll([(s, grayStyle) for s in segsE3])

    if cuts is not None:
        cut_graph, cut_tree = cuts
        cut_segments = []
        remaining_segments = []
        for edge in cut_graph.edges:
            dart = edge.dart1
            segment = SegmentE3(dart.origin.data, dart.dest.data)
            if edge.idx in cut_tree:
                cut_segments.append(segment)
            else:
                remaining_segments.append(segment)

        direction_segment = SegmentE3(PointE3(0, 0, 0), PointE3(0, 0, 1))
        sceneS2.addAll([(direction_segment, redStyle)])

        sceneS2.addAll([(s, boldStyle) for s in remaining_segments])
        sceneS2.addAll([(s, boldStyle) for s in cut_segments])

    scale = 100
    sceneE2.addAll([(scale * v.data,
                     redStyle if v.idx == root_idx else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[
                         1].idx else blackStyle) for v in unfolding.verts if v.data is not None])
    # sceneE2.addAll([e.data for e in unfolding.edges if e.data is not None])
    sceneE2.addAll([(scale * s, grayStyle) for s in segsE2])

    viewer.add_scene(sceneS2)
    viewer.add_scene(sceneE2)

    viewer.run()


def cut_unfolding(algorithm=steepest_edge_unfolding,
                  n_points=100, n_iterations=1000,
                  visualize=True,
                  visual_cut_graph=False,
                  test_for_overlap=False,
                  seed = 42,
                  **kwargs) -> bool:
    packing, _ = generate_coin_polygon(n_points, n_iterations, seed)
    # packing = build_dcel_with_gop(n_points)
    cut_graph = create_cut_graph_from_packing(packing)
    cut_tree, root_idx = algorithm(cut_graph=cut_graph, packing=packing, **kwargs)
    unfolding = create_join_tree_from_cut_tree(packing, cut_tree, root_idx)
    unfolding_geometry_from_tree(packing, unfolding, root_idx)
    nbsE2 = unfolding.verts[root_idx].neighbors()

    for i, vertex in enumerate(packing.verts):
        print(f"vertex {i}: center at vertex {vertex.data.centerE3} with radius {vertex.data.radiusE3}")


    inversive_distances_test(unfolding, packing, debug=True)
    if visualize:
        cuts = (cut_graph, cut_tree) if visual_cut_graph else None
        visualize_unfolding(unfolding, packing, nbsE2, root_idx, cuts)
    if test_for_overlap:
        return inversive_distances_test(unfolding, packing, debug=True) and check_for_intersections(unfolding)
    return True

def join_unfolding(algorithm=breadth_first_search_unfolding, n_points=100, n_iterations=1000, state_json=None, method_label=None, **kwargs):
    title_suffix = ""
    if state_json:
        title_suffix = Path(state_json).name
        packing = packing_from_state_json(state_json, n_iterations=n_iterations)
    else:
        packing, _ = generate_coin_polygon(n_points, n_iterations)
    unfolding, root_idx = algorithm(packing=packing, **kwargs)
    unfolding_geometry_from_tree(packing, unfolding, root_idx)
    print(len(unfolding.verts))
    nbsE2 = unfolding.verts[root_idx].neighbors()
    print(inversive_distances_test(unfolding, packing, debug=False))
    visualize_unfolding(unfolding, packing, nbsE2, root_idx, None, title_suffix=title_suffix, method_label=method_label)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="View an unfolding from a saved state JSON using a selected unfolding method."
    )
    parser.add_argument(
        "--unfold",
        required=True,
        help="Path to a saved koebepy state JSON to unfold and view.",
    )
    parser.add_argument(
        "--method",
        default="bfs",
        choices=[
            "bfs",
            "dfs",
            "shortest",
            "min-degree-shortest",
            "max-degree-shortest",
            "shortest-shortest",
            "longest-shortest",
            "normal-min",
            "normal-max",
            "coin",
        ],
        help="Unfolding algorithm to use.",
    )

    args = parser.parse_args()

    method_map = {
        "bfs": breadth_first_search_unfolding,
        "dfs": depth_first_search_unfolding,
        "shortest": shortest_paths_unfolding,
        "min-degree-shortest": min_degree_shortest_paths_unfolding,
        "max-degree-shortest": max_degree_shortest_paths_unfolding,
        "shortest-shortest": shortest_shortest_paths_unfolding,
        "longest-shortest": longest_shortest_paths_unfolding,
        "normal-min": lambda packing: normal_order_unfolding(packing, mode="min"),
        "normal-max": lambda packing: normal_order_unfolding(packing, mode="max"),
        "coin": coin_unfolding,
    }

    join_unfolding(
        algorithm=method_map[args.method],
        state_json=args.unfold,
        method_label=args.method,
    )



