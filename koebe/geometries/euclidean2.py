#
# Classes for working in Euclidean 2-space
#

import math

from typing import Any, List
from dataclasses import dataclass

from koebe.datastructures.dcel import *
from .commonOps import *

@dataclass(frozen=True)
class PointE2:
    
    __slots__ = ["x", "y"]
    x: Any
    y: Any
    
    def __iter__(self):
        yield self.x
        yield self.y
    
    @classmethod
    def fromPointE2(cls, p):
        return cls(p.x, p.y)
    
    def __sub__(self, other):
        return VectorE2(self.x - other.x,
                        self.y - other.y)
    
    def distSqTo(self, p):
        dx = p.x - self.x
        dy = p.y - self.y
        return dx * dx + dy * dy
    
    def distTo(self, p):
        return math.sqrt(self.distSqTo(p))
    
    def __eq__(self, other):
        if other == None:
            return False
        return self.x == other.x and self.y == other.y
    
    def __ne__(self, other):
        return not self == other
    
    def __add__(self, other: "VectorE2") -> "PointE2":
        return PointE2(self.x + other.x, self.y + other.y)
    
# TODO After SegmentE2 and DiskE2 are implemented, uncomment
#     def distSqToSegmentE2(self, seg):
#         return self.distSqTo(seg.closestPointE2To(self))
#     def distToSegmentE2(self, seg):
#         return math.sqrt(self.distSqToSegmentE2(seg))
#     def distToDiskE2(self, disk):
#         return self.distTo(disk.center) - disk.radius
  
# END PointE2
PointE2.O = PointE2(0.0, 0.0)

@dataclass(frozen=True)
class VectorE2:
    
    __slots__ = ["x", "y"]
    x: Any
    y: Any
    
    def __iter__(self):
        yield self.x
        yield self.y
    
    def __add__(self, other):
        return VectorE2(self.x + other.x, 
                        self.y + other.y)
    
    def __sub__(self, other):
        return VectorE2(self.x - other.x,
                        self.y - other.y)
    
    def __mul__(self, a):
        return VectorE2(self.x * a, self.y * a)
    
    def __rmul__(self, a):
        return VectorE2(self.x * a, self.y * a)
    
    def __truediv__(self, a):
        return VectorE2(self.x / a, self.y / a)
    
    def __neg__(self):
        return VectorE2(-self.x, -self.y)
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __ne__(self, other):
        return not self == other
    
    def dot(self, p):
        return self.x * p.x + self.y * p.y
    
    def normSq(self):
        return self.x * self.x + self.y * self.y
    
    def norm(self):
        return math.sqrt(self.normSq())
    
    def angleFromXAxis(self):
        normInv = 1.0 / self.norm()
        if self.y >= 0:
            return math.acos(self.dot(VectorE2(1.0, 0.0)) * normInv)
        else:
            return 2 * math.pi - math.acos(self.dot(VectorE2(1.0, 0.0)) * normInv)
    
    def toPointE2(self):
        return PointE2(self.x, self.y)
    

# END VectorE2

@dataclass(frozen=True)
class SegmentE2:
    
    __slots__ = ["source", "target"]
    
    source: PointE2
    target: PointE2
    
    def __iter__(self):
        yield tuple(self.source)
        yield tuple(self.target)
    
    @property
    def lengthSq(self):
        return self.target.distSqTo(self.source)
    
    @property
    def length(self):
        return self.target.distTo(self.source)
    
    def pointAlongAt(self, t):
        return ((1.0 - t) * (self.source - PointE2.O) 
                + t * (self.target - PointE2.O)).toPointE2()

    def closestPointE2To(self, p):
        t = max(0.0, min(1.0, (p - self.source).dot(self.target - self.source) / self.lengthSq))
        return self.pointAlongAt(t)
    
    def distTo(self, p):
        return self.closestPointE2To(p).distTo(p)
    
    def distSqTo(self, p):
        return self.closestPointE2To(p).distSqTo(p)
    
    def orientationTo(self, p: PointE2) -> int:
        return determinant3(
            self.source.x, self.source.y, 1,
            self.target.x, self.target.y, 1,
                      p.x,           p.y, 1
        )

# END SegmentE2

@dataclass(frozen=True)
class CircleE2:
    
    __slots__ = ["center", "radius"]
    
    center: PointE2
    radius: Any
    
    def __iter__(self):
        yield tuple(self.center)
        yield self.radius
        
    def inversiveDistTo(self, other: "CircleE2") -> float: 
        dSq = self.center.distSqTo(other.center)
        rSq = self.radius * self.radius
        RSq = other.radius * other.radius
        return (dSq - rSq - RSq) / (2.0 * self.radius * other.radius)
    
    def invertPointE2(self, p: PointE2) -> PointE2:
        v = p - self.center
        return self.center + (self.radius * self.radius * v / (v.normSq()))
        
    def contains(self, p: PointE2) -> bool:
        return self.radius * self.radius >= self.center.distSqTo(p)
    
    def intersects(self, other: "CircleE2") -> bool:
        radSum = self.radius + other.radius
        return self.center.distSqTo(other.center) <= radSum * radSum
    
    @property
    def area(self) -> float:
        return math.pi * self.radius * self.radius
    
    @property
    def perimeter(self):
        return 2.0 * math.pi * self.radius
    
    @property
    def diameter(self):
        return 2.0 * self.radius
    
    
# END CircleE2

@dataclass(frozen=True)
class PolygonE2:
    
    __slots__ = ["vertices"]
    
    vertices: List[PointE2]
    
    def __iter__(self):
        yield vertices
    
    def segments(self):
        return [SegmentE2(self.vertices[i-1], self.vertices[i]) 
                for i in range(len(self.vertices))]

    def signedArea(self):
        return 0.5 * sum([s.source.x * s.target.y - s.target.x * s.source.y
         for s in self.segments()])
    
    def area(self):
        return abs(self.signedArea)
    
    def orientation(self):
        return (
            1 if self.signedArea > 0 
            else -1 if self.signedArea < 0 
            else 0
        )
    
    def ccwOrientation(self) -> "PolygonE2":
        if self.orientation >= 0:
            return self
        else:
            return PolygonE2(self.vertices[::-1])
    
    @property
    def vertexCount(self):
        return len(self.vertices)
    
    def __getitem__(self, idx):
        return self.vertices[idx % self.vertexCount]
    
    def windingNumber(self, p: PointE2) -> int:
        wn = 0
        
        def upwardCrossing(seg):
            return seg.source.y <= p.y and seg.target.y > p.y
        
        def downwardCrossing(seg):
            return seg.target.y <= p.y and seg.source.y > p.y
        
        for seg in self.segments():
            if upwardCrossing(seg) and seg.orientationTo(p) > 0:
                wn += 1
            elif downwardCrossing(seg) and seg.orientationTo(p) < 0:
                wn -= 1
                
        return wn
    
    def contains(self, p: PointE2) -> bool:
        return self.windingNumber(p) != 0
    
    def toDCEL(self) -> DCEL:
        
        poly = self.ccwOrientation()
        
        pDCEL = DCEL()

        pDCEL.outerFace = Face(pDCEL)
        interiorFace = Face(pDCEL)

        verts = [Vertex(pDCEL, data = p) for p in poly.vertices]
        ccwDarts = [Dart(pDCEL, origin = verts[i], face = interiorFace) 
                    for i in range(len(verts))]

        for i in range(len(ccwDarts)):
            ccwDarts[i-1].makeNext(ccwDarts[i])

        dartTwins = [Dart(pDCEL, 
                          origin = ccwDarts[i].next.origin, 
                          face = pDCEL.outerFace) 
                     for i in range(len(ccwDarts))]

        for i in range(len(dartTwins)):
            dartTwins[i].makeNext(dartTwins[i-1])

        edges = [Edge(pDCEL, aDart = ccwDarts[i]) 
                 for i in range(len(ccwDarts))]

        for i in range(len(ccwDarts)):
            ccwDarts[i].makeTwin(dartTwins[i])

            dartTwins[i].edge = edges[i]
            ccwDarts[i].edge  = edges[i]
            edges[i].aDart    = ccwDarts[i]

        return pDCEL
                
# END PolygonE2