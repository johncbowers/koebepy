

from random import random
from koebe.algorithms.circlepackings.layout import canonical_spherical_layout, canonical_spherical_layout_v2, canonical_spherical_projection
from koebe.algorithms.hypPacker import maximalPacking
from koebe.algorithms.incrementalConvexHull import randomConvexHullE3
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2
from koebe.geometries.euclidean2 import PointE2
from koebe.geometries.euclidean3 import PointE3, SegmentE3, VectorE3
from koebe.geometries.spherical2 import CPlaneS2, DiskS2

from koebe.graphics.scenes.spherical2scene import S2Scene

from koebe.graphics.flask.spherical2server import viewer
from koebe.graphics.spherical2viewer import makeStyle
import math



pointsE2 = [PointE2(random() * 0.1, random() * 0.1) for _ in range(10)]

lifted_points = [VectorE3(p.x, p.y, (1 - p.x*p.x + p.y*p.y)**0.5) for p in pointsE2] + [VectorE3(1,0,0)]
print(f"Norm: {((1/len(lifted_points)) * sum(lifted_points, start=VectorE3(0,0,0))).norm()}")

disks = [DiskS2(p.x, p.y, p.z, -1) for p in lifted_points]

for _ in range(10):

    I1 = DiskS2(1,0,0,0)
    disks = [d.invertThrough(I1) for d in disks]
    
    center_of_mass = (1/len(disks)) * sum(disks, start=DiskS2(0,0,0,0))
    new_center = DiskS2(0, 0, 0, math.sqrt(abs(center_of_mass.lorentzTo(center_of_mass))))

    I2 = new_center.bisectorWith(center_of_mass).dualDiskS2
    
    disks = [d.invertThrough(I2) for d in disks]
    
    lifted_points = [VectorE3(d.a/d.d, d.b/d.d, d.c/d.d) for d in disks]
    
    print(f"Norm: {((1/len(lifted_points)) * sum(lifted_points, start=VectorE3(0,0,0))).norm()}")
    



blueStyle = makeStyle(stroke=(0,0,255), strokeWeight=2, fill=None)
redStyle = makeStyle(stroke=(255,0,0), strokeWeight=2, fill=None)

scene = S2Scene()

scene.addAll([p.toPointE3() for p in lifted_points])

viewer.loadScene(scene)
viewer.run()
