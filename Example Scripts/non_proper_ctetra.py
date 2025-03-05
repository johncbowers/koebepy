from koebe.graphics.p5.spherical2viewer import *
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

from math import *
from random import *


# print(f"3,4 {disks[2].inversiveDistTo(disks[3])}")
# print(f"3,5 {disks[2].inversiveDistTo(disks[4])}")
# print(f"4,6 {disks[3].inversiveDistTo(disks[5])}")

# D1 = DiskS2(-1.0748811207324158, -0.0, -0.0, 1)
# D2 = DiskS2(1.0748811207324158, 0.0, -0.0, 1)

# print(f"Back to front: {D1.inversiveDistTo(D2)}")



viewer = S2Viewer()

viewer.scale = 2
viewer.showBox = False

blackStyle = makeStyle(stroke=(0,0,0))
blueStyle = makeStyle(stroke=(0,0,255))
redStyle = makeStyle(stroke=(255,0,0), strokeWeight=2.0)


# 0.0, 0.0, 2.7269530298948657


A = DiskS2(0.0, 0.0, 1.1, 1.0)
B = DiskS2(0.9, 0.7, 0.2, 1.0)
C = DiskS2(0.9, -0.7, -0.2, 1.0)
D = DiskS2(0.0, 0.0, -1.0, 0.0)

I1 = DiskS2(0, 0, -1.2, 1)
I2 = DiskS2(0, 0, -1.4, 1)

tetra = [x.invertThrough(I2).invertThrough(I1) for x in [A, B, C, D]]
verts = [x.dualPointOP3.toPointE3() for x in tetra if x.d != 0]
edges = [SegmentE3(verts[i], verts[j]) for i in range(len(verts)-1) for j in range(i+1, len(verts))]
orthos = [CPlaneS2.throughThreeDiskS2(tetra[i], tetra[j], tetra[k]) 
          for i in range(len(verts)-2) 
          for j in range(i+1, len(verts)-1) 
          for k in range(j+1, len(verts))]
ortho_disks = [o.dualDiskS2 for o in orthos]

print(A.inversiveDistTo(D))

packing_showing = True
viewer.addAll(tetra)
#viewer.addAll(verts)
viewer.addAll(edges)
orthos_showing = True
viewer.addAll([(o, redStyle) for o in ortho_disks])

def key_pressed_handler(key):
    global packing_showing, orthos_showing
    if key == "s":
        viewer.toggleSphere()
    # elif key == "r":
    #     viewer._view_x = 0
    #     viewer._view_y = 0
    elif key == "p":
        if packing_showing: 
            viewer.removeAll(tetra)
            packing_showing = False
        else:
            viewer.addAll(diskSet)
            packing_showing = True
    elif key == "o":
        if orthos_showing: 
            viewer.removeAll(ortho_disks)
            orthos_showing = False
        else:
            viewer.addAll(ortho_disks)
            orthos_showing = True

viewer._key_pressed_handler = key_pressed_handler

viewer.show()


