#
# Classes for working in Minkowski (3, 1)-space
#

import math

from typing import Any
from dataclasses import dataclass
import functools

from koebe.geometries.euclidean2 import PointE2
from koebe.geometries.euclidean3 import PointE3
from koebe.geometries.orientedProjective2 import LineOP2, PointOP2

from .commonOps import *
from enum import Enum

class MinkowskiType(Enum):
    TIMELIKE = -1
    LIGHTLIKE = 0
    SPACELIKE = 1

@dataclass(frozen=True)
class VectorM21:
    
    __slots__ = ['x', 'y', 't']
    x: Any
    y: Any
    t: Any
    
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.t
        
    @classmethod
    def fromPointE2(cls, p):
        return cls(p.x, p.y, 1)
    
    @classmethod
    def fromPointOP2(cls, p):
        return cls(p.hx, p.hy, p.hw)
    
    def toPointE2(self):
        return PointE2(self.x / self.t, self.y / self.t)
    
    def toPointE3(self):
        return PointE3(self.x, self.y, self.t)
    
    def projectToLevelE3(self, level):
        return PointE3(level * self.x / self.t, level * self.y / self.t, level)
    
    def toPointOP2(self):
        return PointOP2(self.x, self.y, self.t)

    def innerProductWith(self: "VectorM21", other: "VectorM21"):
        return self.x * other.x + self.y * other.y - self.t * other.t

    def normSq(self):
        return self.innerProductWith(self)
    
    def normalize(self):
        if self.isLightlike():
            return self
        else: 
            fact = 1 / math.sqrt(abs(self.normSq()))
            return fact * self

    def hyperbolicDistanceTo(self, other):
        return math.acosh(-self.normalize().innerProductWith(other.normalize()))

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

    def __add__(self: "VectorM21", other: "VectorM21") -> "VectorM21":
        return VectorM21(self.x + other.x, self.y + other.y, self.t + other.t)
    
    def __sub__(self, other):
        return VectorM21(self.x - other.x, self.y - other.y, self.t - other.t)

    def __mul__(self, a):
        return VectorM21(self.x * a, self.y * a, self.t * a)
    
    def __rmul__(self, a):
        return VectorM21(a * self.x, a * self.y, a * self.t)
    
    def __truediv__(self, a):
        return VectorM21(self.x / a, self.y / a, self.t / a)
    
    def __neg__(self):
        return VectorM21(-self.x, -self.y, -self.t)
    
    def dualSpanM21(self):
        return SpanM21(-self.x, -self.y, self.t)

    def bisectorWith(self, other):
        
        # First we normalize our vectors with respect to the Minkowski 3,1 inner product:
        minNorm1 = math.sqrt(abs(self.normSq()))
        minNorm2 = math.sqrt(abs(other.normSq()))

        # Now find the coefficients (a, b, c, d) of the plane of equal Minkowski 3,1 inner product from
        # the normalized vectors of this and disk:
        a = other.x * minNorm1 - self.x * minNorm2
        b = other.y * minNorm1 - self.y * minNorm2
        c = self.t * minNorm2 - other.t * minNorm1

        # Return the resulting bisector plane
        return SpanM21(a, b, c)

    @classmethod
    def intersectionOf(span1, span2):
        return meet(span1, span2)
    
    def invertThrough(self, spanM21):
        n = inner_product21(self.x, self.y, self.t, -spanM21.a, -spanM21.b, spanM21.c)
        d = inner_product21(spanM21.a, spanM21.b, spanM21.c, spanM21.a, spanM21.b, spanM21.c)
        if d == 0:
            return VectorM21(
                    (d * self.x + 2 * n * spanM21.a),
                    (d * self.y + 2 * n * spanM21.b),
                    (d * self.t - 2 * n * spanM21.c)
            )
        else:
            fact = n / d
            return VectorM21(
                    self.x + 2 * fact * spanM21.a,
                    self.y + 2 * fact * spanM21.b,
                    self.t - 2 * fact * spanM21.c
            )
    
@dataclass(frozen=True)
class SpanM21:
    
    __slots__ = ['a', 'b', 'c']
    a: Any
    b: Any
    c: Any
    
    def __iter__(self):
        yield self.a
        yield self.b
        yield self.c
    
    def dualVectorM21(self):
        return VectorM21(-self.a, -self.b, self.c)

    @classmethod
    def spanOf(cls, v1, v2):
        return join(v1, v2)
    
    def intersectWithOP2(self):
        """
        Returns the intersection of this span with the t=1 subspace as a LineOP2 object.
        """
        return LineOP2(self.a, self.b, self.c)

def join(v1, v2):
    return SpanM21(
                    a = + determinant2(
                            v1.b, v1.c, 
                            v2.b, v2.c),
                    b = - determinant2(
                            v1.a, v1.c,
                            v2.a, v2.c),
                    c = + determinant2(
                            v1.a, v1.b,
                            v2.a, v2.b)
                   )

def meet(span1, span2):
    return VectorM21(
                    x = + determinant2(
                            span1.b, span1.c,
                            span2.b, span2.c),
                    y = - determinant2(
                            span1.a, span1.c,
                            span2.a, span2.c),
                    t = + determinant2(
                            span1.a, span1.b,
                            span2.a, span2.b),
                 )