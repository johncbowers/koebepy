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

print("Generating random convex hull of eight points and computing a Tutte embedding... ")
poly = randomConvexHullE3(100) # Generate a random polyhedron with 16 vertices. 
poly.outerFace = poly.faces[0] # Arbitrarily select an outer face. 
tutteGraph = tutteEmbeddingE2(poly) # Compute the tutte embedding of the polyhedron. 
print("\tdone.")

print("Computing a circle packing... ")
dists = [(v.data - PointE3.O).normSq() for v in tutteGraph.verts]
closestToOriginIdx = dists.index(min(dists))
packing, _ = maximalPacking(
    tutteGraph, 
    num_passes=1000, 
    centerDartIdx = tutteGraph.darts.index(tutteGraph.verts[closestToOriginIdx].aDart)
)

# Store each vertex's index
for i in range(len(packing.verts)):
    packing.verts[i].name = i
print("\tdone.")

print("Computing a random path... ")
path = [packing.verts[randint(0, len(packing.verts)-1)]]
visited = set(path)
while True: 
    neighborhood = list(set(path[-1].neighbors()) - visited)
    if len(neighborhood) > 0:
        random_neighbor = neighborhood[randint(0, len(neighborhood)-1)]
        path.append(random_neighbor)
        visited.add(random_neighbor)
    else:
        break
path_set = set(path)
path_disks = [v.data for v in path]
print("\tdone.")
print(f"\tObtained a path of length: {len(path)}")

# D1 = DiskS2(0, 0, 2, 1.6)
# D2 = DiskS2(0, 2, 0, 1.6)

# D1 = DiskS2(0, 0, -sqrt(2), 1)
# D2 = DiskS2(-sqrt(2), 0, 0, 1)

# print(D1.inversiveDistTo(D2))

# Inversion disks to improve the view
I1 = DiskS2(1, 0, 0, 0.975)
I2 = DiskS2(1, 0, 0, 0.9995)

viewer = S2Viewer()

viewer.scale = 2
viewer.showBox = False

blackStyle = makeStyle(stroke=(0,0,0))
redStyle = makeStyle(stroke=(255,0,0), strokeWeight=2.0)

diskSet = [(DiskOP2.fromCircleE2(v.data.toPoincareCircleE2()).toDiskS2().invertThrough(I1).invertThrough(I2), 
            redStyle if v in path_set else blackStyle)
           for v in packing.verts]

disks = [DiskOP2.fromCircleE2(D.toPoincareCircleE2()).toDiskS2().invertThrough(I1).invertThrough(I2) for D in path_disks]
caps = [d.dualPointOP3.toPointE3() for d in disks]
segs = [SegmentE3(caps[i], caps[i+1]) for i in range(len(caps)-1)]

vs = [(c - PointE3.O).normalize() for c in caps]
ns = [vs[i].cross(vs[i+1]).normalize() for i in range(len(vs) - 1)]

thetas = [
    math.atan2(vs[i+1].dot(ns[i].cross(ns[i+1])), ns[i].dot(ns[i+1]))
    for i in range(len(ns) - 1)
]

cos_thetas = [
    ns[i].dot(ns[i+1])
    for i in range(len(ns) - 1)
]

sin_thetas = [
    vs[i+1].dot(ns[i].cross(ns[i+1]))
    for i in range(len(ns) - 1)
]
    # math.acos(ns[i].dot(ns[i+1])) for i in range(len(ns) - 1)]


vE2s = [VectorE2(1, 0)]
ctrs = [PointE2(0, 0)]

for i in range(len(vs) - 1):
    ri, rip1 = disks[i].radiusE3, disks[i+1].radiusE3
    ctrs.append(ctrs[-1] + (ri+rip1)*vE2s[-1])
    if (i != len(vs)-2):
        vE2s.append(vE2s[-1].rotate(c=cos_thetas[i], s=sin_thetas[i]))

circs = [CircleE2(ctrs[i], disks[i].radiusE3) for i in range(len(disks))]

test_passed = True
for i in range(len(circs)-3):
    for j in range(i+3, len(circs)):
        if circs[i].inversiveDistTo(circs[j]) < 0.999:
            print("Failure detected.")
            print(i, j, circs[i].inversiveDistTo(circs[j]))
            print(circs[i])
            print(circs[j])
            test_passed = False
            break

print(f"Zipper Test: {'passed' if test_passed else 'failed'}")

packing_showing = True
viewer.addAll(diskSet)
viewer.addAll(circs)

# viewer.addAll([(c, redStyle) for c in caps])
viewer.addAll([(s, redStyle) for s in segs])
# viewer.add(D1)
# viewer.add(D2)
# viewer.add(D1.dualPointOP3)
# viewer.add(D2.dualPointOP3)
# viewer.add(SegmentE3(D1.dualPointOP3.toPointE3(), D2.dualPointOP3.toPointE3()))


def key_pressed_handler(key):
    global packing_showing
    if key == "s":
        viewer.toggleSphere()
    elif key == "r":
        viewer._view_x = 0
        viewer._view_y = 0
    elif key == "p":
        if packing_showing: 
            viewer.removeAll(diskSet)
            viewer.removeAll(segs)
            packing_showing = False
        else:
            viewer.addAll(diskSet)
            viewer.addAll(segs)
            packing_showing = True

viewer._key_pressed_handler = key_pressed_handler


viewer.show()


