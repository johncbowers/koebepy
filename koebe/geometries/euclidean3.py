#
# Classes for working in Euclidean 3-space
#

import math

from typing import Any
from dataclasses import dataclass

from .commonOps import *
from .orientedProjective3 import PointOP3
from enum import Enum

@dataclass(frozen=True)
class PointE3:
    
    __slots__ = ['x', 'y', 'z']
    x: Any
    y: Any
    z: Any
    
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z
        
    @classmethod
    def fromPointE3(cls, p):
        return cls(p.x, p.y, p.z)
    
    def __add__(self: "PointE3", other: "VectorE3") -> "PointE3":
        return PointE3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self: "PointE3", other: "PointE3") -> "VectorE3":
        return VectorE3(self.x - other.x, self.y - other.y, self.z - other.z)
    
   
    def __mul__(self, a):
        return PointE3(self.x * a, self.y * a, self.z * a)
    
    def __rmul__(self, a):
        return PointE3(a * self.x, a * self.y, a * self.z)
    
    def distSqTo(self, p):
        dx = p.x - self.x
        dy = p.y - self.y
        dz = p.z - self.z
        return dx * dx + dy * dy + dz * dz
    
    def distTo(self, p):
        return math.sqrt(self.distSqTo(p))
    
    def toVectorE3(self):
        return self - PointE3.O
    
    # def __eq__(self, other):
    #     return not other == None and (self is other or (self.x == other.x 
    #                              and self.y == other.y 
    #                              and self.z == other.z))
    
    def __ne__(self, other):
        return not self == other
    
    def __str__(self):
        return f"PointE3({self.x}, {self.y}, {self.z})"
    
# END PointE3

@dataclass(frozen=True)
class SegmentE3:
    
    __slots__ = ["source", "target"]
    
    source: PointE3
    target: PointE3
    
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
        return ((1.0 - t) * self.source.toVectorE3() + t * self.target.toVectorE3()).toPointE3()

    def closestPointE3To(self, p):
        t = max(0.0, min(1.0, (p - self.source).dot(self.target - self.source) / self.lengthSq))
        return self.pointAlongAt(t)
    
# END SegmentE3

@dataclass(frozen=True)
class VectorE3:
    
    __slots__ = ['x', 'y', 'z']
    x: Any
    y: Any
    z: Any
        
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z
        
    @classmethod
    def fromVectorE3(cls, v):
        return cls(v.x, v.y, v.z)
    
    def __add__(self: "VectorE3", other: "VectorE3") -> "VectorE3":
        return VectorE3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return VectorE3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, a):
        return VectorE3(self.x * a, self.y * a, self.z * a)
    
    def __rmul__(self, a):
        return VectorE3(a * self.x, a * self.y, a * self.z)
    
    def __truediv__(self, a):
        return VectorE3(self.x / a, self.y / a, self.z / a)
    
    def __neg__(self):
        return VectorE3(-self.x, -self.y, -self.z)
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def normSq(self):
        return self.x * self.x + self.y * self.y + self.z * self.z
    
    def norm(self):
        return math.sqrt(self.normSq())
    
    def normalize(self):
        invNorm = 1.0 / self.norm()
        return invNorm * self
    
    def cross(self, v):
        return VectorE3(
             determinant2(self.y, v.y, self.z, v.z), 
            -determinant2(self.x, v.x, self.z, v.z),
             determinant2(self.x, v.x, self.y, v.y)
        )
    
    def toPointE3(self):
        return PointE3(self.x, self.y, self.z)
    
    # def __eq__(self, other):
    #     return not other == None and type(self) == type(other) and (self is other or (self.x == other.x 
    #                              and self.y == other.y 
    #                              and self.z == other.z))
    
    def __ne__(self, other):
        return not self == other
    
    def __str__(self):
        return f"VectorE3({self.x}, {self.y}, {self.z})"
    
@dataclass(frozen=True)
class DirectionE3:
    
    __slots__ = ["vec"]
    vec: VectorE3
        
    def __iter__(self):
        _v = self.v
        yield _v.x
        yield _v.y
        yield _v.z
    
    @classmethod
    def fromDirectionE3(cls,d):
        return cls(d.vec)
    
    @property
    def v(self):
        norm = self.vec.norm()
        if norm == 0: 
            return VectorE3(0,0,0)
        else:
            invd     = 1.0 / norm
            return VectorE3(self.vec.x * invd, 
                            self.vec.y * invd, 
                            self.vec.z * invd)
    @property
    def endPoint(self):
        return PointE3(self.v.x, self.v.y, self.v.z)
    
    def __add__(self, other):
        return DirectionE3(self.v + other.v)
    
    def __sub__(self, other):
        return DirectionE3(self.v - other.v)
    
    def __neg__(self):
        return DirectionE3(-self.vec)
    
    def dot(self, other):
        return self.v.dot(other.v)
    
    def cross(self, other):
        return DirectionE3(self.v.cross(other.v))
    
    def __eq__(self, other):
        return not other == None and type(self) == type(other) (self is other or self.v == other.v)
    
    def __ne__(self, other):
        return not self == other
    
    def __str__(self):
        return f"DirectionE3({self.v.x}, {self.v.y}, {self.v.z})"

# END DirectionE3

@dataclass(frozen=True)
class PlaneE3:
    
    __slots__ = ["N", "d"]
    N: VectorE3
    d: Any
        
    def __iter__(self):
        yield tuple(self.N)
        yield self.d
    
    @classmethod
    def fromPlaneE3(cls, p):
        return cls(VectorE3(p.N), p.d)
    
    @classmethod
    def fromThreePointE3(cls, p1, p2, p3):
        return cls((p2 - p1).cross(p3 - p1), 
                       (PointE3.O - p1).dot((p2 - p1).cross(p3 - p1)))

    def pointE3ClosestOrigin(self):
        fact = self.d / self.N.normSq()
        return PointE3(-self.N.x * fact, 
                       -self.N.y * fact, 
                       -self.N.z * fact)
    
    def pointOP3ClosestOrigin(self):
        nsq = self.N.normSq()
        return PointOP3(-self.N.x * nsq, 
                        -self.N.y * nsq,
                        -self.N.z * nsq,
                        self.d)
    
    def __eq__(self, other):
        return not other == None and (self is other or 
                                         are_dependent4(self.N.x,  
                                                        self.N.y,  
                                                        self.N.z,  
                                                        self.d,
                                                        other.N.x,
                                                        other.N.y, 
                                                        other.N.z, 
                                                        other.d)
                                     )
    
    def __ne__(self, other):
        return not self == other
    
    def __str__(self):
        return f"PlaneE3(N={self.N}, d={self.d})"
# END PlaneE3

class DominantE3(Enum):
    E3_POSX = VectorE3(1.0, 0.0, 0.0)
    E3_NEGX = VectorE3(-1.0, 0.0, 0.0)
    E3_POSY = VectorE3(0.0, 1.0, 0.0)
    E3_NEGY = VectorE3(0.0, -1.0, 0.0)
    E3_POSZ = VectorE3(0.0, 0.0, 1.0)
    E3_NEGZ = VectorE3(0.0, 0.0, -1.0)

def dominant(dx, dy, dz):
    dxabs = dx if (dx >= 0.0) else -dx
    dyabs = dy if (dy >= 0.0) else -dy
    dzabs = dz if (dz >= 0.0) else -dz

    if (dxabs >= dyabs and dxabs >= dzabs):
        return DominantE3.E3_POSX if (dx > 0.0) else DominantE3.E3_NEGX
    elif(dyabs >= dzabs):
        return DominantE3.E3_POSY if (dy > 0.0) else DominantE3.E3_NEGY
    else:
        return DominantE3.E3_POSZ if (dz > 0.0) else DominantE3.E3_NEGZ

def least_dominant(dx, dy, dz):
    dxabs = dx if (dx >= 0.0) else -dx
    dyabs = dy if (dy >= 0.0) else -dy
    dzabs = dz if (dz >= 0.0) else -dz

    if (dxabs <= dyabs and dxabs <= dzabs):
        return DominantE3.E3_POSX if (dx >= 0.0) else DominantE3.E3_NEGX
    elif (dyabs <= dzabs):
        return DominantE3.E3_POSY if (dy >= 0.0) else DominantE3.E3_NEGY
    else:
        return DominantE3.E3_POSZ if (dz >= 0.0) else DominantE3.E3_NEGZ
    
def least_dominant_VectorE3(v):
    return least_dominant(v.x, v.y, v.z)

# Class Objects
PointE3.O      = PointE3(0.0, 0.0, 0.0)

VectorE3.e1    = VectorE3(1.0, 0.0, 0.0)
VectorE3.e2    = VectorE3(0.0, 1.0, 0.0)
VectorE3.e3    = VectorE3(0.0, 0.0, 1.0)

DirectionE3.e1 = DirectionE3(VectorE3.e1)    
DirectionE3.e2 = DirectionE3(VectorE3.e2)    
DirectionE3.e3 = DirectionE3(VectorE3.e3)