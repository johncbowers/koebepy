from collections import deque

from koebe.datastructures.dcel import DCEL, Dart, Edge, Vertex
from koebe.geometries.euclidean3 import VectorE3
from cut_graph_construction import compute_interstices

"""
A file for unfolding algorithms based on the cut graph. These algorithms return a
cut set of edge indices and the index of the root vertex.
"""


def steepest_edge_unfolding(cut_graph: DCEL, packing: DCEL, direction=VectorE3(0, 0, 1)) -> (set[int], int):
    """
    Steepest edge unfolding as described in Wolfram 54-57.

    :param cut_graph:
    :param packing:
    :param direction: Direction used to determine edge steepness.
    :return: Cut set of edge indices.
    """

    compute_interstices(cut_graph=cut_graph, packing=packing)

    def hinge_direction(dart: Dart) -> VectorE3:
        origin, dest = dart.origin, dart.dest
        return VectorE3(*(origin.data - dest.data))

    def relative_direction(vector: VectorE3) -> VectorE3:
        return direction.dot(vector) / (direction.norm() * vector.norm())

    # First, compute the highest vertex wrt direction
    vertex_directions = [relative_direction(VectorE3(*vertex.data)) for vertex in cut_graph.verts]
    highest_vertex_idx = max(enumerate(vertex_directions), key=lambda pair: pair[1])[0]

    cut_set: set[int] = set()

    for vertex in cut_graph.verts:
        if vertex.idx != highest_vertex_idx:
            relative_directions = [relative_direction(hinge_direction(dart)) for dart in vertex.inDarts()]
            steepest_edge_idx = max(enumerate(relative_directions),
                                    key=lambda pair: pair[1])[0]
            edge_idx = vertex.edges()[steepest_edge_idx].idx
            cut_set.add(edge_idx)
    # TODO determine an appropriate root vertex as well

    root_idx = min(packing.verts,
                   key=lambda vert: relative_direction(VectorE3(*vert.data.centerE3))).idx
    return cut_set, root_idx


def depth_first_search_cut_tree(cut_graph: DCEL) -> (set[Edge], int):
    """
    A simple depth-first computation of a cut tree, made to test other code.

    :param packing:
    :return: Cut set of edge indices and the root vertex in the join tree.
    """
    # initialize graph data structures
    visited = set()
    tree_set = set()
    cut_set = set()
    root_idx = 0
    fringe = deque([cut_graph.verts[root_idx]])

    # Use whatever first search to construct the spanning tree
    while fringe:
        v: Vertex = fringe.pop()

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
                    cut_set.add(edge.idx)
                    fringe.append(v1)
                    tree_set.add(v1)
    return cut_set, root_idx