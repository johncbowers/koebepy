# Import geometries

from koebe.algorithms.circlepackings.layout import canonical_spherical_projection, compute_tangencies
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *

# Import convex hull, circle packing, and tutte embedding algorithms
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

# General imports

# Scene and Visualization libraries
from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle
from koebe.graphics.scenes.euclidean2scene import E2Scene

from cut_unfolding_algorithms import *
from cut_graph_construction import *
from build_unfolding import *

n_points = 100
n_iterations = 1000


def generate_coin_polygon(n_points, n_iterations):
    """
    Generates a coin polygon.
    :param n_points:
    :param n_iterations:
    :return:
    """
    print(f"Generating random convex hull of {n_points} points and computing a Tutte embedding... ")
    poly = randomConvexHullE3(n_points)  # Generate a random polyhedron with 16 vertices.
    poly.outerFace = poly.faces[0]  # Arbitrarily select an outer face.
    print("\tdone.")

    print("Computing a circle packing... ")

    hyp_packing, _ = maximalPacking(
        poly,
        num_passes=n_iterations
    )
    packing = canonical_spherical_projection(hyp_packing)
    packing.markIndices()
    print("\tdone.")

    compute_tangencies(packing)
    return packing

def visualize_unfolding(unfolding, packing, nbsE2, root_idx, cuts=None):
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
    grayStyle = makeStyle(stroke=(128, 128, 128), strokeWeight=0.5, fill=None)

    sceneS2 = S2Scene(title="Coin polyhedron", show_sphere=False)
    size = 800
    sceneE2 = E2Scene(title="Proposed unfolding", scale=1.5, height=size, width=size, pan_and_zoom=True)

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

        sceneS2.addAll([(s, grayStyle) for s in remaining_segments])
        sceneS2.addAll([(s, greenStyle) for s in cut_segments])

    scale = 100
    sceneE2.addAll([(scale * v.data,
                     redStyle if v.idx == root_idx else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[
                         1].idx else blackStyle) for v in unfolding.verts if v.data is not None])
    # sceneE2.addAll([e.data for e in unfolding.edges if e.data is not None])
    sceneE2.addAll([(scale * s, grayStyle) for s in segsE2])

    viewer.add_scene(sceneS2)
    viewer.add_scene(sceneE2)

    viewer.run()


packing = generate_coin_polygon(n_points, n_iterations)
cut_graph = create_cut_graph_from_packing(packing)
cut_tree = steepest_edge_unfolding(cut_graph, packing)
root_idx = 0
unfolding, root_idx = create_join_tree_from_cut_tree(packing, cut_tree, root_idx)


unfolding_geometry_from_tree(packing, unfolding, root_idx)

# print(check_for_intersections(unfolding))

nbsE2 = unfolding.verts[root_idx].neighbors()

#visualize(cut_graph, cut_tree)
visualize_unfolding(unfolding, packing, nbsE2, root_idx)

