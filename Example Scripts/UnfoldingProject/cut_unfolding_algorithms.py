from collections import deque

from koebe.datastructures.dcel import DCEL, Dart, Edge, Vertex
from koebe.geometries.euclidean3 import VectorE3
from cut_graph_construction import compute_hinge_direction


def steepest_edge_unfolding(cut_graph: DCEL, packing: DCEL, direction=VectorE3(0, 0, 1)) -> set[int]:
    compute_hinge_direction(cut_graph, packing)

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
    return cut_set


def depth_first_search_cut_tree(packing: DCEL) -> (set[Edge], int):
    # initialize graph data structures
    visited = set()
    tree_set = set()
    cut_set = set()
    root_idx = 13
    fringe = deque([packing.verts[root_idx]])

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
                    cut_set.add(edge)
                    fringe.append(v1)
                    tree_set.add(v1)
    return cut_set, root_idx