from koebe.geometries.spherical2 import *
from koebe.geometries.commonOps import *

def wingDiskOf(dart):
    if dart.dcel.outerFace == dart.face:
        return DiskS2(0, 0, -1, 0)
    else:
        return dart.prev.origin.data

def computeVoronoiArc(d1, d2, d3, d4):
    bisector12 = d1.bisectorWith(d2)
    bisector23 = d1.bisectorWith(d3)
    bisector24 = d1.bisectorWith(d4)
    
    dual12 = bisector12.dualDiskS2
    dual23 = bisector23.dualDiskS2
    dual24 = bisector24.dualDiskS2
    
    cfDual12a = CoaxialFamilyS2(dual12, dual23)
    cfDual12b = CoaxialFamilyS2(dual12, dual24)
    
    genPoints1 = cfDual12a.generatorPoints()
    genPoints2 = cfDual12b.generatorPoints()
    
    ortho123 = CPlaneS2.throughThreeDiskS2(d1, d2, d3)
    ortho142 = CPlaneS2.throughThreeDiskS2(d1, d4, d2)
    
    pt1DotOrtho123 = inner_product4(ortho123.a, ortho123.b, ortho123.c, ortho123.d,
                                   genPoints1[0].x, genPoints1[0].y, genPoints1[0].z, 1)
    
    if len(genPoints1) == 1 or isZero(pt1DotOrtho123):
        pt1 = genPoints1[0]
    else:
        pt1 = genPoints1[1]
    
    pt2DotOrtho142 = inner_product4(ortho142.a, ortho142.b, ortho142.c, ortho142.d,
                                   genPoints2[0].x, genPoints2[0].y, genPoints2[0].z, 1)
    
    if len(genPoints2) == 1 or isZero(pt2DotOrtho142):
        pt2 = genPoints2[0]
    else:
        pt2 = genPoints2[1]

    return CircleArcS2(pt1, pt2, dual12)
    
    
def computeVoronoiArcForEdge(edge):
    dart = edge.aDart
    disk1 = dart.origin.data
    disk2 = dart.dest.data
    disk3 = wingDiskOf(dart)
    disk4 = wingDiskOf(dart.twin)
    return computeVoronoiArc(disk1, disk2, disk3, disk4)

def inversiveVoronoi(packing):
    return [computeVoronoiArcForEdge(e) for e in packing.edges]