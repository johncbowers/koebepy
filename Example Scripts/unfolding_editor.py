from koebe.graphics.p5.euclidean2viewer import *
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

from math import *
from random import *


blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
blueStyle = makeStyle(stroke=(0,0,255), fill=(255, 0, 0), strokeWeight=2.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)

# def scale_disk(D, scale):
#     p = D.dualPointOP3.toPointE3()
#     v = p.toVectorE3()
#     q = (((v.norm() - 1)*scale + 1)*v.normalize()) + PointE3.O
#     return DiskS2(q.x, q.y, q.z, 1)

# def random_koebe(n, scale=1):
#     global blackStyle, redStyle

#     I1 = DiskS2(1, 0, 0, 0.975)
#     I2 = DiskS2(1, 0, 0, 0.9995)

#     print(f"Generating random convex hull of {n} points and computing a Tutte embedding... ")
#     poly = randomConvexHullE3(n) # Generate a random polyhedron with 16 vertices. 
#     poly.outerFace = poly.faces[0] # Arbitrarily select an outer face. 
#     tutteGraph = tutteEmbeddingE2(poly) # Compute the tutte embedding of the polyhedron. 
#     print("\tdone.")

#     print("Computing a circle packing... ")
#     dists = [(v.data - PointE3.O).normSq() for v in tutteGraph.verts]
#     closestToOriginIdx = dists.index(min(dists))
#     packing, _ = maximalPacking(
#         tutteGraph, 
#         num_passes=1000, 
#         centerDartIdx = tutteGraph.darts.index(tutteGraph.verts[closestToOriginIdx].aDart)
#     )
#     for vIdx in range(len(packing.verts)):
#         packing.verts[vIdx].idx = vIdx

#     # Store each vertex's index
#     for i in range(len(packing.verts)):
#         packing.verts[i].name = i
#     print("\tdone.")

#     diskSet = [(scale_disk(DiskOP2.fromCircleE2(v.data.toPoincareCircleE2()).toDiskS2().invertThrough(I1).invertThrough(I2), scale), blackStyle)
#             for v in packing.verts]

#     caps = [d[0].dualPointOP3.toPointE3() for d in diskSet]
#     segs = [SegmentE3(caps[i], caps[j]) for i, j in [[v.idx for v in edge.endPoints()] for edge in packing.edges]]

#     orthos = [(CPlaneS2.throughThreeDiskS2(*[diskSet[v.idx][0] for v in f.vertices()]), redStyle) for f in packing.faces]

#     return diskSet, caps, segs, orthos

# diskSet, caps, segs, orthos = random_koebe(25)


# viewer = S2Viewer()

# viewer.scale = 2
# viewer.showBox = False

# packing_showing = True
# orthos_showing = False

# viewer.addAll(diskSet)
# viewer.addAll([(c, redStyle) for c in caps])
# viewer.addAll(segs)

# def key_pressed_handler(key):
#     global packing_showing, orthos_showing, diskSet, caps, segs, orthos
#     if key == "s":
#         viewer.toggleSphere()
#     elif key == "r":
#         viewer._view_x = 0
#         viewer._view_y = 0
#     elif key == "p":
#         if packing_showing: 
#             viewer.removeAll(diskSet)
#             viewer.removeAll(segs)
#             packing_showing = False
#         else:
#             viewer.addAll(diskSet)
#             viewer.addAll(segs)
#             packing_showing = True
#     elif key == "o":
#         if orthos_showing: 
#             viewer.removeAll(orthos)
#             orthos_showing = False
#         else:
#             viewer.addAll(orthos)
#             orthos_showing = True
#     elif key == "n":
#         packing_showing = True
#         orthos_showing = False
#         viewer.clear()
#         diskSet, caps, segs, orthos = random_koebe(25)
#         viewer.addAll(diskSet)
#         viewer.addAll([(c, redStyle) for c in caps])
#         viewer.addAll(segs)
#     elif key == "m":
#         packing_showing = True
#         orthos_showing = False
#         viewer.clear()
#         diskSet, caps, segs, orthos = random_koebe(25, scale=0.7)
#         viewer.addAll(diskSet)
#         viewer.addAll([(c, redStyle) for c in caps])
#         viewer.addAll(segs)
        

# viewer._key_pressed_handler = key_pressed_handler


# viewer.show()



mouse_down = False
selected_idx = -1
closest_idx = -1
closest_dist = float('inf')


def create_random_tutte():
    global points, tutteGraph
    print("Generating random convex hull of eight points and computing a Tutte embedding... ")
    poly = randomConvexHullE3(25) # Generate a random polyhedron with 16 vertices. 
    poly.outerFace = poly.faces[0] # Arbitrarily select an outer face. 
    tutteGraph = tutteEmbeddingE2(poly) # Compute the tutte embedding of the polyhedron. 
    print("\tdone.")
    
    xs = [v.data.x for v in tutteGraph.verts]
    ys = [v.data.y for v in tutteGraph.verts]

    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    extent = max(maxx-minx, maxy-miny)

    points = [PointE2(1400*(v.data.x-minx)/extent + 200, 1400*(v.data.y-miny)/extent + 100) for v in tutteGraph.verts]

    for vIdx in range(len(tutteGraph.verts)):
        tutteGraph.verts[vIdx].idx = vIdx
    
    refresh_points(points)

def refresh_points(new_points):
    global closest_idx, selected_idx, viewer, points
    viewer.clear()
    viewer.addAll([(SegmentE2(*[points[v.idx] for v in e.endPoints()]), blackStyle) for e in tutteGraph.edges])
    viewer.addAll([
        (new_points[pIdx], redStyle if pIdx == selected_idx else blackStyle if closest_dist >= 225 or closest_idx != pIdx else blueStyle) for pIdx in range(len(new_points))
    ])
    points = new_points
    
def mouse_pressed_handler(event):
    global mouse_down, closest_idx, closest_dist, selected_idx
    if closest_dist < 225:
        selected_idx = closest_idx
    mouse_down = True
    refresh_points(points)

def mouse_released_handler(event):
    global mouse_down, selected_idx
    mouse_down = False
    selected_idx = -1
    refresh_points(points)

def mouse_moved_handler(event):
    global points, mouse_down, closest_idx, closest_dist, selected_idx
    p = PointE2(event.x, event.y)
    distSqs = [p.distSqTo(q) for q in points]
    closest_dist = min(distSqs)
    closest_idx = distSqs.index(closest_dist)
    if selected_idx != -1:
        new_points = [points[pIdx] if pIdx != selected_idx else PointE2(event.x, event.y) for pIdx in range(len(points))]
        closest_dist = 0
        refresh_points(new_points)
    else:
        refresh_points(points)

def key_pressed_handler(event):
    if event.key == " ":
        create_random_tutte()

viewer = E2Viewer()
create_random_tutte()
viewer._mouse_moved_handler = mouse_moved_handler
viewer._mouse_pressed_handler = mouse_pressed_handler
viewer._mouse_released_handler = mouse_released_handler
viewer._mouse_dragged_handler = mouse_moved_handler
viewer._key_pressed_handler = key_pressed_handler
viewer.show()
