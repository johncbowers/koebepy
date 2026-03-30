from collections import deque

import numpy as np

from koebe.datastructures.dcel import DCEL, Dart, Edge, Face, Vertex

"""
A file for functions used to construct the cut graph based on the packing, and to
transform the cut tree into a join tree that we can use to build the unfolding 
geometry. 
"""

def create_cut_graph_from_packing(packing: DCEL) -> DCEL:
    """
    Builds DCEL structure of the cut graph based on the join graph. Each edge's
    index matches with the corresponding edge in the join graph. Each vertex stores
    a sorted tuple of indices of the faces that meet to form the vertex. Each
    face has the same index as the corresponding vertex in the join graph.

    :param packing:
    :return: DCEL structure of the cut graph.
    """
    cut_graph = DCEL()


    # Map of sorted tuples of face indices to the corresponding dart
    created_darts: dict[(int, int): Dart] = {}
    # Map of sorted tuples of parent faces to the corresponding vertex
    parents_to_vertices: dict[(int, int, int): Vertex] = {}

    def make_dart(face, vertex, neighbor):
        dart = Dart(cut_graph, face=face)
        face.aDart = dart
        dart.data = (vertex.idx, neighbor.idx)
        return dart

    def fix_dart(dart_idx):
        dart = darts[dart_idx]
        idx0, idx1 = dart.data

        # Set origin point based on parents of origin
        prev_idx = vertex.neighbors()[dart_idx-1].idx
        parents = tuple(sorted([idx0, idx1, prev_idx]))
        if parents not in parents_to_vertices:
            origin = Vertex(cut_graph, dart, parents)
            parents_to_vertices[parents] = origin
        dart.origin = parents_to_vertices[parents]

        # Connect to twin if it exists, and create corresponding edge
        twin_key = tuple(sorted([idx0, idx1]))
        twin = created_darts.get(twin_key, None)
        if twin is None:
            created_darts[twin_key] = dart
            edge = Edge(cut_graph, dart)
            dart.edge = edge
            edge.data = vertex.edges()[dart_idx].idx
        else:
            dart.makeTwin(twin)
            dart.edge = twin.edge

        dart.makePrev(darts[dart_idx-1])

    # Construct DCEL by traversing counterclockwise across each face, building darts as go you
    for vertex in packing.verts:
        # Build a new face
        face = Face(cut_graph)
        face.data = vertex.idx

        # Make darts
        darts = list(map(lambda neighbor: make_dart(face, vertex, neighbor), vertex.neighbors()))

        # Fix darts to have proper DCEL structure
        for i in range(len(darts)):
            fix_dart(i)
    # Ensures that edge indices match the corresponding edge the join graph
    cut_graph.edges.sort(key=lambda edge: edge.data)
    cut_graph.markIndices()
    return cut_graph


def compute_interstices(cut_graph: DCEL, packing: DCEL) -> None:
    """
    Populates data of cut_graph vertices with the location of the vertex in the
    3D packing. This overwrites an existing data. Computes these locations by computing
    the intersection of the three planes that correspond the three parent faces of the vertices.

    :param cut_graph:
    :param packing:
    :return:
    """

    def compute_interstice(face0_idx, face1_idx, face2_idx) -> np.array:
        """
        Compute the location of the interstice between three faces by
        solving a linear system.

        :param face0_idx:
        :param face1_idx:
        :param face2_idx:
        :return:
        """
        vert0, vert1, vert2 = packing.verts[face0_idx], packing.verts[face1_idx], packing.verts[face2_idx]
        center0, center1, center2 = vert0.data.centerE3, vert1.data.centerE3, vert2.data.centerE3
        center0 = list(center0.__iter__())
        center1 = list(center1.__iter__())
        center2 = list(center2.__iter__())
        # Since the center of the sphere is 0, 0, 0, normals and points are the same!
        normals = [center0, center1, center2]
        points = [center0, center1, center2]

        # Convert to numpy arrays
        normals = np.array(normals, dtype=float)
        points = np.array(points, dtype=float)

        # Build coefficient matrix A and RHS vector d
        A = normals
        d = np.einsum('ij,ij->i', normals, points)  # dot product for each plane

        # Check if normals are linearly independent
        if np.linalg.matrix_rank(A) < 3:
            raise ValueError("The planes do not intersect at a unique point (normals are dependent).")

        # Solve the system A * [x, y, z] = d
        intersection_point = np.linalg.solve(A, d)
        return intersection_point

    for vertex in cut_graph.verts:
        vertex.data = compute_interstice(*(vertex.data))
    return

def create_join_tree_from_cut_tree(packing: DCEL, cut_set: set[int], root_idx: int) -> DCEL:
    """
    Constructs a join tree from a cut tree, starting at root_idx. Returns the unfolding
    along with the root index.

    :param packing: DCEL structure of the cut graph.
    :param cut_set: A set of the indices of edges in the cut tree.
    :param root_idx: Index of the vertex in the join graph to start from.
    :return: Unfolding DCEL.
    """
    unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
    unfolding.markIndices()

    for v in unfolding.verts:
        v.parent = None

    visited = set()
    tree_set = set()
    fringe = deque([unfolding.verts[root_idx]])

    # Build using DFS
    while fringe:
        v: Vertex = fringe.pop()

        if v not in visited:
            visited.add(v)
            edges = v.edges()
            for edge in edges:
                if edge.idx not in cut_set:
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