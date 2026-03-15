# Import geometries
from koebe.algorithms.circlepackings.layout import canonical_spherical_projection, compute_tangencies
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *

# Import convex hull, circle packing, and tutte embedding algorithms
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

# General imports
from math import *
from random import *
import heapq

# Scene and Visualization libraries
from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle
from koebe.graphics.scenes.euclidean2scene import E2Scene

n_points = 100
n_iterations = 10000

print(f"Generating random convex hull of {n_points} points and computing a Tutte embedding... ")
poly = randomConvexHullE3(n_points) # Generate a random polyhedron with 16 vertices. 
poly.outerFace = poly.faces[0] # Arbitrarily select an outer face. 
print("\tdone.")

print("Computing a circle packing... ")

hyp_packing, _ = maximalPacking(
    poly, 
    num_passes=n_iterations 
)
packing = canonical_spherical_projection(hyp_packing)
packing.markIndices()
print("\tdone.")

compute_tangencies(packing)

def bfs(dcel, start_vertex_idx=0):
    Q = deque([(None, dcel.verts[start_vertex_idx])])
    parentOf = {}
    while Q:
        p, v = Q.popleft()
        if v not in parentOf:
            parentOf[v] = p
            for w in v.neighbors():
                Q.append((v, w)) 
    return parentOf

def bfs_dual_tree_from_primal(dcel, primal_tree, start_face_idx=0):
    edge_map = dcel.vertexPairToEdgeMap()
    primal_edge_set = set(edge_map[(v, p)] for v, p in primal_tree.items() if p is not None)

    Q = deque([(None, dcel.faces[start_face_idx])])
    parentOf = {}
    while Q:
        p, f = Q.popleft()
        if f not in parentOf:
            parentOf[f] = p
            for dart in f.darts():
                # if the edge corresponding to this dart is not in the primal tree, then we can traverse it in the dual tree
                e = dart.edge
                if e not in primal_edge_set:
                    # get the face on the other side of this edge
                    g = dart.twin.face
                    Q.append((f, g)) 
    return parentOf

primal_tree = bfs(packing)
dual_tree = bfs_dual_tree_from_primal(packing, primal_tree)
vertex_pair_edge_map = packing.vertexPairToEdgeMap()
face_pair_edge_map = packing.facePairToEdgeMap()

# Put together the visualization

blackStyle = makeStyle(stroke=(0,0,0))
redStyle = makeStyle(stroke=(255,0,0), strokeWeight=2, fill=None)
greenStyle = makeStyle(stroke=(0,255,0), strokeWeight=2, fill=None)
blueStyle = makeStyle(stroke=(0,0,255), strokeWeight=2, fill=None)
grayStyle = makeStyle(stroke=(128,128,128), strokeWeight=0.5, fill=None)


# loop over each edge uv in the primal_tree and create two SegmentE3 objects, 
# one from the euclidean center of the disk u to the tangency point of the disks (stored on 
# the edge data), and one from the euclidean center of the disk v to the tangency point of the disks.
# with blueStyle
primal_tree_segs = []
for v, p in primal_tree.items():
    if p is not None:
        e = vertex_pair_edge_map[(v, p)]
        tangency_point = e.data
        primal_tree_segs.append((SegmentE3(v.data.centerE3, tangency_point), blueStyle))
        primal_tree_segs.append((SegmentE3(p.data.centerE3, tangency_point), blueStyle))

# Create CPlaneS2 objects for each face and store them at the .data of each face
# using CPlaneS2.throughThreeDiskS2 (since DiskS2 objects are stored at each vertex)
for f in packing.faces:
    f.data = CPlaneS2.throughThreeDiskS2(*[v.data for v in f.vertices()])

# The Euclidean center of a CPlaneS2 object can be obtained via
# .dualDiskS2.centerE3. 
# loop over every edge uv in the dual tree and create a SegmentE3 from the euclidean center 
# of the CPlaneS2 object stored at face u to the tangency point stored at the edge.data, and then 
# one from the tangency point to the euclidean center of the CPlaneS2 object 
# stored at face v, with redStyle
dual_tree_segs = []
for f, p in dual_tree.items():
    if p is not None:
        e = face_pair_edge_map[(f, p)]
        tangency_point = e.data
        dual_tree_segs.append((SegmentE3(f.data.dualDiskS2.centerE3, tangency_point), redStyle))
        dual_tree_segs.append((SegmentE3(p.data.dualDiskS2.centerE3, tangency_point), redStyle))


sceneS2 = S2Scene(title="Coin polyhedron", show_sphere=False)
#sceneE2 = E2Scene(title="Proposed unfolding", scale=1.5, height=800, width=800, pan_and_zoom=True)

sceneS2.addAll(primal_tree_segs)
#sceneS2.addAll([(f.data, redStyle) for f in packing.faces])
sceneS2.addAll(dual_tree_segs)

sceneS2.addAll([(v.data, blackStyle) for v in packing.verts])
#sceneS2.addAll([(v.data, redStyle if v.idx == 0 else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[1].idx else blackStyle) for v in packing.verts])
#sceneS2.addAll([(s, grayStyle) for s in segsE3])


# scale = 100
# sceneE2.addAll([(scale * v.data, redStyle if v.idx == 0 else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[1].idx else blackStyle) for v in unfolding.verts if v.data is not None])
# #sceneE2.addAll([e.data for e in unfolding.edges if e.data is not None])
# sceneE2.addAll([(scale * s, grayStyle) for s in segsE2])

viewer.add_scene(sceneS2)
# viewer.add_scene(sceneE2)

viewer.run()

