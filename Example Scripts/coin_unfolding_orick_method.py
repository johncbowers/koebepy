# Import geometries
from koebe.algorithms.circlepackings.layout import canonical_spherical_layout, compute_tangencies
from koebe.algorithms.circlepackings.newton_packing import newton_packing
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *

# Import convex hull and tutte embedding algorithms
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

# General imports
from math import *
from random import *
import heapq

# Scene and Visualization libraries
from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle
from koebe.graphics.scenes.euclidean2scene import E2Scene

n_points = 500

print(f"Generating random convex hull of {n_points} points and computing a Tutte embedding... ")
poly = randomConvexHullE3(n_points)
poly.outerFace = poly.faces[0]
print("\tdone.")

print("Computing a circle packing via Orick's Newton method... ")

packing = newton_packing(poly, quiet=False)
packing = canonical_spherical_layout(packing, n_iterations=50)
packing.markIndices()
print("\tdone.")

compute_tangencies(packing)

# Compute an unfolding
unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
unfolding.markIndices()

print(f"Placing vertex {0} ")
unfolding.verts[0].data = CircleE2(PointE2(0, 0), packing.verts[0].data.radiusE3)
nbsS2 = packing.verts[0].neighbors()
edgesS2 = packing.verts[0].edges()
nbsE2 = unfolding.verts[0].neighbors()

# Initialize the unfolding parent for each vertex to None
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

# Project all edge tangent points onto the line through the origin in direction n
for e in packing.edges:
    v = e.data - PointE3.O
    e.key = -v.dot(n)
    
# Create a min priority queue of edges keyed by projection distance
pq = [(e.key, random(), e) for e in packing.edges]
heapq.heapify(pq)

# Process edges in priority order to unfold
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
        # v0 has been placed; place v1 using the angle from v0's parent direction
        print(f"Placing vertex {v1_idx} with parent {v0_idx}")
        if v0.parent == None:
            print(f"v0 has no parent, this should not happen. v0's index is {v0_idx}")
            break
        parent_idx = v0.neighbors().index(v0.parent)
        parent_dirE2 = (v0.parent.data.center - v0.data.center).normalize()
        
        parent_dirS2 = packing.verts[v0_idx].data.tangentPointWith(packing.verts[v0.parent.idx].data).toVectorE3() - packing.verts[v0_idx].data.centerE3
        v1_dirS2 = packing.verts[v0_idx].data.tangentPointWith(packing.verts[v1_idx].data).toVectorE3() - packing.verts[v0_idx].data.centerE3
        n = packing.verts[v0_idx].data.basis3.normalize()

        theta = math.atan2(parent_dirS2.cross(v1_dirS2).dot(n), parent_dirS2.dot(v1_dirS2))
        
        v = parent_dirE2.rotate(theta).normalize()
        v1.data = CircleE2(
            v0.data.center + (packing.verts[v0_idx].data.radiusE3 + packing.verts[v1_idx].data.radiusE3) * v,
            packing.verts[v1_idx].data.radiusE3
        )
        v1.parent = v0

# ---------------------------------------------------------------------------
# Inversive distance via the Lorentz model
# ---------------------------------------------------------------------------
# A Euclidean circle with center (x, y) and radius r maps to a spacelike
# vector in the Minkowski (3,1) model:
#
#   v = (a, b, c, d) = (2x, 2y, x^2+y^2-r^2-1, x^2+y^2-r^2+1) / (2r)
#
# with inner product <v,w>_{3,1} = a1*a2 + b1*b2 + c1*c2 - d1*d2.
# The inversive distance is  delta = -<v,w>_{3,1}  (unit spacelike vectors).
#
# This avoids the catastrophic cancellation in (d^2 - r1^2 - r2^2) / (2*r1*r2)
# that plagues the naive formula when radii are small.

def _lorentz_coords_e2(circle: CircleE2):
    """Lorentz (3,1) coordinates for a Euclidean circle."""
    x, y, r = circle.center.x, circle.center.y, circle.radius
    inv2r = 1.0 / (2.0 * r)
    xxyy = x * x + y * y
    rr = r * r
    return (
        2.0 * x * inv2r,            # a
        2.0 * y * inv2r,            # b
        (xxyy - rr - 1.0) * inv2r,  # c
        (xxyy - rr + 1.0) * inv2r,  # d
    )

def _inversive_dist_lorentz_e2(c1: CircleE2, c2: CircleE2) -> float:
    """Inversive distance between two Euclidean circles via the Lorentz model."""
    a1, b1, c1L, d1 = _lorentz_coords_e2(c1)
    a2, b2, c2L, d2 = _lorentz_coords_e2(c2)
    # <v,w>_{3,1} = a1*a2 + b1*b2 + c1*c2 - d1*d2
    # For unit spacelike vectors, inversive distance = -<v,w>
    return -(a1*a2 + b1*b2 + c1L*c2L - d1*d2)


# Check the inversive distance conjecture
inversive_distances_sphere = []
inversive_distances_plane = []
min_radius_pairs = []
for i in range(len(unfolding.verts)-1):
    for j in range(i+1, len(unfolding.verts)):
        if (unfolding.verts[j].parent != unfolding.verts[i]
                and unfolding.verts[i].parent != unfolding.verts[j]
                and unfolding.verts[i].data is not None
                and unfolding.verts[j].data is not None):
            inversive_distances_sphere.append(
                packing.verts[i].data.inversiveDistTo(packing.verts[j].data))
            inversive_distances_plane.append(
                _inversive_dist_lorentz_e2(unfolding.verts[i].data, unfolding.verts[j].data))
            min_radius_pairs.append(min(
                packing.verts[i].data.radiusE3,
                packing.verts[j].data.radiusE3,
                unfolding.verts[i].data.radius,
                unfolding.verts[j].data.radius,
            ))

violations = []
for i in range(len(inversive_distances_plane)):
    diff = inversive_distances_plane[i] - inversive_distances_sphere[i]
    if diff < 0:
        violations.append({
            'index': i,
            'sphere': inversive_distances_sphere[i],
            'plane': inversive_distances_plane[i],
            'diff': diff,
            'ratio': (inversive_distances_plane[i] / inversive_distances_sphere[i]
                      if inversive_distances_sphere[i] != 0 else float('inf')),
            'min_radius': min_radius_pairs[i],
        })

if violations:
    print(f"\n{len(violations)} violations detected out of {len(inversive_distances_plane)} pairs")
    print(f"Max |violation|:  {max(abs(v['diff']) for v in violations):.6e}")
    print(f"Min |violation|:  {min(abs(v['diff']) for v in violations):.6e}")
    print(f"Mean |violation|: {sum(abs(v['diff']) for v in violations)/len(violations):.6e}")
    print(f"Min radius among violating pairs: {min(v['min_radius'] for v in violations):.6e}")
    print(f"Min ratio (plane/sphere):         {min(v['ratio'] for v in violations):.12f}")
    print(f"\nWorst 5 violations:")
    violations.sort(key=lambda v: v['diff'])
    for v in violations[:5]:
        print(f"  sphere={v['sphere']:.12f}  plane={v['plane']:.12f}  "
              f"diff={v['diff']:.6e}  min_r={v['min_radius']:.6e}")
else:
    print(f"\nNo violations. Conjecture holds for all {len(inversive_distances_plane)} pairs.")

print(f"\nPasses inversive distance test: {len(violations) == 0}")
print(f"Minimum inversive distance detected in the sphere: {min(inversive_distances_sphere)}")
print(f"Minimum inversive distance detected in the plane: {min(inversive_distances_plane)}")
print(f"Minimum radius in packing: {min(v.data.radiusE3 for v in packing.verts):.6e}")

# Create segments for the child-parent relationships
segsE2 = []
for v in unfolding.verts:
    if v.parent is not None:
        segsE2.append(SegmentE2(v.data.center, v.parent.data.center))

segsE3 = []
for v in unfolding.verts:
    if v.parent is not None:
        segsE3.append(SegmentE3(packing.verts[v.idx].data.basis3.normalize().toPointE3(), 
                                packing.verts[v.parent.idx].data.basis3.normalize().toPointE3()))

# Visualization
# blackStyle = makeStyle(stroke=(0,0,0))
# redStyle = makeStyle(stroke=(255,0,0), strokeWeight=2, fill=None)
# greenStyle = makeStyle(stroke=(0,255,0), strokeWeight=2, fill=None)
# blueStyle = makeStyle(stroke=(0,0,255), strokeWeight=2, fill=None)
# grayStyle = makeStyle(stroke=(128,128,128), strokeWeight=0.5, fill=None)
#
# sceneS2 = S2Scene(title="Coin polyhedron", show_sphere=False)
# sceneE2 = E2Scene(title="Proposed unfolding", scale=1.5, height=800, width=800, pan_and_zoom=True)
#
# sceneS2.addAll([(v.data, redStyle if v.idx == 0 else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[1].idx else blackStyle) for v in packing.verts])
# sceneS2.addAll([(s, grayStyle) for s in segsE3])
#
# scale = 100
# sceneE2.addAll([(scale * v.data, redStyle if v.idx == 0 else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[1].idx else blackStyle) for v in unfolding.verts if v.data is not None])
# sceneE2.addAll([(scale * s, grayStyle) for s in segsE2])
#
# viewer.add_scene(sceneS2)
# viewer.add_scene(sceneE2)
#
# viewer.run()
