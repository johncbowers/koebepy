import bisect
import heapq
import math
from argparse import ArgumentError
from collections import deque
from math import acos
from random import random

from koebe.datastructures.dcel import DCEL, Vertex
from koebe.geometries.euclidean2 import CircleE2, PointE2
from koebe.geometries.euclidean3 import VectorE3, PointE3

"""
A file for unfolding algorithms based on the join graph. These algorithms return the
unfolding DCEL and the index of the root vertex.
"""


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
        # TODO: Implement left first search as described in wolfram
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
    :return: A tuple of the generated unfolding and the index of the root vertex.
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
    """
    Computes the shortest path tree starting at a min degree vertex.
    :param packing:
    :return:
    """
    min_degree_idx = min(packing.verts, key= lambda v: len(v.neighbors())).idx
    return shortest_paths_unfolding(packing, min_degree_idx)

def max_degree_shortest_paths_unfolding(packing) -> (DCEL, int):
    """
    Computes the shortest path tree starting at a max degree vertex.
    :param packing:
    :return:
    """
    max_degree_idx = max(packing.verts, key= lambda v: len(v.neighbors())).idx
    return shortest_paths_unfolding(packing, max_degree_idx)

def calc_unfolding_tree_length(packing: DCEL, unfolding: DCEL) -> float:
    """
    Computes the total length of the unfolding tree.
    :param packing:
    :param unfolding:
    :return:
    """
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
    :param packing:
    :return:
    """

    unfolding, root = min(map(lambda v: shortest_paths_unfolding(packing, v.idx), packing.verts),
                          key = lambda unf : calc_unfolding_tree_length(packing, unf[0]))

    return unfolding, root

def longest_shortest_paths_unfolding(packing) -> (DCEL, int):
    """
    Try every possible starting vertex, compute the shortest-paths tree
    (as produced by `shortest_paths_unfolding`) for that root, and return
    the unfolding whose tree has the largest total edge length in the
    original packing.
    :param packing:
    :return:
    """

    unfolding, root = max(map(lambda v: shortest_paths_unfolding(packing, v.idx), packing.verts),
                          key = lambda unf : calc_unfolding_tree_length(packing, unf[0]))

    return unfolding, root

def normal_order_unfolding(packing, mode="min") -> (DCEL, int):
    """
    Computes the normal order unfolding as described in Wolfram 63-65. The normal order
    unfolding computes an angle a between some direct c and the normal vector
    of each face. It sorts vertices into a list L based on this angle. At each
    step, it finds the first vertex v_i in L not already added to the join tree
    and adjacent to an vertex v_j in the join tree. If there are multiple adjcanent
    vertices, it picks one based on a criterion.

    :param packing:
    :param mode: May be 'min', 'max', 'flat', or 'longest'.
    :return:
    """
    def find_first_adjacent(j: int):
        j_neighbors = unfolding.verts[j].neighbors()
        for i in L:
            if unfolding.verts[i] in j_neighbors:
                return i
        return None

    def min_adjacent(T):
        """
        Finds the adjacent vertex in the join tree T with minimal index.
        :param T:
        :return:
        """
        return next(
            filter(lambda pair: pair[1] is not None,
                map(lambda k: (k, find_first_adjacent(k)), T)
            ),
            None)

    def max_adjacent(T):
        """
        Finds the adjacent vertex in the join tree T with maximal index.
        :param T:
        :return:
        """
        for j in reversed(T):
            i = find_first_adjacent(j)
            if i is not None:
                return j, i
        return None

    def flat_adjacent(T):
        # TODO implement correctly according to Wolfram 63
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
        # TODO implement correctly according to WOlfram 64
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
        raise ArgumentError(f"Mode must be one of 'min', 'max', or 'long', but was '{mode}'")


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

    # Pseudo code on page 65
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
    """
    Unfolds a packing using Bower's algorithm. This algorithm uses a sweep-line approach. It defines a vertex
    as the north direction, then adds vertices from north to south.

    :param packing:
    :return:
    """
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