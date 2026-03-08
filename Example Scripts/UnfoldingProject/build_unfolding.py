import math
from argparse import ArgumentError
from collections import deque, defaultdict
from typing import Optional

from koebe.datastructures.dcel import DCEL, Vertex
from koebe.geometries.euclidean2 import CircleE2, PointE2

"""
A file for functions that help build the geometry of the unfolding from
an unfolding tree.
"""

# Disabled inspection since we know these DCEL objects have idx fields.
# noinspection PyUnresolvedReferences
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
        # Compute angle between grandparent -> parent and parent->child on the packing

        parent_dirE2 = (parent.parent.data.center - parent.data.center).normalize()

        parent_dirS2 = packing.verts[parent_idx].data.tangentPointWith(packing.verts[parent.parent.idx].data).toVectorE3() - \
                       packing.verts[parent_idx].data.centerE3
        v1_dirS2 = packing.verts[parent_idx].data.tangentPointWith(packing.verts[child_idx].data).toVectorE3() - \
                   packing.verts[parent_idx].data.centerE3
        n = packing.verts[parent_idx].data.basis3.normalize()
        theta = math.atan2(parent_dirS2.cross(v1_dirS2).dot(n), parent_dirS2.dot(v1_dirS2))

        # Now place child on the plane based on the angle
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


def _build_parent_map(dcel: DCEL, root: Optional[Vertex], parent_of):
    """Build a parent map from explicit parents or a BFS spanning tree."""
    if parent_of is not None:
        return parent_of

    parent_map = {}
    has_explicit_parent = False
    for v in dcel.verts:
        if hasattr(v, "parent") and v.parent is not None:
            parent_map[v] = v.parent
            has_explicit_parent = True

    if has_explicit_parent:
        return parent_map

    if not dcel.verts:
        return parent_map

    start = root or dcel.verts[0]
    queue = deque([start])
    visited = {start}
    parent_map[start] = None
    while queue:
        v = queue.popleft()
        for nb in v.neighbors():
            if nb in visited:
                continue
            visited.add(nb)
            parent_map[nb] = v
            queue.append(nb)

    return parent_map

def unfolding_geometry_from_tree(packing: DCEL, unfolding: DCEL,
                                 root_idx: int) -> None:
    """
    Constructs unfolding geometry given packing and parent relationships in a tree.
    :param packing:
    :param unfolding:
    :param root_idx:
    :return:
    """
    parent_dict = _build_parent_map(unfolding, unfolding.verts[root_idx], None)

    """ Phase 1: turn parent-child relationships into explicit dictionary"""
    # Invert the child->parent dictionary to get the parent->child one
    join_tree = defaultdict(list)
    for key, value in parent_dict.items():
        join_tree[value].append(key)

    """ Phase 2: Create geometrical data"""
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