import sys

from koebe.algorithms.poissonDiskSampling import slowUniformDartThrowing, slowUniformDartThrowingWithBoundary

from koebe.geometries.euclidean2 import PointE2
from koebe.geometries.spherical2 import PointS2
from koebe.geometries.euclidean3 import PointE3
from koebe.graphics.euclidean2viewer import UnitScaleE2Sketch, makeStyle
from koebe.graphics.spherical2viewer import S2Viewer

from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3

from random import random

if len(sys.argv) != 3:
    print("USAGE: python poisson_sampling.py radius out-file")
else:
    samples = []
    samples = slowUniformDartThrowingWithBoundary(float(sys.argv[1]))
    samplePoints = [PointE2(2*sample[0] - 1, 2*sample[1] - 1) for sample in samples]

    s2points = [PointS2.sgProjectFromPointE2(p) for p in samplePoints]

    pts = [(sp.directionE3.vec * (1 + random() / 10000)).toPointE3() for sp in s2points]
   
    mesh = incrConvexHull(pts + [PointE3(0,0,-1)], orientationPointE3)
    mesh.outerFace = mesh.verts[-1].remove()

    mesh2 = mesh.duplicate(
        vdata_transform = (lambda v : PointS2(v.x, v.y, v.z).sgProjectToPointE2())
    )

    vtoi = dict([(v, k) for k, v in enumerate(mesh2.verts)])

    # convert a face to a string:
    f_to_s = (lambda f : [vtoi[v] for v in f.vertices()])

    # Because of the random perturbation we are using, we get some degenerate triangles 
    # along the boundary and have to filter them out. 
    def valid_face(f):
        vcoords = [tuple(v.data) for v in f.vertices()]
        return ((vcoords[0][0] != vcoords[1][0] or vcoords[1][0] != vcoords[2][0] or vcoords[0][0] != vcoords[2][0]) 
                and (vcoords[0][1] != vcoords[1][1] or vcoords[1][1] != vcoords[2][1] or vcoords[0][1] != vcoords[2][1]))
    
    faces = [f for f in mesh2.faces if valid_face(f)]
    vert_string = "".join([f"{x} {y}\n" for x, y in [tuple(v.data) for v in mesh2.verts]])
    triangle_string = "".join([f"{i} {j} {k}\n" for i, j, k in [f_to_s(f) for f in faces if f != mesh2.outerFace]])
    
    out_string = f"vertex-count triangle-count\n{len(mesh2.verts)} {len(faces)}\n" + vert_string + triangle_string
    
    outfile = open(sys.argv[2], 'w')
    outfile.write(out_string)
    outfile.close()
