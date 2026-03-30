# Steepest Edge coin unfolding demo using visualize2d

from koebe.algorithms.circlepackings.layout import canonical_spherical_projection, compute_tangencies
from koebe.algorithms.incrementalConvexHull import randomConvexHullE3
from koebe.algorithms.hypPacker import maximalPacking
from steepest_edge import steepest_edge_cut_tree
from koebe.geometries.euclidean2 import CircleE2, PointE2
from koebe.geometries.euclidean3 import VectorE3
from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle
from visualize2D import display_dcel_2d

import math

n_points = 200
n_iterations = 1000

print(f"Generating random convex hull of {n_points} points and computing a circle packing...")
poly = randomConvexHullE3(n_points)
poly.outerFace = poly.faces[0]
hyp_packing, _ = maximalPacking(poly, num_passes=n_iterations)
packing = canonical_spherical_projection(hyp_packing)
packing.markIndices()
compute_tangencies(packing)
print("\tdone.")

# Compute an unfolding
unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
unfolding.markIndices()

# Build the steepest-edge tree (Rule 7) from the algorithm module.
c = VectorE3(0.0, 0.0, 1.0)
cut_tree = steepest_edge_cut_tree(packing, c)
root = cut_tree["top_vertex"]
root_idx = root.idx

# Rebuild parent pointers on the unfolding graph according to that tree.
for v in unfolding.verts:
    v.parent = None

for child, parent in cut_tree["parent"].items():
    unfolding.verts[child.idx].parent = unfolding.verts[parent.idx]

# Place the root at origin.
unfolding.verts[root_idx].data = CircleE2(PointE2(0, 0), packing.verts[root_idx].data.radiusE3)

# Children lists from parent map.
children = {v.idx: [] for v in packing.verts}
for child, parent in cut_tree["parent"].items():
    children[parent.idx].append(child.idx)

# Seed root children in one local frame around the root.
root_children = children[root_idx]
if len(root_children) > 0:
    first_child_idx = root_children[0]
    unfolding.verts[first_child_idx].data = CircleE2(
        PointE2(
            unfolding.verts[root_idx].data.radius + packing.verts[first_child_idx].data.radiusE3,
            0,
        ),
        packing.verts[first_child_idx].data.radiusE3,
    )

    root_normal = packing.verts[root_idx].data.basis3.normalize()
    root_ref_s2 = (
        packing.verts[root_idx].data.tangentPointWith(packing.verts[first_child_idx].data).toVectorE3()
        - packing.verts[root_idx].data.centerE3
    )

    for child_idx in root_children[1:]:
        child_dir_s2 = (
            packing.verts[root_idx].data.tangentPointWith(packing.verts[child_idx].data).toVectorE3()
            - packing.verts[root_idx].data.centerE3
        )
        theta = math.atan2(root_ref_s2.cross(child_dir_s2).dot(root_normal), root_ref_s2.dot(child_dir_s2))
        unfolding.verts[child_idx].data = CircleE2(
            PointE2(
                (packing.verts[root_idx].data.radiusE3 + packing.verts[child_idx].data.radiusE3) * math.cos(theta),
                (packing.verts[root_idx].data.radiusE3 + packing.verts[child_idx].data.radiusE3) * math.sin(theta),
            ),
            packing.verts[child_idx].data.radiusE3,
        )

# BFS traversal down the steepest-edge tree for the rest.
queue = list(root_children)
while queue:
    v0_idx = queue.pop(0)
    v0 = unfolding.verts[v0_idx]
    if v0.parent is None or v0.data is None:
        continue

    parent_idx = v0.parent.idx
    parent_dirE2 = (v0.parent.data.center - v0.data.center).normalize()

    parent_dirS2 = (
        packing.verts[v0_idx].data.tangentPointWith(packing.verts[parent_idx].data).toVectorE3()
        - packing.verts[v0_idx].data.centerE3
    )
    normal = packing.verts[v0_idx].data.basis3.normalize()

    for child_idx in children[v0_idx]:
        child = unfolding.verts[child_idx]
        if child.data is not None:
            continue

        child_dirS2 = (
            packing.verts[v0_idx].data.tangentPointWith(packing.verts[child_idx].data).toVectorE3()
            - packing.verts[v0_idx].data.centerE3
        )
        theta = math.atan2(parent_dirS2.cross(child_dirS2).dot(normal), parent_dirS2.dot(child_dirS2))

        direction = parent_dirE2.rotate(theta).normalize()
        child.data = CircleE2(
            v0.data.center
            + (packing.verts[v0_idx].data.radiusE3 + packing.verts[child_idx].data.radiusE3) * direction,
            packing.verts[child_idx].data.radiusE3,
        )
        queue.append(child_idx)

inversive_distances_sphere = []
inversive_distances_plane = []
for i in range(len(unfolding.verts) - 1):
    for j in range(i + 1, len(unfolding.verts)):
        if (
            unfolding.verts[j].parent != unfolding.verts[i]
            and unfolding.verts[i].parent != unfolding.verts[j]
            and unfolding.verts[i].data is not None
            and unfolding.verts[j].data is not None
        ):
            inversive_distances_sphere.append(
                packing.verts[i].data.inversiveDistTo(packing.verts[j].data)
            )
            inversive_distances_plane.append(
                unfolding.verts[i].data.inversiveDistTo(unfolding.verts[j].data)
            )

for i in range(len(inversive_distances_plane)):
    if inversive_distances_plane[i] < inversive_distances_sphere[i]:
        print(
            f"{i} {inversive_distances_plane[i]} {inversive_distances_sphere[i]} "
            f"{inversive_distances_plane[i] - inversive_distances_sphere[i]} "
            f"{inversive_distances_plane[i] > inversive_distances_sphere[i]}"
        )

if len(inversive_distances_plane) > 0:
    print(
        "Passes inversive distance test: "
        f"{not (False in [inversive_distances_plane[i] > inversive_distances_sphere[i] for i in range(len(inversive_distances_plane))])}"
    )
    print(f"Minimum inversive distance detected in the sphere: {min(inversive_distances_sphere)}")
    print(f"Minimum inversive distance detected in the plane: {min(inversive_distances_plane)}")
else:
    print("Inversive distance test skipped: no eligible vertex pairs found.")

blackStyle = makeStyle(stroke=(0, 0, 0))
redStyle = makeStyle(stroke=(255, 0, 0), strokeWeight=2, fill=None)
greenStyle = makeStyle(stroke=(0, 255, 0), strokeWeight=2, fill=None)
blueStyle = makeStyle(stroke=(0, 0, 255), strokeWeight=2, fill=None)
grayStyle = makeStyle(stroke=(128, 128, 128), strokeWeight=0.5, fill=None)

sceneS2 = S2Scene(title="Coin polyhedron", show_sphere=False)
sceneS2.addAll([
    (
        v.data,
        redStyle
        if v.idx == root_idx
        else greenStyle
        if len(root_children) > 0 and v.idx == root_children[0]
        else blueStyle
        if len(root_children) > 1 and v.idx == root_children[1]
        else blackStyle,
    )
    for v in packing.verts
])

scale = 100
sceneE2 = display_dcel_2d(
    unfolding,
    title="Steepest Edge Unfolding (visualize2d)",
    scale=scale,
    width=800,
    height=800,
    pan_and_zoom=True,
    show_faces=False,
    show_edges=False,
    show_vertices=True,
    show_tree=True,
    root_idx=root_idx,
    root_at_origin=False,
    order_from_root=True,
    vertex_style=lambda v, depth: redStyle
    if v.idx == root_idx
    else greenStyle
    if len(root_children) > 0 and v.idx == root_children[0]
    else blueStyle
    if len(root_children) > 1 and v.idx == root_children[1]
    else blackStyle,
    tree_style=grayStyle,
)

viewer.add_scene(sceneS2)
viewer.add_scene(sceneE2)
viewer.run()
