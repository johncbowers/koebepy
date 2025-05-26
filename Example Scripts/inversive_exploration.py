

from random import random
from koebe.algorithms.circlepackings.layout import canonical_spherical_layout, canonical_spherical_layout_v2, canonical_spherical_projection
from koebe.algorithms.hypPacker import maximalPacking
from koebe.algorithms.incrementalConvexHull import randomConvexHullE3
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2
from koebe.geometries.euclidean3 import PointE3, SegmentE3
from koebe.geometries.spherical2 import CPlaneS2, DiskS2

from koebe.graphics.scenes.spherical2scene import S2Scene

from koebe.graphics.flask.spherical2server import viewer
from koebe.graphics.spherical2viewer import makeStyle
import math


n_points = 50
n_iterations = 1000

print(f"Generating random convex hull of {n_points} points and computing a Tutte embedding... ")
poly = randomConvexHullE3(n_points) # Generate a random polyhedron with 16 vertices. 
poly.outerFace = poly.faces[0] # Arbitrarily select an outer face. 
tutteGraph = tutteEmbeddingE2(poly) # Compute the tutte embedding of the polyhedron. 
print("\tdone.")

print("Computing a circle packing... ")
I1 = DiskS2(1, 0, 0, 0)

dists = [(v.data - PointE3.O).normSq() for v in tutteGraph.verts]
closestToOriginIdx = dists.index(min(dists))
hyp_packing, _ = maximalPacking(
    tutteGraph, 
    num_passes=n_iterations, 
    centerDartIdx = tutteGraph.darts.index(tutteGraph.verts[closestToOriginIdx].aDart)
)
packing = canonical_spherical_projection(hyp_packing, n_iterations=50)
# packing = packing.duplicate(
# #    vdata_transform=lambda d: DiskS2(d.a, d.b, d.c, (d.d*1.01 if d.radiusE3 > 0.15 else d.d*.99) if random() < 0.5 else d.d*.95)
#     vdata_transform=lambda d: DiskS2(d.a, d.b, d.c, (0.8+(random()/5.0)) * math.sqrt(d.a * d.a + d.b * d.b + d.c * d.c))
# )
# packing = canonical_spherical_layout(packing)
packing.markIndices()
print("\tdone.")


blueStyle = makeStyle(stroke=(0,0,255), strokeWeight=2, fill=None)
redStyle = makeStyle(stroke=(255,0,0), strokeWeight=2, fill=None)

caps = [v.data.dualPointOP3.toPointE3() for v in packing.verts]
segs = [SegmentE3(pi, pj) for pi, pj in [[v.data.dualPointOP3.toPointE3() for v in edge.endPoints()] for edge in packing.edges]]

scene = S2Scene()

scene.addAll([(v.data, blueStyle) for v in packing.verts])
scene.addAll([(CPlaneS2.throughThreeDiskS2(*[v.data for v in f.vertices()]), redStyle) for f in packing.faces])
scene.addAll(segs)

viewer.loadScene(scene)
viewer.run()
