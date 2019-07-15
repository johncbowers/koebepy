#
# Classes representing the oriented Projective 2-plane
#
import math

from orientation import Orientation
from commonOps import determinant2, determinant3, inner_product4, isZero
from euclidean3 import VectorE3
from euclidean2 import PointE2
import spherical2
from lazy import lazyproperty

class PointOP2:

    def __init__(self, hx, hy, hw = 1.0):
        self.hx = hx
        self.hy = hy
        self.hw = hw
    
    def distSqTo(self, p):
        dx = p.hx / p.hw - self.hx / self.hw
        dy = p.hy / p.hw - self.hy / self.hw
        return dx * dx + dy * dy
    
    def distTo(self, p):
        return math.sqrt(self.distSqTo(p))
    
    def bisector(self, p):
        v = (VectorE3(self.hx, self.hy, self.hw).normalize() 
             - VectorE3(p.hx, p.hy, p.hw).normalize())
        return LineOP2(v.x, v.y, v.z)
    
    def toPointE2(self):
        fact = 1.0 / self.hw
        return PointE2(self.hx * fact, self.hy * fact)
    
# END PointOP2

class DiskOP2:
    
    def __init__(self, a, b, c, d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
    
    @classmethod
    def fromPointOP2(cls, p1, p2, p3):
        return cls(
            a = + determinant3(
                    p1.hx * p1.hw, p1.hy * p1.hw, p1.hw * p1.hw,
                    p2.hx * p2.hw, p2.hy * p2.hw, p2.hw * p2.hw,
                    p3.hx * p3.hw, p3.hy * p3.hw, p3.hw * p3.hw
            ),
            b = - determinant3(
                    (p1.hx * p1.hx + p1.hy * p1.hy), p1.hy * p1.hw, p1.hw * p1.hw,
                    (p2.hx * p2.hx + p2.hy * p2.hy), p2.hy * p2.hw, p2.hw * p2.hw,
                    (p3.hx * p3.hx + p3.hy * p3.hy), p3.hy * p3.hw, p3.hw * p3.hw
            ),
            c = + determinant3(
                    (p1.hx * p1.hx + p1.hy * p1.hy), p1.hx * p1.hw, p1.hw * p1.hw,
                    (p2.hx * p2.hx + p2.hy * p2.hy), p2.hx * p2.hw, p2.hw * p2.hw,
                    (p3.hx * p3.hx + p3.hy * p3.hy), p3.hx * p3.hw, p3.hw * p3.hw
            ),
            d = - determinant3(
                    (p1.hx * p1.hx + p1.hy * p1.hy), p1.hx * p1.hw, p1.hy * p1.hw,
                    (p2.hx * p2.hx + p2.hy * p2.hy), p2.hx * p2.hw, p2.hy * p2.hw,
                    (p3.hx * p3.hx + p3.hy * p3.hy), p3.hx * p3.hw, p3.hy * p3.hw
            )
        )
   
    @classmethod
    def fromCenterAndRadius(cls:"DiskOP2", center:PointOP2, radius:float) -> "DiskOP2":
        return cls(
            a = center.hw * center.hw,
            b = -2.0 * center.hx * center.hw,
            c = -2.0 * center.hy * center.hw,
            d = center.hx * center.hx + center.hy * center.hy - radius * radius * center.hw * center.hw
        )
    
    # Returns Orientation.ZERO if p is on the boundary of the disk, Orientation.POSITIVE if it is on the positive side, and ORIENTATION.negative o/w
    def orientationOf(self, p:PointOP2) -> Orientation:
        wSq = p.hw * p.hw
        test = inner_product4(
            self.a, self.b, self.c, self.d,
            p.hx*p.hx + p.hy*p.hy, p.hx * wSq, p.hy * wSq, wSq
        )
        return (
            Orientation.ZERO     if isZero(test) else
            Orientation.POSITIVE if test > 0.0 else
            Orientation.NEGATIVE
        )
    
    @property
    def isLine(self):
        return isZero(self.a)
    
    @lazyproperty
    def center(self):
        return PointOP2(-self.b, -self.c, 2.0*self.a)
    
    @lazyproperty
    def radiusSq(self):
        return self.center.x*self.center.x + self.center.y * self.center.y - (self.d/self.a)
    
    @lazyproperty
    def radius(self):
        return math.sqrt(self.radiusSq)
    
    def intersectWithLineOP2(self: "DiskOP2", line: "LineOP2"):
        if not isZero(line.a):
            # x = -(By+C)/A , solve for Y, then X
            alpha = self.a * line.b * line.b + self.a * line.a * line.a
            beta  = 2 * self.a * line.b * line.c - self.b * line.b * line.a + self.c * line.a * line.a
            gamma = self.a * line.c * line.c - self.b * line.a * line.c + self.d * line.a * line.a

            # Test for number of intersection points
            # Case 1: 1 intersection point
            if isZero(beta*beta - 4*alpha*gamma):
                point1Y = -beta/(2*alpha)
                point1X = (-line.b*point1Y-line.c)/line.a
                return [PointOP2(point1X, point1Y)]
            # Case 2: 0 intersection points
            elif beta*beta - 4*alpha*gamma < 0.0:
                return []
            # Case 3: 2 intersection points
            else:
                point1Y = (-beta + math.sqrt(beta*beta - 4*alpha*gamma))/(2 * alpha)
                point2Y = (-beta - math.sqrt(beta*beta - 4*alpha*gamma))/(2 * alpha)

                point1X = (-line.b*point1Y-line.c)/line.a
                point2X = (-line.b*point2Y-line.c)/line.a

                return [PointOP2(point1X, point1Y), PointOP2(point2X, point2Y)]
        else: # if line.b != 0.0
            # y = -(Ax+C)/B, solve for X, then Y
            alpha = self.a * line.b * line.b + self.a * line.a * line.a
            beta  =  2 * self.a * line.a * line.c + line.b * line.b * self.b - self.c * line.a * line.b
            gamma = self.a * line.c * line.c - self.c * line.b * line.c + self.d * line.b * line.b

            # Test for number of intersection points
            # Case 1: 1 intersection point
            if isZero(beta * beta - 4 * alpha * gamma):
                point1X = -beta / (2 * alpha)
                point1Y = (-line.a * point1X - line.c) / line.b
                return [PointOP2(point1X, point1Y)]
            # Case 2: 0 intersection points
            elif beta * beta - 4 * alpha * gamma < 0.0:
                return []
            # Case 3: 2 intersection points
            else:
                point1X = (-beta + math.sqrt(beta*beta - 4*alpha*gamma)) /(2 * alpha)
                point2X = (-beta - math.sqrt(beta*beta - 4*alpha*gamma)) /(2 * alpha)

                point1Y = (-line.a*point1X-line.c)/line.b
                point2Y = (-line.a*point2X-line.c)/line.b

                return [PointOP2(point1X, point1Y), PointOP2(point2X, point2Y)]

    def intersectWithDiskOP2(self: "DiskOP2", disk2: "DiskOP2"):
            
        A = determinant2(self.a, self.b, disk2.a, disk2.b)
        B = determinant2(self.a, self.c, disk2.a, disk2.c)
        C = determinant2(self.a, self.d, disk2.a, disk2.d)

        # if A & B are both = 0 -> 
        # circles are concentric; no points of intersection
        # return an empty list
        if A == 0.0 and B == 0.0:
            return []
        # otherwise, call intersectWith on lineOP2 with 
        # coefficients A,B, and C and return result
        return intersectWith( LineOP2(A, B, C) )
    
    def __funky_innerproduct(self, disk1, disk2):
        return disk1.b*disk2.b + disk1.c*disk2.c - 2*disk2.a*disk1.d - 2*disk1.a*disk2.d
    
    def inversiveDistTo(self, disk):
        ip12 = self.__funky_innerproduct(self, disk)
        ip11 = self.__funky_innerproduct(self, self)
        ip22 = self.__funky_innerproduct(disk, disk)
        return -ip12 / (math.sqrt(ip11) * math.sqrt(ip22))
    
    def invertThrough(self, disk):
        fact = (self.__funky_innerproduct(self, disk) 
                / self.__funky_innerproduct(disk, disk))
        return DiskOP2(
            self.a - 2 * fact * disk.a,
            self.b - 2 * fact * disk.b,
            self.c - 2 * fact * disk.c,
            self.d - 2 * fact * disk.d
        )
    
    def inversiveNormalize(self):
        scale = 1.0 / self.inversiveDistTo(self)
        return DiskOP2(self.a * scale, 
                       self.b * scale, 
                       self.c * scale, 
                       self.d * scale
                      )
    def toDiskS2(self):
        return spherical2.DiskS2(self.a - self.d, 
                      self.c, 
                      self.b, 
                      -(self.a + self.d)
                     )
    
# END DiskOP2

class CircleArcOP2:
    
    def __init__(self, source, target, disk):
        self.source = source
        self.target = target
        self.disk   = disk
    
    @classmethod
    def fromPointOP2(cls, p1, p2, p3):
        return cls(p1, p3, DiskOP2.fromPointOP2(p1, p2, p3))
    
    @property
    def center(self):
        return self.disk.center
    
    @property
    def radius(self):
        return self.disk.radius
    
    def __isBetweenSourceAndTarget(self, p):
        # Signed area of triangle ABC = (1/2)( (B.x - A.x) * (C.y - A.y) - (C.x - A.x) * (B.y - A.y) );
        psx  = p.hx * self.source.hw - self.source.hx * p.hw
        tsy  = self.target.hy * self.source.hw - self.source.hy * self.target.hw
        tsx  = self.target.hx * self.source.hw - self.source.hx * self.target.hw
        psy  = p.hy * self.source.hw - self.source.hy * p.hw
        test = psx * tsy - tsx * psy
        return (0 < test) if (self.disk.a > 0) else (0 > test)
    
    def intersectWithLineOP2(self, aLine):
        return [p for p in self.disk.intersectWithLineOP2(aLine) 
                  if self.__isBetweenSourceAndTarget(p)
               ]
    
    def intersectWithDiskOP2(self, aDisk):
        return [p for p in self.disk.intersectWithDiskOP2(aLine) 
                  if self.__isBetweenSourceAndTarget(p)
               ]
        
    def intersectWithCircleArcOP2(self, anArc):
        return [p for p in self.disk.intersectWithDiskOP2(aLine) 
                  if (self.__isBetweenSourceAndTarget(p) 
                      and anArc.isBetweenSourceAndTarget(p)
                     )
               ]
    
# END CircleArcOP2

class LineOP2:

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c
    
    def intersectWithLineOP2(self, line2): 
        detx =  determinant2(self.b, self.c, line2.b, line2.c)
        dety = -determinant2(self.a, self.c, line2.a, line2.c)
        detw =  determinant2(self.a, self.b, line2.a, line2.b)
        return PointOP2(detx, dety, detw)
    
    def intersectWithDiskOP2(self, disk):
        return disk.intersectWith(self)
    
# END LineOP2

class VectorOP2:
    
    def __init__(self, hx, hy, hw = 1.0):
        self.hx = hx
        self.hy = hy
        self.hw = hw
        
    @classmethod
    def fromVectorOP2(cls, v):
        return cls(v.hx, v.hy, v.hw)
    
    @classmethod
    def fromVectorE2(cls, v):
        return cls(v.x, v.y)
    
    def __eq__(self, v):
        return self is v or (
            are_dependent3(self.hx, self.hy, self.hw, v.hx, v.hy, v.hw)
            and inner_product(self.hx, self.hy, self.hw, v.hx, v.hy, v.hw) > 0
        )
    
    def __ne__(self, v):
        return not self == v
    
    def __add__(self, v):
        return VectorOP2(
            self.hx * v.hw + v.hx * self.hw, 
            self.hy * v.hw + v.hy * self.hw, 
            self.hw * v.hw
        )
    
    def __mul__(self, d):
        return VectorOP2(self.hx * d, self.hy * d, self.hw)
    
    def __rmul__(self, d):
        return self * d
    
    def isIdeal(self):
        return self.hw == 0.0
    
    def toVectorE2(self):
        fact = 1.0 / self.hw
        return VectorE2(self.hx * fact, self.hy * fact)
    
# END VectorOP2