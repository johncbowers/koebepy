#
# Classes for working in Minkowski (3, 1)-space
#

import math

from typing import Any
from dataclasses import dataclass
import functools

from .commonOps import *
from enum import Enum

class MinkowskiType(Enum):
    TIMELIKE = -1
    LIGHTLIKE = 0
    SPACELIKE = 1

@dataclass(frozen=True)
class VectorM31:
    
    __slots__ = ['x', 'y', 'z', 't']
    x: Any
    y: Any
    z: Any
    t: Any
    
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z
        yield self.t
        
    @classmethod
    def fromPointE3(cls, p):
        return cls(p.x, p.y, p.z, 1)
    
    def innerProductWith(self: "VectorM31", other: "VectorM31"):
        return self.x * other.x + self.y * other.y + self.z * other.z - self.t * other.t

    def normSq(self):
        return self.innerProductWith(self)

    def type(self):
        n = self.normSq()
        if isZero(n):
            return MinkowskiType.LIGHTLIKE
        elif n < 0:
            return MinkowskiType.TIMELIKE
        else:
            return MinkowskiType.SPACELIKE

    def isSpacelike(self):
        return self.type() == MinkowskiType.SPACELIKE

    def isTimelike(self):
        return self.type() == MinkowskiType.TIMELIKE
    
    def isLightlike(self):
        return self.type() == MinkowskiType.LIGHTLIKE

    def __add__(self: "VectorM31", other: "VectorM31") -> "VectorM31":
        return VectorM31(self.x + other.x, self.y + other.y, self.z + other.z, self.t + self.t)
    
    def __sub__(self, other):
        return VectorM31(self.x - other.x, self.y - other.y, self.z - other.z, self.t - other.t)

    def __mul__(self, a):
        return VectorM31(self.x * a, self.y * a, self.z * a, self.t * a)
    
    def __rmul__(self, a):
        return VectorM31(a * self.x, a * self.y, a * self.z, a * self.t)
    
    def __truediv__(self, a):
        return VectorM31(self.x / a, self.y / a, self.z / a, self.t / a)
    
    def __neg__(self):
        return VectorM31(-self.x, -self.y, -self.z, -self.t)
    
    def dualSpanM31(self):
        return SpanM31(-self.x, -self.y, -self.z, self.t)

    def bisectorWith(self, other):
        
        # First we normalize our vectors with respect to the Minkowski 3,1 inner product:
        minNorm1 = math.sqrt(abs(self.normSq()))
        minNorm2 = math.sqrt(abs(other.normSq()))

        # Now find the coefficients (a, b, c, d) of the plane of equal Minkowski 3,1 inner product from
        # the normalized vectors of this and disk:
        a = other.x * minNorm1 - self.x * minNorm2
        b = other.y * minNorm1 - self.y * minNorm2
        c = other.z * minNorm1 - self.z * minNorm2
        d = self.t * minNorm2 - other.t * minNorm1

        # Return the resulting bisector plane
        return SpanM31(a, b, c, d)

    @classmethod
    def intersectionOf(span1, span2, span3):
        return meet(span1, span2, span3)
    
@dataclass(frozen=True)
class SpanM31:
    
    __slots__ = ['a', 'b', 'c', 'd']
    a: Any
    b: Any
    c: Any
    d: Any
    
    def __iter__(self):
        yield self.a
        yield self.b
        yield self.c
        yield self.d
    
    def dualVectorM31(self):
        return VectorM31(-self.a, -self.b, -self.c, self.d)

    @classmethod
    def spanOf(cls, v1, v2, v3):
        return join(v1, v2, v3)


def join(v1, v2, v3):
    return SpanM31(
                    a = + determinant3(
                            v1.y, v1.z, v1.t,
                            v2.y, v2.z, v2.t,
                            v3.y, v3.z, v3.t),
                    b = - determinant3(
                            v1.x, v1.z, v1.t,
                            v2.x, v2.z, v2.t,
                            v3.x, v3.z, v3.t),
                    c = + determinant3(
                            v1.x, v1.y, v1.t,
                            v2.x, v2.y, v2.t,
                            v3.x, v3.y, v3.t),
                    d = - determinant3(
                            v1.x, v1.y, v1.z,
                            v2.x, v2.y, v2.z,
                            v3.x, v3.y, v3.z)
                   )

def meet(span1, span2, span3):
    return VectorM31(
                    x = + determinant3(
                            span1.b, span1.c, span1.d,
                            span2.b, span2.c, span2.d,
                            span3.b, span3.c, span3.d),
                    y = - determinant3(
                            span1.a, span1.c, span1.d,
                            span2.a, span2.c, span2.d,
                            span3.a, span3.c, span3.d),
                    z = + determinant3(
                            span1.a, span1.b, span1.d,
                            span2.a, span2.b, span2.d,
                            span3.a, span3.b, span3.d),
                    t = - determinant3(
                            span1.a, span1.b, span1.c,
                            span2.a, span2.b, span2.c,
                            span3.a, span3.b, span3.c)
                 )