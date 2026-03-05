from collections import deque

import numpy as np

from koebe.datastructures.dcel import DCEL, Dart, Edge, Face, Vertex


def create_cut_graph_from_packing(packing: DCEL) -> DCEL:
    cut_graph = DCEL()

    created_darts: dict[(int, int): Dart] = {}
    parents_to_vertices: dict[(int, int, int): Dart] = {}

    def make_dart(face, vertex, neighbor):
        dart = Dart(cut_graph, face=face)
        face.aDart = dart
        dart.data = (vertex.idx, neighbor.idx)
        return dart

    def fix_edge(dart_idx):
        dart = darts[dart_idx]
        idx0, idx1 = dart.data
        if idx0 > idx1:
            idx0, idx1 = idx1, idx0

        prev_idx = vertex.neighbors()[dart_idx-1].idx
        parents = tuple(sorted([idx0, idx1, prev_idx]))
        if parents not in parents_to_vertices:
            origin = Vertex(cut_graph, dart, parents)
            parents_to_vertices[parents] = origin
        dart.origin = parents_to_vertices[parents]

        twin = created_darts.get((idx0, idx1), None)
        if twin is None:
            created_darts[(idx0, idx1)] = dart
            edge = Edge(cut_graph, dart)
            dart.edge = edge
            edge.data = packing.verts[dart_idx].idx
        else:
            dart.makeTwin(twin)
            dart.edge = twin.edge

        dart.makePrev(darts[dart_idx-1])

    for vertex in packing.verts:
        # Build a new face
        face = Face(cut_graph)
        face.data = vertex.idx
        darts = list(map(lambda neighbor: make_dart(face, vertex, neighbor), vertex.neighbors()))

        for i in range(len(darts)):
            fix_edge(i)
    # Ensures that edge indices match the corresponding edge the join graph
    cut_graph.edges.sort(key=lambda edge: edge.data)
    cut_graph.markIndices()


    # adjacent_faces: dict[int: set[int]] = {}
    # for i in range(len(cut_graph.faces)):
    #     adjacent_faces[i] = set()
    #
    # for face in cut_graph.faces:
    #     for edge in face.edges():
    #         face0, face1 = edge.incidentFaces()
    #         idx0, idx1 = face0.data, face1.data
    #         adjacent_faces[idx0].add(idx1)
    #         adjacent_faces[idx1].add(idx0)
    #
    # faces_to_vertices: dict[Tuple[int, int, int]: Vertex] = set()
    #
    # for face in cut_graph.faces:
    #     for edge in face.edges():
    #         face0, face1 = edge.incidentFaces()
    #         f0_idx, f1_idx = face0.data, face1.data
    #         mutually_incident_faces = adjacent_faces[f0_idx] & adjacent_faces[f1_idx]
    #         # TODO may fall for small numbers of points!
    #         assert len(mutually_incident_faces) == 2
    #         incident_idx0, incident_idx1 = mutually_incident_faces
    #         vertex_identifer0 = tuple(sorted([f0_idx, f1_idx, incident_idx0]))
    #         vertex_identifer1 = tuple(sorted([f0_idx, f1_idx, incident_idx0]))
    #         dart0, dart1 = edge.darts()
    #         if vertex_identifer0 not in faces_to_vertices:
    #             origin = Vertex(dart0, vertex_identifer0)
    #             faces_to_vertices[vertex_identifer0] = origin
    #             dart0.origin = origin
    #         if vertex_identifer1 not in faces_to_vertices:
    #             dest = Vertex(dart1, vertex_identifer1)
    #             faces_to_vertices[vertex_identifer1] = dest
    #             dart1.origin = dest


    return cut_graph

def validate_cut_graph(cut_graph: DCEL, packing: DCEL) -> None:
    assert len(cut_graph.faces) == len(packing.verts)
    assert len(cut_graph.edges) == len(packing.edges)

    for vertex in packing.verts:
        assert any(map(lambda face: face.data == vertex.idx, cut_graph.faces))
        for neighbor in vertex.neighbors():
            assert any(map(lambda dart: dart.data[0] == vertex.idx
                                        and dart.data[1] == neighbor.idx, cut_graph.darts))
    return


def compute_hinge_direction(cut_graph: DCEL, packing: DCEL) -> None:
    # # First phase: construct a map from faces of the cut graph to the adjacent faces
    #
    # adjacent_faces: dict[int: set[int]] = {}
    # for i in range(len(cut_graph.faces)):
    #     adjacent_faces[i] = set()
    #
    # for face in cut_graph.faces:
    #     for edge in face.edges():
    #         face0, face1 = edge.incidentFaces()
    #         idx0, idx1 = face0.data, face1.data
    #         adjacent_faces[idx0].add(idx1)
    #         adjacent_faces[idx1].add(idx0)

    # Second phase: Compute the hinge direction

    def compute_interstice(vert0_idx, vert1_idx, vert2_idx):
        """
        Compute the intersection point of three planes in point-normal form.

        Parameters:
            normals: list of 3 tuples/lists (a, b, c) - normal vectors
            points: list of 3 tuples/lists (x0, y0, z0) - points on each plane

        Returns:
            numpy array (x, y, z) - intersection point
        Raises:
            ValueError if planes do not intersect at a single point
        """
        vert0, vert1, vert2 = packing.verts[vert0_idx], packing.verts[vert1_idx], packing.verts[vert2_idx]
        center0, center1, center2 = vert0.data.centerE3, vert1.data.centerE3, vert2.data.centerE3
        center0 = list(center0.__iter__())
        center1 = list(center1.__iter__())
        center2 = list(center2.__iter__())
        # Assume center of sphere is 0, 0, 0, normals and points are the same!
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

    # for edge in cut_graph.edges:
    #     origin, dest = edge.endPoints()
    #
    #     interstice0 = compute_interstice(*(origin.data))
    #     interstice1 = compute_interstice(*(dest.data))
    #
    #     hinge_direction = interstice1-interstice0
    #     edge.data = VectorE3(*hinge_direction)

    for vertex in cut_graph.verts:
        vertex.data = compute_interstice(*(vertex.data))
    return

def create_join_tree_from_cut_tree(packing: DCEL, cut_set: set[int], root_idx: int) -> (DCEL, int):
    unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
    unfolding.markIndices()

    for v in unfolding.verts:
        v.parent = None

    visited = set()
    tree_set = set()
    fringe = deque([unfolding.verts[root_idx]])

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
    return unfolding, root_idx