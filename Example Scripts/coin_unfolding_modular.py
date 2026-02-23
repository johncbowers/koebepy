# Import geometries
import bisect
from argparse import ArgumentError, ArgumentTypeError
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


n_points = 60
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


def place(packing: DCEL, unfolding: DCEL, parent: Vertex, child: Vertex, root_idx: int) -> None:
    """
    Places the child vertex on the 2D plane for the unfolding based on its
    parent vertex.

    :param packing: The circle packing in 3D space.
    :param unfolding: The derived unfolding.
    :param parent: The parent vertex, from the unfolding, should have geometrical information.
    :param child: The child vertex, from the folding, does not have geometrical information.
    :param root: The root vertex of the join tree.
    :return:
    """
    parent_idx = parent.idx
    child_idx = child.idx


    # General case: parent is not the root, so grandparents exist
    if parent_idx != root_idx:
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
    # Special case: the parent the root, so it has no parent
    else:
        n = packing.verts[root_idx].data.basis3.normalize()
        packing_edges = packing.verts[parent_idx].edges()
        neighbors = packing.verts[parent_idx].neighbors()


        neighbor_index = next(
            (i for i, vertex in enumerate(neighbors) if vertex.idx == child_idx),
            float("inf") # Should never occur
        )

        if neighbor_index == float("inf"):
            raise ArgumentError(f"Vertex {child_idx} should share an edge with vertex the root vertex, but it does not.")

        # Special Case for the 0th neighbor
        if neighbor_index == 0:
            child.data = CircleE2(PointE2(unfolding.verts[root_idx].data.radius
                         + neighbors[0].data.radiusE3, 0), neighbors[0].data.radiusE3)
        else:
            # Angle of ith neighbor is based off of the position of the 0th neighbor
            v0 = packing_edges[0].data.toVectorE3() - packing.verts[root_idx].data.centerE3
            vi = packing_edges[neighbor_index].data.toVectorE3() - packing.verts[root_idx].data.centerE3

            theta = math.atan2(v0.cross(vi).dot(n), v0.dot(vi))
            child.data = CircleE2(
                PointE2(
                    (packing.verts[root_idx].data.radiusE3 + neighbors[neighbor_index].data.radiusE3) * math.cos(theta),
                    (packing.verts[root_idx].data.radiusE3 + neighbors[neighbor_index].data.radiusE3) * math.sin(theta)
                ),
                neighbors[neighbor_index].data.radiusE3
            )


def unfolding_geometry_from_tree(packing: DCEL, unfolding: DCEL,
                                 join_tree: dict[Vertex, list[Vertex]], root_idx: int) -> None:
    """
    Computes the geometry of a coin unfolding given the join tree.

    :param packing: Circle packing in 3D space.
    :param unfolding: The derived unfolding.
    :param join_tree: Represents how circles are joined together to form the unfolding.
    :return:
    """

    # Create geometrical data for vertex 0
    unfolding.verts[root_idx].data = CircleE2(PointE2(0, 0), packing.verts[root_idx].data.radiusE3)
    # Initialize graph search data structures

    visited = set()
    fringe = deque([unfolding.verts[root_idx]])

    # Use depth first search to place the circles
    while len(fringe) > 0:
        parent = fringe.popleft()
        if parent not in visited:
            visited.add(parent)
            for child in join_tree[parent]:
                place(packing, unfolding, parent, child, root_idx)
                fringe.append(child)
    return


def whatever_first_search_unfolding(packing: DCEL, search_type: str) -> (DCEL, int):
    """
    Performs whatever first search unfolding on the given packing.
    :param packing:
    :param search_type: depth or breadth
    :return: A tuple of the generated unfolding and the index of the root vertex.
    """
    if search_type == "depth":
        pop_fn = "pop"
    elif search_type == "breadth":
        pop_fn = "popleft"
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
    root_idx = 13
    fringe = deque([unfolding.verts[root_idx]])


    def left_first_sort(edges, packing_edges):
        pass


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
    return unfolding, root_idx

def depth_first_search_unfolding(packing) -> (DCEL, int):
    return whatever_first_search_unfolding(packing, "depth")

def breadth_first_search_unfolding(packing) -> (DCEL, int):
    return whatever_first_search_unfolding(packing, "breadth")

def shortest_paths_unfolding(packing, root_idx=0) -> (DCEL, int):
    """
    Computes the shortest paths spanning tree starting at a certain vertex.
    :param packing:
    :return:
    """
    unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
    unfolding.markIndices()

    # initialize the unfolding parent for each vertex to None
    for v in unfolding.verts:
        v.parent = None

    # initialize graph data structures
    for edge in packing.edges:
        u = edge.u.data.centerE3
        v = edge.v.data.centerE3
        magnitude = (u-v).norm()
        edge.key = magnitude

    pq = [(e.key, random(), e) for e in packing.verts[root_idx].edges()]
    heapq.heapify(pq)

    placed: set = {unfolding.verts[root_idx]}

    while len(pq) > 0:
        _, _, edge = heapq.heappop(pq)
        v0_idx, v1_idx = [v.idx for v in edge.endPoints()]

        v0 = unfolding.verts[v0_idx]
        v1 = unfolding.verts[v1_idx]
        if v1 in placed:
            if v0 in placed:
                continue
            v0, v1 = v1, v0
            v0_idx, v1_idx = v1_idx, v0_idx
        v1.parent = v0
        placed.add(v1)
        for child_edge in packing.verts[v1_idx].edges():
            heapq.heappush(pq, (child_edge.key, random(), child_edge))
    return unfolding, root_idx


def min_degree_shortest_paths_unfolding(packing) -> (DCEL, int):
    min_degree_idx = min(packing.verts, key= lambda v: len(v.neighbors())).idx
    return shortest_paths_unfolding(packing, min_degree_idx)

def max_degree_shortest_paths_unfolding(packing) -> (DCEL, int):
    max_degree_idx = max(packing.verts, key= lambda v: len(v.neighbors())).idx
    return shortest_paths_unfolding(packing, max_degree_idx)

def calc_unfolding_tree_length(unfolding: DCEL) -> float:
    total = 0.0
    for u in unfolding.verts:
        if u.parent is not None:
            a = packing.verts[u.idx].data.centerE3
            b = packing.verts[u.parent.idx].data.centerE3
            total += (a - b).norm()
    return total


def shortest_shortest_paths_unfolding(packing) -> (DCEL, int):
    """
    Try every possible starting vertex, compute the shortest-paths tree
    (as produced by `shortest_paths_unfolding`) for that root, and return
    the unfolding whose tree has the smallest total edge length in the
    original packing.
    """

    unfolding, root = min(map(lambda v: shortest_paths_unfolding(packing, v.idx), packing.verts), key = lambda unf : calc_unfolding_tree_length(unf[0]))

    return unfolding, root

def longest_shortest_paths_unfolding(packing) -> (DCEL, int):
    """
    Try every possible starting vertex, compute the shortest-paths tree
    (as produced by `shortest_paths_unfolding`) for that root, and return
    the unfolding whose tree has the smallest total edge length in the
    original packing.
    """

    unfolding, root = max(map(lambda v: shortest_paths_unfolding(packing, v.idx), packing.verts), key = lambda unf : calc_unfolding_tree_length(unf[0]))

    return unfolding, root


#TODO doesn't work and is derby's job anyway!
def steepest_edge_unfolding(packing, root_idx=0) -> (DCEL, int):
    """
    Build a spanning tree by selecting edges ordered by their projection
    onto the normal vector at `root_idx` (steepest first). The edge key
    is the negative dot product of the edge midpoint vector with the
    root normal, so smaller keys are popped first from the priority queue.
    """
    unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
    unfolding.markIndices()

    # initialize the unfolding parent for each vertex to None
    for v in unfolding.verts:
        v.parent = None

    # normal vector at the root (unit)
    n = packing.verts[root_idx].data.basis3.normalize()

    # assign keys to edges based on midpoint projection onto n
    for edge in packing.edges:
        mid = (edge.u.data.centerE3 + edge.v.data.centerE3) * 0.5
        mid_vec = mid - PointE3.O
        edge.key = - mid_vec.dot(n)

    pq = [(e.key, random(), e) for e in packing.verts[root_idx].edges()]
    heapq.heapify(pq)

    placed: set = {unfolding.verts[root_idx]}

    while len(pq) > 0:
        _, _, edge = heapq.heappop(pq)
        v0_idx, v1_idx = [v.idx for v in edge.endPoints()]

        v0 = unfolding.verts[v0_idx]
        v1 = unfolding.verts[v1_idx]
        if v1 in placed:
            if v0 in placed:
                continue
            v0, v1 = v1, v0
            v0_idx, v1_idx = v1_idx, v0_idx
        v1.parent = v0
        placed.add(v1)
        for child_edge in packing.verts[v1_idx].edges():
            heapq.heappush(pq, (child_edge.key, random(), child_edge))

    return unfolding, root_idx

def normal_order_unfolding(packing, mode="min") -> (DCEL, int):
    def find_first_adjacent(j: int):
        j_neighbors = unfolding.verts[j].neighbors()
        for i in L:
            if unfolding.verts[i] in j_neighbors:
                return i
        return None

    def min_adjacent(T):
        return next(
            filter(lambda pair: pair[1] is not None,
                map(lambda k: (k, find_first_adjacent(k)), T)
            ),
            None)

    def max_adjacent(T):
        for j in reversed(T):
            i = find_first_adjacent(j)
            if i is not None:
                return j, i
        return None

    def flat_adjacent(T):
        flattest_j, flattest_i = None, None
        flattest_angle = -float('inf')
        for j in T:
            i = find_first_adjacent(j)
            if i is not None:
                center_j = packing.verts[j].data.centerE3
                center_i = packing.verts[i].data.centerE3
                direction = center_i - center_j
                angle = acos(direction.dot(c)/(c.norm()*direction.norm()))
                if abs(angle) > flattest_angle:
                    flattest_angle = abs(angle)
                    flattest_j, flattest_i = j, i
        return None if flattest_i is None else flattest_j, flattest_i



    def longest_adjacent(T):
        longest_j, longest_i = None, None
        longest_distance = -float("inf")
        for j in T:
            i = find_first_adjacent(j)
            if i is not None:
                center_j = packing.verts[j].data.centerE3
                center_i = packing.verts[j].data.centerE3
                distance = (center_i - center_j).norm()
                if distance > longest_distance:
                    longest_j, longest_i = j, i
                    longest_distance = distance
        return None if longest_i is None else longest_j, longest_i

    if mode == 'min':
        choose_adjacent_tree_facet = min_adjacent
    elif mode == 'max':
        choose_adjacent_tree_facet = max_adjacent
    elif mode == 'flat':
        choose_adjacent_tree_facet = flat_adjacent
    elif mode == 'long':
        choose_adjacent_tree_facet = longest_adjacent
    else:
        raise ArgumentTypeError(f"Mode must be one of 'min', 'max', or 'long', but was '{mode}'")


    unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
    unfolding.markIndices()

    # initialize the unfolding parent for each vertex to None
    for v in unfolding.verts:
        v.parent = None

    c = VectorE3(1, 0, 0)
    centroid = sum(map(lambda vert: vert.data.centerE3, packing.verts), start=PointE3(0, 0, 0))*(1/len(packing.verts))

    def angle_with_c(vertex):
        normal_vector = vertex.data.centerE3 - centroid
        dot_product = normal_vector.dot(c)
        cos_theta = dot_product/(c.norm()*normal_vector.norm())
        return math.acos(cos_theta)

    L = deque(map(lambda vert: vert.idx, sorted(packing.verts, key=lambda vert: angle_with_c(vert))))

    root_idx = L.popleft()
    # TODO replaced with balanced BST
    T = [root_idx]

    while L:
        edge = choose_adjacent_tree_facet(T)
        if edge is None:
            # TODO error message
            raise ValueError("")
        j, i = edge
        v_j, v_i = unfolding.verts[j], unfolding.verts[i]
        v_i.parent = v_j
        L.remove(i)
        bisect.insort(T, i, key=lambda idx: angle_with_c(packing.verts[idx]))
    return unfolding, root_idx


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


def visualize_unfolding(unfolding, packing, nbsE2, root_idx):
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
unfolding, root_idx = breadth_first_search_unfolding(packing)
parent_dict = _build_parent_map(unfolding, unfolding.verts[root_idx], None)

# Invert the child->parent dictionary to get the parent->child one
child_dict = defaultdict(list)
for key, value in parent_dict.items():
    child_dict[value].append(key)

unfolding_geometry_from_tree(packing, unfolding, child_dict, root_idx)

print(verify_unfolding(unfolding, packing))

# print(check_for_intersections(unfolding))

nbsE2 = unfolding.verts[root_idx].neighbors()

visualize_unfolding(unfolding, packing, nbsE2, root_idx)

