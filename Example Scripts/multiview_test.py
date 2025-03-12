

# Import various geometries
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *

# Import a few algorithms
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

from math import *
from random import *

# Import the viewer/scene code
from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle
from koebe.graphics.scenes.euclidean2scene import E2Scene

blackStyle = makeStyle(stroke=(0,0,0))
redStyle = makeStyle(stroke=(255,0,0), strokeWeight=2.0)

def scale_disk(D, scale):
    p = D.dualPointOP3.toPointE3()
    v = p.toVectorE3()
    q = (((v.norm() - 1)*scale + 1)*v.normalize()) + PointE3.O
    return DiskS2(q.x, q.y, q.z, 1)

def random_tutte(n):
    print(f"Generating random convex hull of {n} points and computing a Tutte embedding... ")
    poly = randomConvexHullE3(n) # Generate a random polyhedron with 16 vertices. 
    poly.outerFace = poly.faces[0] # Arbitrarily select an outer face. 
    tutteGraph = tutteEmbeddingE2(poly).duplicate(vdata_transform = lambda p: PointE2(p.x * 250, p.y * 250)) # Compute the tutte embedding of the polyhedron. 

    tutteGraph.markIndices() 

    points = [v.data for v in tutteGraph.verts]
    segments = [SegmentE2(*[v.data for v in e.endPoints()]) for e in tutteGraph.edges]
    return points, segments
    
def random_koebe(n, scale=1):
    global blackStyle, redStyle

    I1 = DiskS2(1, 0, 0, 0.975)
    I2 = DiskS2(1, 0, 0, 0.9995)

    print(f"Generating random convex hull of {n} points and computing a Tutte embedding... ")
    poly = randomConvexHullE3(n) # Generate a random polyhedron with 16 vertices. 
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
    for vIdx in range(len(packing.verts)):
        packing.verts[vIdx].idx = vIdx

    # Store each vertex's index
    for i in range(len(packing.verts)):
        packing.verts[i].name = i
    print("\tdone.")

    diskSet = [(scale_disk(DiskOP2.fromCircleE2(v.data.toPoincareCircleE2()).toDiskS2().invertThrough(I1).invertThrough(I2), scale), blackStyle)
            for v in packing.verts]

    caps = [d[0].dualPointOP3.toPointE3() for d in diskSet]
    segs = [SegmentE3(caps[i], caps[j]) for i, j in [[v.idx for v in edge.endPoints()] for edge in packing.edges]]

    orthos = [(CPlaneS2.throughThreeDiskS2(*[diskSet[v.idx][0] for v in f.vertices()]), redStyle) for f in packing.faces]

    return diskSet, caps, segs, orthos

diskSet1, caps1, segs1, orthos1 = random_koebe(12)

s1 = S2Scene(title="Packing #1")
# s1.add(diskSet1[0][0])
# s1.add(diskSet1[1][0])
s1.addAll(diskSet1)
s1.addAll([(c, redStyle) for c in caps1])
s1.addAll(segs1)

diskSet2, caps2, segs2, orthos2 = random_koebe(24)

s2 = S2Scene(title="Packing #2")
# s2.add(diskSet2[0][0])
s2.addAll(diskSet2)
s2.addAll([(c, redStyle) for c in caps2])
s2.addAll(segs2)

points, segments = random_tutte(25)
s3 = E2Scene(title="A Tutte Embedding")
s3.addAll(points)
s3.addAll(segments)

viewer.add_scene(s1)
viewer.add_scene(s2)
viewer.add_scene(s3)

viewer.run()