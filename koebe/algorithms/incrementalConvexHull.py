from ..datastructures.dcel import DCEL, Vertex, Dart, Face, Edge
from ..geometries.commonOps import determinant4
from ..geometries.euclidean3 import PointE3

import math
from random import uniform

#
# Compute the 3D convex hull of a list of points. This method also needs
# an orientation test for tetrahedra of the given point type. A point is
# considered inside the convex hull if it has positive orientation with respect
# to each triangle of teh hull. 
#
# This code currently assumes no four points are collinear (i.e. for no four
# points) does orientation(p1, p2, p3, p4) return 0. 
# TODO Remove the need for this assumption
#
# Parameters:
# * points: PointT - The list of points in some 3D point type
# * orientation: (PointT, PointT, PointT, PointT) -> float an orientation function
#
# Returns: the convex hull of the points as a DCEL
def incrConvexHull(points, orientation):
    if len(points) < 2:
        return DCEL()
    elif len(points) == 3:
        return incrConvexHullOfThreePoints(points[0], points[1], points[2])
    else:
        ch = incrConvexHullOfFourPoints(points[0], points[1], points[2], points[3], orientation)
        for point in points[4:]:
            addPoint(ch, point, orientation)
        return ch

#### SOME CONVEX HULL GENERATORS

def randomConvexHullE3(numPoints):
    
    # We require at least four points
    if (numPoints < 4):
        return None
    
    # Let's not do floating point multiplication more than necessary
    # here's 2*pi
    twopi = 2.0 * math.pi
    
    # Generate random samples of the sphere. Note that these are not
    # a uniform sampling of the sphere. 
    samples = [(uniform(0, twopi), uniform(0, math.pi))
                for _ in range(numPoints)]
    
    points = [PointE3(1.01 * math.cos(theta) * math.sin(phi),
                      1.01 * math.sin(theta) * math.sin(phi),
                      1.01 * math.cos(phi))
              for (theta, phi) in samples]
    
    # Compute the convex hull of the samples
    return incrConvexHull(points, orientationPointE3)

def tetrahedron(size = 1):
    points = [PointE3(size, -size / math.sqrt(3), -size / math.sqrt(6)), 
              PointE3(-size, -size / math.sqrt(3), -size / math.sqrt(6)),
              PointE3(0, 2*size / math.sqrt(3), -size / math.sqrt(6)),
              PointE3(0, 0, 3*size / math.sqrt(6))]
    return incrConvexHull(points, orientationPointE3)
        
#### HELPER FUNCTIONS

def isVisible(face, p, orientation):
    corners = face.darts()
    p1, p2, p3 = [c.origin.data for c in corners[0:3]]
    return orientation(p1, p2, p3, p) < 0.0

def addPoint(ch, p, orientation):
    # First let's filter the faces to obtain a set of all faces that are visible from the
    # insertion point p
    visibleFaces = set([f for f in ch.faces if isVisible(f, p, orientation)])
    # visibleFaces = set(filter(lambda f: isVisible(f, p, orientation), ch.faces))
    
    # Next, check if there are any visible faces, because if there are 
    # not, then this point is already inside the convex hull, so there 
    # is nothing left to do--just return
    if len(visibleFaces) == 0:
        return
    
    # Otherwise, we need to get the set of shadowFaces as well as the 
    # darts that are visible and in shadow.
    shadowFaces  = set([f for f in ch.faces if not isVisible(f, p, orientation)])
    visibleDarts = set([d for d in ch.darts if d.face in visibleFaces])
    shadowDarts = set([d for d in ch.darts if d.face in shadowFaces])

    # shadowFaces  = set(filter(lambda f: not isVisible(f, p, orientation), ch.faces))
    # visibleDarts = set(filter(lambda d: d.face in visibleFaces, ch.darts))
    # shadowDarts  = set(filter(lambda d: d.face in shadowFaces, ch.darts))
    
    # Retain only faces that are not visible to point p
    ch.faces = [face for face in ch.faces if not face in visibleFaces]
    
    # Retain only vertices incident to a shadow face: 
    ch.verts = [vertex for vertex in ch.verts
                       if not shadowFaces.isdisjoint(vertex.faces())]
    
    # Remove all visible darts
    ch.darts = [dart for dart in ch.darts if not dart in visibleDarts]
    
    # Remove all visible edges (an edge is visible if both its darts are)
    ch.edges = [edge for edge in ch.edges
                     if not (edge.aDart in visibleDarts and 
                             edge.aDart.twin in visibleDarts)]
    
    # Next, let's collect the darts that are on the boundary, meaning each shadow dart whose twin is a visible dart.
    shadowBoundaryDarts = [dart for dart in shadowDarts if dart.twin in visibleDarts]
    
    v = Vertex(ch, data = p) # Create the new vertex
    
    for dart in shadowBoundaryDarts:
        a = dart.dest
        b = dart.origin
        c = v
        
        abc = Face(ch)
        
        eab = dart.edge
        
        dab = Dart(ch, edge = eab, origin = a, face = abc, twin = dart)
        dbc = Dart(ch, origin = b, face = abc, prev = dab)
        dca = Dart(ch, origin = c, face = abc, prev = dbc, next = dab)
    
    # TODO continue from tailrec nextShadowDart in Kotlin code
    def nextShadowDart(dart):
        curDart = dart
        while True:
            if curDart == None:
                return None
            elif curDart.prev in shadowBoundaryDarts:
                return curDart.prev
            else:
                curDart = curDart.prev.twin
    
    start = shadowBoundaryDarts[0]
    curr  = start
    
    while True:
        next = nextShadowDart(curr)
        
        edge = Edge(ch)
        
        curr.twin.next.edge = edge
        next.twin.prev.edge = edge
        edge.aDart = curr.twin.next
        
        curr.twin.next.makeTwin(next.twin.prev)
        
        curr = next
        
        if curr == start:
            break
            
def incrConvexHullOfFourPoints(p1, p2, p3, p4, orientation):
    
    ch = DCEL()
    
    orient = orientation(p1, p2, p3, p4)
    
    v1 = Vertex(ch, data = p1 if orient > 0 else p2)
    v2 = Vertex(ch, data = p2 if orient > 0 else p1)
    v3 = Vertex(ch, data = p3)
    v4 = Vertex(ch, data = p4)
    
    e12 = Edge(ch)
    e23 = Edge(ch)
    e13 = Edge(ch)
    e14 = Edge(ch)
    e24 = Edge(ch)
    e34 = Edge(ch)
    
    f123 = Face(ch)
    f134 = Face(ch)
    f142 = Face(ch)
    f243 = Face(ch)
    
    d12 = Dart(ch, edge = e12, origin = v1, face = f123)
    d23 = Dart(ch, edge = e23, origin = v2, face = f123, prev = d12)
    d31 = Dart(ch, edge = e13, origin = v3, face = f123, prev = d23, next=d12)

    d13 = Dart(ch, edge = e13, origin = v1, face = f134, twin = d31)
    d34 = Dart(ch, edge = e34, origin = v3, face = f134, prev = d13)
    d41 = Dart(ch, edge = e14, origin = v4, face = f134, prev = d34, next = d13)

    d14 = Dart(ch, edge = e14, origin = v1, face = f142, twin = d41)
    d42 = Dart(ch, edge = e24, origin = v4, face = f142, prev = d14)
    d21 = Dart(ch, edge = e12, origin = v2, face = f142, prev = d42, next = d14, twin = d12)

    d24 = Dart(ch, edge = e24, origin = v2, face = f243, twin = d42)
    d43 = Dart(ch, edge = e34, origin = v4, face = f243, prev = d24, twin = d34)
    d32 = Dart(ch, edge = e23, origin = v3, face = f243, prev = d43, next = d24, twin = d23)
    
    return ch

def incrConvexHullOfThreePoints(p1, p2, p3):
    
    ch = DCEL()

    v1 = Vertex(ch, data = p1)
    v2 = Vertex(ch, data = p2)
    v3 = Vertex(ch, data = p3)

    f123 = Face(ch, data = Unit)
    f132 = Face(ch, data = Unit)

    e12 = Edge(ch, data = Unit)
    e23 = Edge(ch, data = Unit)
    e13 = Edge(ch, data = Unit)

    d12 = Dart(ch, edge = e12, origin = v1, face = f123)
    d23 = Dart(ch, edge = e23, origin = v2, face = f123, prev = d12)
    d31 = Dart(ch, edge = e13, origin = v3, face = f123, prev = d23, next = d12)

    d13 = Dart(ch, edge = e13, origin = v1, face = f132, twin = d31)
    d32 = Dart(ch, edge = e23, origin = v3, face = f132, prev = d13, twin = d23)
    d21 = Dart(ch, edge = e12, origin = v2, face = f132, prev = d32, next = d13, twin = d12)

    return ch

### SOME BUILT IN ORIENTATION FUNCTIONS

def orientationPointE3(p1, p2, p3, p4):
    return determinant4(
            p1.x, p1.y, p1.z, 1.0,
            p2.x, p2.y, p2.z, 1.0,
            p3.x, p3.y, p3.z, 1.0,
            p4.x, p4.y, p4.z, 1.0
    )
def orientationPointOP3(p1, p2, p3, p4):
    return determinant4(
            p1.hx, p1.hy, p1.hz, p1.hw,
            p2.hx, p2.hy, p2.hz, p2.hw,
            p3.hx, p3.hy, p3.hz, p3.hw,
            p4.hx, p4.hy, p4.hz, p4.hw
    )

def orientationDiskS2(d1, d2, d3, d4):
        return orientationPointOP3(d1.dualPointOP3, d2.dualPointOP3, d3.dualPointOP3, d4.dualPointOP3)
