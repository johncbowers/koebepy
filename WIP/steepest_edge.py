from koebe.geometries.euclidean3 import PointE3, VectorE3


def _coerce_vector_e3(c):
    if isinstance(c, VectorE3):
        return c
    if isinstance(c, PointE3):
        return c - PointE3.O
    if isinstance(c, (tuple, list)) and len(c) == 3:
        return VectorE3(c[0], c[1], c[2])
    raise TypeError("c must be a VectorE3, PointE3, or length-3 tuple/list.")


def _position_of_vertex(v):
    data = v.data
    if isinstance(data, PointE3):
        return data
    if hasattr(data, "centerE3"):
        return data.centerE3
    raise TypeError(
        "Vertex data must be PointE3 or provide a centerE3 attribute (e.g. spherical disk data)."
    )


def _height(c_vec, p):
    return c_vec.dot(p - PointE3.O)


def _ascending_slope(c_vec, p_v, p_w):
    delta = p_w - p_v
    length = delta.norm()
    if length == 0:
        return float("-inf")
    return c_vec.dot(delta) / length


def highest_vertex_wrt_direction(dcel, c, position_of_vertex=None):
    """Return the unique highest vertex (argmax of <c, v>) in the DCEL.

    The uniqueness assumption is the usual "general position" condition.
    If multiple maxima occur (within floating-point equality), the first one
    encountered is returned.
    """
    c_vec = _coerce_vector_e3(c)
    pos = _position_of_vertex if position_of_vertex is None else position_of_vertex
    return max(dcel.verts, key=lambda v: _height(c_vec, pos(v)))


def steepest_ascending_edge_at_vertex(v, c, position_of_vertex=None, eps=1e-12):
    """Pick the steepest ascending incident edge at v w.r.t. direction c.

    Returns:
        The chosen incident Edge, or None if v has no ascending neighbors.
    """
    c_vec = _coerce_vector_e3(c)
    pos = _position_of_vertex if position_of_vertex is None else position_of_vertex

    p_v = pos(v)
    best_edge = None
    best_slope = float("-inf")

    for e in v.edges():
        u, w = e.endPoints()
        nbr = w if u is v else u
        p_nbr = pos(nbr)
        slope = _ascending_slope(c_vec, p_v, p_nbr)
        if slope > eps and slope > best_slope:
            best_slope = slope
            best_edge = e

    return best_edge


def steepest_edge_cut_tree(dcel, c, top_vertex=None, position_of_vertex=None, eps=1e-12):
    """Rule 7 (Steepest-Edge-Unfold) cut tree selector.

    For each vertex v != v+, chooses the steepest ascending edge incident to v,
    where v+ is the highest vertex w.r.t. c. Under general position this yields
    a spanning tree on the vertices.

    Returns:
        dict with keys:
          - "top_vertex": v+
          - "parent": dict {vertex -> parent_vertex} for all v != v+
          - "cut_edges": list of unique selected Edge objects
    """
    c_vec = _coerce_vector_e3(c)
    pos = _position_of_vertex if position_of_vertex is None else position_of_vertex

    v_plus = highest_vertex_wrt_direction(dcel, c_vec, position_of_vertex=pos) if top_vertex is None else top_vertex

    parent = {}
    cut_edges_set = set()

    for v in dcel.verts:
        if v is v_plus:
            continue

        best_edge = steepest_ascending_edge_at_vertex(v, c_vec, position_of_vertex=pos, eps=eps)
        if best_edge is None:
            raise ValueError(
                "No ascending edge found at a non-top vertex. "
                "This usually indicates non-general position or inconsistent geometry data."
            )

        u, w = best_edge.endPoints()
        parent_v = w if u is v else u
        parent[v] = parent_v
        cut_edges_set.add(best_edge)

    return {
        "top_vertex": v_plus,
        "parent": parent,
        "cut_edges": list(cut_edges_set),
    }
