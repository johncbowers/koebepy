#
# Geometry of the Riemann Sphere S2
#

from dataclasses import dataclass
from typing import Any

from .euclidean2 import PointE2
from .euclidean3 import DirectionE3, VectorE3, least_dominant_VectorE3, PointE3
#from . import orientedProjective2 as op2

from .orientedProjective3 import PointOP3, LineOP3, PlaneOP3
from . import extendedComplex as ec
from .commonOps import determinant2, determinant3, inner_product31, isZero, are_dependent4

import math
from enum import Enum

# Representation of a point on the Reimann sphere S2
@dataclass(frozen=True)
class PointS2:
    
    __slots__ = ['x', 'y', 'z']
    
    x: Any
    y: Any
    z: Any
    
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z
    
    @classmethod
    def fromVector(cls, v):
        return cls(v.x, v.y, v.z)
    
    @property
    def antipode(self):
        return PointS2(-x, -y, -z)
    
    @property
    def directionE3(self):
        return DirectionE3(VectorE3(self.x, self.y, self.z))
    
    def __neg__(self):
        return self.antipode
    
    def __eq__(self, other):
        return (self is other 
                or (isinstance(other, PointS2) 
                    and self.directionE3 == other.directionE3
                   )
               )
    
    def toExtendedComplex(self):
        d = self.directionE3
        if d.v.z < 0:
            return ec.ExtendedComplex(complex(d.v.x, d.v.y), complex(1 - d.v.z, 0))
        else: 
            return ec.ExtendedComplex(complex(1 + d.v.z, 0), complex(d.v.x, -d.v.y))
   
    def sgProjectToPointE2(self):
        norm = math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
        fact = 1.0 / (self.z + norm)
        return PointE2(self.x * fact, self.y * fact)
    
    def sgProjectToPointOP2(self):
        import koebe.geometries.orientedProjective2
        norm = math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
        return koebe.geometries.orientedProjective2.PointOP2(self.x, self.y, self.z + norm)
    
    def sgProjectToExtendedComplex(self):
        norm = math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
        if self.x == 0 and self.y == 0 and self.z < 0:
            # Then our point is the south pole, which is infinity in the ExtendedComplex
            return ec.ExtendedComplex.RINFINITY
        else:
            return ec.ExtendedComplex(complex(self.x, self.y), complex(self.z + norm, 0))

    @classmethod
    def sgProjectFromPointE2(cls, p: PointE2) -> "PointS2":
        fact = 1.0 / (1 + p.x * p.x + p.y * p.y)
        return cls(2.0 * p.x * fact, 2.0 * p.y * fact, (1 - (p.x * p.x + p.y * p.y)) * fact)
    
    @classmethod
    def sgProjectFromPointOP2(cls, p: "koebe.geometries.orientedProjective2.PointOP2") -> "PointS2":
        if p.hw == 0:
            # Then the point is at infinity and maps to the south pole
            return cls(0.0, 0.0, -1.0)
        else:
            fact = 1.0 / (p.hx * p.hx + p.hy * p.hy + p.hw * p.hw)
            return cls(2.0 * p.hx * p.hw * fact, 
                       2.0 * p.hy * p.hw * fact, 
                       (p.hw * p.hw - p.hx * p.hx - p.hy * p.hy) * fact)
    
    @classmethod
    def sgProjectFromExtendedComplex(cls, z) -> "PointS2":
        if z.w == ec.ExtendedComplex.ZERO:
            return cls(0.0, 0.0, -1.0)
        
        zwc = z.z * z.w.conjugate()
        zcw = zwc.conjugate()
        zwczcw = (zwc * zcw).real
        R = zwc.real
        I = zwc.imag
        wmsq = z.w.real * z.w.real + z.w.imag * z.w.imag
        wm4 = wmsq * wmsq
        fact = 1.0 / (wm4 + zwczcw)
        
        return cls(2.0 * wmsq * R * fact, 
                   2.0 * wmsq * I * fact, 
                   (wm4 - zwczcw) * fact)
    
# END PointS2
    

# Representation of a disk on the Riemann sphere S2
@dataclass(frozen=True)
class DiskS2:
    
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
        
    @classmethod
    def fromDiskS2(cls, disk):
        return cls(disk.a, disk.b, disk.c, disk.d)
    
    @classmethod
    def throughThreePointS2(cls, p1, p2, p3):
        return cls(
                    a = + determinant3(
                            p1.directionE3.v.y, p1.directionE3.v.z, 1.0,
                            p3.directionE3.v.y, p3.directionE3.v.z, 1.0,
                            p2.directionE3.v.y, p2.directionE3.v.z, 1.0
                    ),
                    b = - determinant3(
                            p1.directionE3.v.x, p1.directionE3.v.z, 1.0,
                            p3.directionE3.v.x, p3.directionE3.v.z, 1.0,
                            p2.directionE3.v.x, p2.directionE3.v.z, 1.0
                    ),
                    c = + determinant3(
                            p1.directionE3.v.x, p1.directionE3.v.y, 1.0,
                            p3.directionE3.v.x, p3.directionE3.v.y, 1.0,
                            p2.directionE3.v.x, p2.directionE3.v.y, 1.0
                    ),
                    d = - determinant3(
                            p1.directionE3.v.x, p1.directionE3.v.y, p1.directionE3.v.z,
                            p3.directionE3.v.x, p3.directionE3.v.y, p3.directionE3.v.z,
                            p2.directionE3.v.x, p2.directionE3.v.y, p2.directionE3.v.z
                    )
                  )
    
    @classmethod
    def withDiameterS2(cls, p1, p2):
        v1 = p1S2.directionE3.v
        v2 = p2S2.directionE3.v
        v  = (v1 + v2) * 0.5
        vn = v.normalize()
        return cls(vn.x, vn.y, vn.z, -v.norm())
    
    @classmethod
    def withCenterAndRadiusS2(cls, center, rho):
        c = center.directionE3.v.normalize()
        return cls(c.x, c.y, c.z, -math.cos(rho))
    
    # Returns the great circle through two points
    @classmethod
    def throughTwoPointS2(cls, p1, p2):
        return cls(
                    a = + determinant2(p1.y, p1.z, p2.y, p2.z),
                    b = - determinant2(p1.x, p1.z, p2.x, p2.z),
                    c = + determinant2(p1.x, p1.y, p2.x, p2.y),
                    d = 0.0
                  )

    
    @property
    def basis1(self):
        return least_dominant_VectorE3(VectorE3(self.a, self.b, self.c)).value.cross(VectorE3(self.a, self.b, self.c))
    
    @property 
    def basis2(self):
        return self.basis1.cross(VectorE3(self.a, self.b, self.c))
    
    @property
    def basis3(self):
        return VectorE3(self.a, self.b, self.c)
    
    @property
    def normedBasis1(self):
        return DirectionE3(self.basis1)
    
    @property
    def normedBasis2(self):
        return DirectionE3(self.basis2)
    
    @property
    def normedBasis3(self):
        return DirectionE3(self.basis3)
    
    @property
    def directionE3(self):
        return DirectionE3(VectorE3(self.a, self.b, self.c))
    
    @property
    def dualPlaneOP3(self):
        return PlaneOP3(self.a, self.b, self.c, self.d)
    
    @property
    def dualPointOP3(self):
        return PointOP3(-self.a, -self.b, -self.c, self.d)
    
    @property
    def dualCPlaneS2(self):
        return CPlaneS2(-self.a, -self.b, -self.c, self.d)
    
    @property
    def centerE3(self):
        return PointOP3(-self.a * self.d, -self.b * self.d, -self.c * self.d, self.a * self.a + self.b * self.b + self.c * self.c).toPointE3()
    
    @property
    def radiusE3(self):
        return math.sqrt(1.0 - (self.centerE3 - PointE3.O).normSq())
    
    @property
    def radiusS2(self):
        return math.asin(self.radiusE3)
    
    # TODO Can we get rid of the norm here? 
    def contains(self, p):
        return isZero(inner_product(p.x, p.y, p.z, VectorE3(p.x, p.y, p.z).norm(), a, b, c, d))
    
    def __eq__(self, other):
        return (self is other
                or (isinstance(other, DiskS2)
                   and are_dependent4(self.a, other.a, 
                                     self.b, other.b, 
                                     self.c, other.c, 
                                     self.d, other.d
                                    )
                  )
               )
    
    def lorentzTo(self, diskS2):
        return inner_product31(self.a, self.b, self.c, self.d,
                               diskS2.a, diskS2.b, diskS2.c, diskS2.d)

    def inversiveDistTo(self, diskS2):
        ip12 = inner_product31(self.a, self.b, self.c, self.d,
                               diskS2.a, diskS2.b, diskS2.c, diskS2.d)
        ip11 = inner_product31(self.a, self.b, self.c, self.d,
                               self.a, self.b, self.c, self.d)
        ip22 = inner_product31(diskS2.a, diskS2.b, diskS2.c, diskS2.d,
                               diskS2.a, diskS2.b, diskS2.c, diskS2.d)
        return -ip12 / (math.sqrt(ip11) * math.sqrt(ip22))
    
    def bisectorWith(self, diskS2):
        
        # First we normalize our vectors with respect to the Minkowski 3,1 inner product:
        minNorm1 = math.sqrt(inner_product31(self.a, self.b, self.c, self.d, self.a, self.b, self.c, self.d))
        minNorm2 = math.sqrt(inner_product31(diskS2.a, diskS2.b, diskS2.c, diskS2.d, diskS2.a, diskS2.b, diskS2.c, diskS2.d))

        # Now find the coefficients (a, b, c, d) of the plane of equal Minkowski 3,1 inner product from
        # the normalized vectors of this and disk:
        a = diskS2.a / minNorm2 - self.a / minNorm1
        b = diskS2.b / minNorm2 - self.b / minNorm1
        c = diskS2.c / minNorm2 - self.c / minNorm1
        d = self.d / minNorm1 - diskS2.d / minNorm2

        # Return the resulting bisector plane
        return CPlaneS2(a, b, c, d)
    
    def get3PointsOnDisk(self):
        # translate basis vectors to center of the disk and scale by radius
        newBasis1 = self.normedBasis1.v * self.radiusE3 + self.centerE3.toVectorE3()
        newBasis2 = self.normedBasis2.v * self.radiusE3 + self.centerE3.toVectorE3()
        newBasis3 = - self.normedBasis1.v * self.radiusE3 + self.centerE3.toVectorE3()
        newBasis4 = - self.normedBasis2.v * self.radiusE3 + self.centerE3.toVectorE3()

        negZ = VectorE3(0.0, 0.0, -1.0)
        isNegZ1 = isZero(1.0 - newBasis1.dot(negZ) / newBasis1.norm())
        isNegZ2 = isZero(1.0 - newBasis2.dot(negZ) / newBasis2.norm())
        isNegZ3 = isZero(1.0 - newBasis3.dot(negZ) / newBasis3.norm())
        isNegZ4 = isZero(1.0 - newBasis4.dot(negZ) / newBasis4.norm())

        if (not (isNegZ1 or isNegZ2 or isNegZ3)):
            return [PointS2(*newBasis1), PointS2(*newBasis2), PointS2(*newBasis3)]
        elif (not (isNegZ2 or isNegZ3 or isNegZ4)):
            return [PointS2(*newBasis2), PointS2(*newBasis3), PointS2(*newBasis4)]
        elif (not (isNegZ3 or isNegZ4 or isNegZ1)):
            return [PointS2(*newBasis3), PointS2(*newBasis4), PointS2(*newBasis1)]
        else:
            return [PointS2(*newBasis4), PointS2(*newBasis1), PointS2(*newBasis2)]
        
    def invertThrough(self, diskS2):
        fact = (inner_product31(self.a, self.b, self.c, self.d, diskS2.a, diskS2.b, diskS2.c, diskS2.d) /
                inner_product31(diskS2.a, diskS2.b, diskS2.c, diskS2.d, diskS2.a, diskS2.b, diskS2.c, diskS2.d)
               )

        return DiskS2(
                self.a - 2 * fact * diskS2.a,
                self.b - 2 * fact * diskS2.b,
                self.c - 2 * fact * diskS2.c,
                self.d - 2 * fact * diskS2.d
        )
    
    def sgProjectToOP2(self):
        import koebe.geometries.orientedProjective2
        return koebe.geometries.orientedProjective2.DiskOP2.fromPointOP2(*[p.sgProjectToPointOP2() for p in self.get3PointsOnDisk()])
    
    def inversiveNormalize(self):
        scale = 1.0 / math.sqrt(self.lorentzTo(self))
        return DiskS2(self.a * scale, self.b * scale, self.c * scale, self.d * scale)
    
    # def normalize(self):
    #     scale = 1.0 / math.sqrt(inner_product31(self.a, self.b, self.c, self.d, self.a, self.b, self.c, self.d))
    #     return DiskS2(self.a * scale, self.b * scale, self.c * scale, self.d * scale)
    
    def toDiskOP2(self): 
        import koebe.geometries.orientedProjective2
        return koebe.geometries.orientedProjective2.DiskOP2(0.5 * (self.a - self.d), self.c, self.b, -(self.a + self.d) * 0.5)
    
    def __mul__(self, a):
        return DiskS2(a*self.a, a*self.b, a*self.c, a*self.d)
    
    def __rmul__(self, a):
        return DiskS2(a*self.a, a*self.b, a*self.c, a*self.d)
    
    def __add__(self, other: "DiskS2") -> "DiskS2":
        return DiskS2(self.a + other.a, self.b + other.b, self.c + other.c, self.d + other.d)
    
# END DiskS2

class CoaxialFamilyS2Type(Enum):
    PARABOLIC = 0
    ELLIPTIC = 1
    HYPERBOLIC = 2

@dataclass(frozen=True)
class CoaxialFamilyS2:
    __slots__ = ['source', 'target']
    
    source: Any
    target: Any
    
    def __iter__(self):
        yield self.source
        yield self.target
    
    def type(self):
        isectCount = len(LineOP3.fromPlaneOP3(self.source.dualPlaneOP3, self.target.dualPlaneOP3).getIntersectionWithUnit2Sphere())
        if isectCount == 0:
            return CoaxialFamilyS2Type.HYPERBOLIC
        elif isectCount == 1:
            return CoaxialFamilyS2Type.PARABOLIC
        else:
            return CoaxialFamilyS2Type.ELLIPTIC
    
    def isHyperbolic(self):
        return self.type() == CoaxialFamilyS2Type.HYPERBOLIC
    
    def isParabolic(self):
        return self.type() == CoaxialFamilyS2Type.PARABOLIC
    
    def isElliptic(self):
        return self.type() == CoaxialFamilyS2Type.ELLIPTIC
    
    def dualLineOP3(self):
        return LineOP3(
                determinant2(self.source.a, self.source.b, self.target.a, self.target.b), # p01
                determinant2(self.source.a, self.source.c, self.target.a, self.target.c), # p02
                determinant2(self.source.a, self.source.d, self.target.a, self.target.d), # p03
                determinant2(self.source.b, self.source.c, self.target.b, self.target.c), # p12
                determinant2(self.source.b, self.source.d, self.target.b, self.target.d), # p13
                determinant2(self.source.c, self.source.d, self.target.c, self.target.d)  # p23
        )
    def generatorPoints(self):
        line = (LineOP3.fromPlaneOP3(self.source.dualPlaneOP3, self.target.dualPlaneOP3)
                if   self.isElliptic()
                else LineOP3.fromPointOP3(self.source.dualPointOP3, self.target.dualPointOP3)
                )
        return [PointS2.fromVector(p.toVectorE3()) for p in line.getIntersectionWithUnit2Sphere()]
                
    def diskThroughPointS2(self, pt):
        a1 = self.source.a
        b1 = self.source.b
        c1 = self.source.c
        d1 = self.source.d

        a2 = self.target.a
        b2 = self.target.b
        c2 = self.target.c
        d2 = self.target.d

        x = pt.directionE3.v.x
        y = pt.directionE3.v.y
        z = pt.directionE3.v.z

        return DiskS2(
                a2 * (d1 + b1 * y + c1 * z) - a1 * (d2 + b2 * y + c2 * z),
                b2 * (d1 + a1 * x + c1 * z) - b1 * (d2 + a2 * x + c2 * z),
                c2 * (d1 + a1 * x + b1 * y) - c1 * (d2 + a2 * x + b2 * y),
                -a2 * d1 * x + d2 * (a1 * x + b1 * y + c1 * z) - d1 * (b2 * y + c2 * z)
        )

# END CoaxialFamilyS2

# The three types of c-planes
class CPlaneS2Type(Enum):
    PARABOLIC = 0
    ELLIPTIC = 1
    HYPERBOLIC = 2

# END CPlaneS2Type

# Representation of a c-plane (aka bundle of circles) on the Riemann sphere S2
@dataclass(frozen=True)
class CPlaneS2:
    
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
        
    @classmethod
    def throughThreeDiskS2(cls, disk1, disk2, disk3):
        return join(disk1, disk2, disk3)
    
    @property
    def dualDiskS2(self):
        return DiskS2(-self.a, -self.b, -self.c, self.d)
    
    @property
    def type(self):
        dSq = self.d * self.d
        dot_abc = self.a * self.a + self.b * self.b + self.c * self.c
        scale = dSq / dot_abc
        aSc = self.a * scale
        bSc = self.b * scale
        cSc = self.c * scale
        val = aSc * aSc + bSc * bSc + cSc * cSc
        return (CPlaneS2Type.PARABOLIC if val == 1.0 
                else CPlaneS2Type.HYPERBOLIC if 0 <= val and val <= 1.0
                else CPlaneS2Type.ELLIPTIC
               )
    
    @property
    def isHyperbolic(self):
        return self.type == CPlaneS2Type.HYPERBOLIC
    
    @property
    def isParabolic(self):
        return self.type == CPlaneS2Type.PARABOLIC
    
    @property
    def isElliptic(self):
        return self.type == CPlaneS2Type.ELLIPTIC
    
# END CPlaneS2


@dataclass(frozen=True)
class CircleArcS2:
    
    __slots__ = ['source', 'target', 'disk']
    
    source: Any
    target: Any
    disk: Any
        
    def __iter__(self):
        yield self.source
        yield self.target
        yield self.disk
    
    @property
    def basis1(self):
        return self.disk.basis1
    
    @property
    def basis2(self):
        return self.disk.basis2
    
    @property
    def basis3(self):
        return self.disk.basis3
    
    @property
    def normedBasis1(self):
        return self.disk.normedBasis1
    
    @property
    def normedBasis2(self):
        return self.disk.normedBasis2
    
    @property
    def normedBasis3(self):
        return self.disk.normedBasis3
    
    @property 
    def centerE3(self):
        return self.disk.centerE3
    
    @property
    def radiusE3(self):
        return self.disk.radiusE3
    
    def sgToCircleArcOP2(self):
        import koebe.geometries.orientedProjective2
        # Project the PointE3s to PointOP2s
        pointsOP2 = [p.sgProjectToPointOP2() 
                     for p in self.disk.get3PointsOnDisk()]
        
        # Return the CircleArcOP2 through with the source and target PointOP2s and DiskOP2
        return koebe.geometries.orientedProjective2.CircleArcOP2(
                self.source.sgProjectToPointOP2(), 
                self.target.sgProjectToPointOP2(), 
                koebe.geometries.orientedProjective2.DiskOP2.fromPointOP2(*pointsOP2)
        )
    
    def toDiskOP2(self):
        import koebe.geometries.orientedProjective2
        return koebe.geometries.orientedProjective2.DiskOP2(
                        0.5 * (self.a - self.d), 
                        self.c, 
                        self.b, 
                        0.5 * (self.d - self.a)
                     )

    
# END CircleArcS2
    

def join(disk1, disk2, disk3):
    return CPlaneS2(
                    a = + determinant3(
                            disk1.b, disk1.c, disk1.d,
                            disk2.b, disk2.c, disk2.d,
                            disk3.b, disk3.c, disk3.d),
                    b = - determinant3(
                            disk1.a, disk1.c, disk1.d,
                            disk2.a, disk2.c, disk2.d,
                            disk3.a, disk3.c, disk3.d),
                    c = + determinant3(
                            disk1.a, disk1.b, disk1.d,
                            disk2.a, disk2.b, disk2.d,
                            disk3.a, disk3.b, disk3.d),
                    d = - determinant3(
                            disk1.a, disk1.b, disk1.c,
                            disk2.a, disk2.b, disk2.c,
                            disk3.a, disk3.b, disk3.c)
                   )

def meet(plane1, plane2, plane3):
    return DiskS2(
                    a = + determinant3(
                            plane1.b, plane1.c, plane1.d,
                            plane2.b, plane2.c, plane2.d,
                            plane3.b, plane3.c, plane3.d),
                    b = - determinant3(
                            plane1.a, plane1.c, plane1.d,
                            plane2.a, plane2.c, plane2.d,
                            plane3.a, plane3.c, plane3.d),
                    c = + determinant3(
                            plane1.a, plane1.b, plane1.d,
                            plane2.a, plane2.b, plane2.d,
                            plane3.a, plane3.b, plane3.d),
                    d = - determinant3(
                            plane1.a, plane1.b, plane1.c,
                            plane2.a, plane2.b, plane2.c,
                            plane3.a, plane3.b, plane3.c)
                 )
        