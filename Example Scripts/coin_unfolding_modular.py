# Import geometries
from argparse import ArgumentError
from collections import defaultdict

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
from math import *
from random import *
import heapq

# Scene and Visualization libraries
from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle
from koebe.graphics.scenes.euclidean2scene import E2Scene
from visualize2d import _build_parent_map


n_points = 50
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


def place(packing: DCEL, unfolding: DCEL, parent: Vertex, child: Vertex) -> None:
    """
    Places the child vertex on the 2D plane for the unfolding based on its
    parent vertex.

    :param packing: The circle packing in 3D space.
    :param unfolding: The derived unfolding.
    :param parent: The parent vertex, from the unfolding, should have geometrical information.
    :param child: The child vertex, from the folding, does not have geometrical information.
    :return:
    """
    parent_idx = parent.idx
    child_idx = child.idx


    # General case: parent is not vertex 0, so grandparents exist
    if parent_idx != 0:
        parent_dirE2 = (parent.parent.data.center - parent.data.center).normalize()

        parent_dirS2 = packing.verts[parent_idx].data.tangentPointWith(packing.verts[parent.parent.idx].data).toVectorE3() - \
                       packing.verts[parent_idx].data.centerE3
        v1_dirS2 = packing.verts[parent_idx].data.tangentPointWith(packing.verts[child_idx].data).toVectorE3() - \
                   packing.verts[parent_idx].data.centerE3
        n = packing.verts[parent_idx].data.basis3.normalize()
        theta = math.atan2(parent_dirS2.cross(v1_dirS2).dot(n), parent_dirS2.dot(v1_dirS2))

        vec = parent_dirE2.rotate(theta).normalize()
        child.data = CircleE2(
            parent.data.center + (packing.verts[parent_idx].data.radiusE3 + packing.verts[child_idx].data.radiusE3) * vec,
            packing.verts[child_idx].data.radiusE3
        )
    # Special case: the parent is vertex 0, so it has no parent
    else:
        n = packing.verts[0].data.basis3.normalize()
        packing_edges = packing.verts[parent_idx].edges()
        packing_vertices = packing.verts[parent_idx].neighbors()


        neighbor_index = next(
            (i for i, vertex in enumerate(packing_vertices) if vertex.idx == child_idx),
            float("inf") # Should never occur
        )

        if neighbor_index == float("inf"):
            raise ArgumentError(f"Vertex {child_idx} should share an edge with vertex 0, but it does not.")

        # Special Case for the 0th neighbor
        if neighbor_index == 0:
            child.data = CircleE2(PointE2(unfolding.verts[0].data.radius
                         + packing_vertices[0].data.radiusE3, 0), packing_vertices[0].data.radiusE3)
        else:
            # Angle of ith neighbor is based off of the position of the 0th neighbor
            v0 = packing_edges[0].data.toVectorE3() - packing.verts[0].data.centerE3
            vi = packing_edges[neighbor_index].data.toVectorE3() - packing.verts[0].data.centerE3

            theta = math.atan2(v0.cross(vi).dot(n), v0.dot(vi))
            child.data = CircleE2(
                PointE2(
                    (packing.verts[0].data.radiusE3 + packing_vertices[neighbor_index].data.radiusE3) * math.cos(theta),
                    (packing.verts[0].data.radiusE3 + packing_vertices[neighbor_index].data.radiusE3) * math.sin(theta)
                ),
                packing_vertices[neighbor_index].data.radiusE3
            )


def unfolding_geometry_from_tree(packing: DCEL, unfolding: DCEL, join_tree: dict[Vertex, list[Vertex]]) -> None:
    """
    Computes the geometry of a coin unfolding given the join tree.

    :param packing: Circle packing in 3D space.
    :param unfolding: The derived unfolding.
    :param join_tree: Represents how circles are joined together to form the unfolding.
    :return:
    """

    # Create geometrical data for vertex 0
    unfolding.verts[0].data = CircleE2(PointE2(0, 0), packing.verts[0].data.radiusE3)
    nbsE2 = unfolding.verts[0].neighbors()
    # Initialize graph search data structures

    visited = set()
    fringe = deque([unfolding.verts[0]])

    # Use depth first search to place the circles
    while len(fringe) > 0:
        parent = fringe.popleft()
        if parent not in visited:
            visited.add(parent)
            for child in join_tree[parent]:
                place(packing, unfolding, parent, child)
                fringe.append(child)
    return


def whatever_first_search_unfolding(packing, search_type) -> DCEL:
    if search_type == "depth":
        pop_fn = "popleft"
    elif search_type == "breadth":
        pop_fn = "popright"
    else:
        raise ArgumentError(f"Parameter search_type must be either 'depth' or 'breadth', got {search_type}")


    unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
    unfolding.markIndices()

    # initialize the unfolding parent for each vertex to None
    for v in unfolding.verts:
        v.parent = None

    # initialize graph data structures
    visited = set()
    tree_set = set()
    fringe = deque([unfolding.verts[0]])


    def left_first_sort(edges, packing_edges):
        """
        Sort edges in the left-first manner as described on Wolfram 43.

        :param edges:
        :param packing_edges:
        :return:
        """
        if 'packing_center' not in locals():
            packing_center = sum(map(lambda vertex: vertex.data.centerE3, packing.verts),
                                 start=PointE3(0.0, 0.0, 0.0)) * (1/len(packing.verts))
        midpoints = map(lambda edge: (edge.u.data.centerE3+edge.v.data.centerE3)*0.5, packing_edges)
        vectors = list(map(lambda midpoint: midpoint - packing_center, midpoints))
        vector0 = vectors[0]
        # TODO make this actually compute the angle between vectors
        angles = list(map(lambda vector: vector0.dot(vector)/(vector0.norm()*vector.norm()), vectors))
        sorted_pairs = sorted(zip(angles, edges))
        _, sorted_edges = zip(*sorted_pairs)
        return sorted_edges


    # Use whatever first search to construct the spanning tree
    while fringe:
        v: Vertex = getattr(fringe, pop_fn)()

        if v not in visited:
            visited.add(v)
            edges = v.edges()
            for edge in edges:
                v0, v1 = edge.endPoints()
                # v1 should be the child
                if v1 == v:
                    v0, v1 = v1, v0
                # Only add edge to v1 if the tree does not already connect to v1
                if v1 not in tree_set:
                    fringe.append(v1)
                    tree_set.add(v1)
                    v1.parent = v0
    return unfolding

def depth_first_search_unfolding(packing) -> DCEL:
    return whatever_first_search_unfolding(packing, "depth")

def breadth_first_search_unfolding(packing) -> DCEL:
    return whatever_first_search_unfolding(packing, "breadth")




def coin_unfolding(packing):
    # Compute an unfolding
    unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
    unfolding.markIndices()

    print(f"Placing vertex {0} ")
    unfolding.verts[0].data = CircleE2(PointE2(0, 0), packing.verts[0].data.radiusE3)
    nbsS2 = packing.verts[0].neighbors()
    edgesS2 = packing.verts[0].edges()
    nbsE2 = unfolding.verts[0].neighbors()

    # initialize the unfolding parent for each vertex to None
    for v in unfolding.verts:
        v.parent = None

    # Place the first neighbor
    nbsE2[0].data = CircleE2(PointE2(unfolding.verts[0].data.radius + nbsS2[0].data.radiusE3, 0), nbsS2[0].data.radiusE3)
    nbsE2[0].parent = unfolding.verts[0]

    n = packing.verts[0].data.basis3.normalize()
    # Place the rest of the neighbors
    for i in range(1, len(nbsE2)):
        v0 = edgesS2[0].data.toVectorE3() - packing.verts[0].data.centerE3
        vi = edgesS2[i].data.toVectorE3() - packing.verts[0].data.centerE3
        print(f"Placing vertex {nbsS2[i].idx} with parent 0")
        theta = math.atan2(v0.cross(vi).dot(n), v0.dot(vi))
        nbsE2[i].data = CircleE2(
            PointE2(
                (packing.verts[0].data.radiusE3 + nbsS2[i].data.radiusE3) * math.cos(theta),
                (packing.verts[0].data.radiusE3 + nbsS2[i].data.radiusE3) * math.sin(theta)
            ),
            nbsS2[i].data.radiusE3
        )
        nbsE2[i].parent = unfolding.verts[0]

    # Project all edge data points onto the line through the origin in direction n
    for e in packing.edges:
        v = e.data - PointE3.O
        e.key = -v.dot(n)

    # Create a min priority queue of edge.data keyed by key.data for all edges
    pq = [(e.key, random(), e) for e in packing.edges]
    heapq.heapify(pq)

    # While the queue is not empty remove min and process
    while len(pq) > 0:
        _, _, e = heapq.heappop(pq)
        v0_idx, v1_idx = [v.idx for v in e.endPoints()]

        v0 = unfolding.verts[v0_idx]
        v1 = unfolding.verts[v1_idx]
        if v0.data == None and v1.data == None:
            print("Can't place edge because neither endpoint is placed. This should never happen.")
            continue
        if v0.data == None:
            v0, v1 = v1, v0
            v0_idx, v1_idx = v1_idx, v0_idx

        if v1.data == None:
            # now v0 has been placed and we need to place v1
            print(f"Placing vertex {v1_idx} with parent {v0_idx}")
            if v0.parent == None:
                print(f"v0 has no parent, this should not happen. v0's index is {v0_idx}")
                break
            parent_idx = v0.neighbors().index(v0.parent)
            parent_dirE2 = (v0.parent.data.center - v0.data.center).normalize()

            parent_dirS2 = packing.verts[v0_idx].data.tangentPointWith(packing.verts[v0.parent.idx].data).toVectorE3() - \
                           packing.verts[v0_idx].data.centerE3
            v1_dirS2 = packing.verts[v0_idx].data.tangentPointWith(packing.verts[v1_idx].data).toVectorE3() - packing.verts[
                v0_idx].data.centerE3
            n = packing.verts[v0_idx].data.basis3.normalize()
            theta = math.atan2(parent_dirS2.cross(v1_dirS2).dot(n), parent_dirS2.dot(v1_dirS2))

            v = parent_dirE2.rotate(theta).normalize()
            v1.data = CircleE2(
                v0.data.center + (packing.verts[v0_idx].data.radiusE3 + packing.verts[v1_idx].data.radiusE3) * v,
                packing.verts[v1_idx].data.radiusE3
            )
            v1.parent = v0

    return unfolding, nbsE2


def check_for_intersections(unfolding, tol=1e-10) -> bool:
    for i in range(len(unfolding.verts)):
        for j in range(i+1, len(unfolding.verts)):
            v_i = unfolding.verts[i]
            v_j = unfolding.verts[j]
            point_i = v_i.data.center
            point_j = v_j.data.center

            distance = point_i.distTo(point_j)
            sum_radii = v_i.data.radius + v_j.data.radius
            if sum_radii-tol > distance:
                print(f"Overlap between {point_i} and {point_j} at tolerance {tol}"
                      f"distance {distance} less than the sum of their radii {sum_radii}")

def verify_unfolding(unfolding, packing):

    inversive_distances_sphere = []
    inversive_distances_plane = []
    for i in range(len(unfolding.verts) - 1):
        for j in range(i + 1, len(unfolding.verts)):
            if unfolding.verts[j].parent != unfolding.verts[i] and unfolding.verts[i].parent != unfolding.verts[j] and \
                    unfolding.verts[i].data != None and unfolding.verts[j].data != None:
                inversive_distances_sphere.append(packing.verts[i].data.inversiveDistTo(packing.verts[j].data))
                inversive_distances_plane.append(unfolding.verts[i].data.inversiveDistTo(unfolding.verts[j].data))

    for i in range(len(inversive_distances_plane)):
        if inversive_distances_plane[i] < inversive_distances_sphere[i]:
            print(
                f"{i} {inversive_distances_plane[i]} {inversive_distances_sphere[i]} {inversive_distances_plane[i] - inversive_distances_sphere[i]} {inversive_distances_plane[i] > inversive_distances_sphere[i]}")

    print(
        f"Passes inversive distance test: {not (False in [inversive_distances_plane[i] > inversive_distances_sphere[i] for i in range(len(inversive_distances_plane))])}")
    print(f"Minimum inversive distance detected in the sphere: {min(inversive_distances_sphere)}")
    print(f"Minimum inversive distance detected in the plane: {min(inversive_distances_plane)}")


def visualize_unfolding(unfolding, packing, nbsE2):
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
                     redStyle if v.idx == 0 else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[
                         1].idx else blackStyle) for v in packing.verts])
    sceneS2.addAll([(s, grayStyle) for s in segsE3])

    scale = 100
    sceneE2.addAll([(scale * v.data,
                     redStyle if v.idx == 0 else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[
                         1].idx else blackStyle) for v in unfolding.verts if v.data is not None])
    # sceneE2.addAll([e.data for e in unfolding.edges if e.data is not None])
    sceneE2.addAll([(scale * s, grayStyle) for s in segsE2])

    viewer.add_scene(sceneS2)
    viewer.add_scene(sceneE2)

    viewer.run()


packing = generate_coin_polygon(n_points, n_iterations)
unfolding = whatever_first_search_unfolding(packing, "depth")
parent_dict = _build_parent_map(unfolding, unfolding.verts[0], None)

# Invert the child->parent dictionary to get the parent->child one
child_dict = defaultdict(list)
for key, value in parent_dict.items():
    child_dict[value].append(key)

nbsE2 = unfolding_geometry_from_tree(packing, unfolding, child_dict)

visualize_unfolding(unfolding, packing, nbsE2)

