#
# Geometry of the Riemann Sphere S2
#

from dataclasses import dataclass

from .euclidean2 import PointE2
from .euclidean3 import DirectionE3, VectorE3, least_dominant_VectorE3, PointE3
from .orientedProjective2 import PointOP2
from .orientedProjective3 import PointOP3, PlaneOP3
from .extendedComplex import ExtendedComplex
from .commonOps import determinant2, determinant3, inner_product31
import math
from enum import Enum

# Representation of a point on the Reimann sphere S2
@dataclass(frozen=True)
class PointS2:
    
    __slots__ = ['x', 'y', 'z']
    
    x: float
    y: float
    z: float
    
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
            return ExtendedComplex(d.v.x + d.v.y * 1j, 1 - d.v.z + 0j)
        else: 
            return ExtendedComplex(1 + d.v.z + 0j, d.v.x - d.v.y * 1j)
   
    def sgProjectToPointE2(self):
        invNorm = 1.0 / Math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
        X = x * invNorm
        Y = y * invNorm
        Z = z * invNorm
        return PointE2(X / (Z + 1), Y / (Z + 1))
    
    def sgProjectToPointOP2(self):
        invNorm = 1.0 / Math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
        X = x * invNorm
        Y = y * invNorm
        Z = z * invNorm
        return PointOP2(2.0 * X, 2.0 * Y, Z + 1.0)

# END PointS2
    

# Representation of a disk on the Riemann sphere S2
@dataclass(frozen=True)
class DiskS2:
    
    __slots__ = ['a', 'b', 'c', 'd']
    
    a: float
    b: float
    c: float
    d: float
    
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
        return (this is other
                or (isinstance(other, DiskS2)
                   and are_dependent(self.a, other.a, 
                                     self.b, other.b, 
                                     self.c, other.c, 
                                     self.d, other.d
                                    )
                  )
               )
    
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
            return [PointS2(newBasis1), PointS2(newBasis2), PointS2(newBasis3)]
        elif (not (isNegZ2 or isNegZ3 or isNegZ4)):
            return [PointS2(newBasis2), PointS2(newBasis3), PointS2(newBasis4)]
        elif (not (isNegZ3 or isNegZ4 or isNegZ1)):
            return [PointS2(newBasis3), PointS2(newBasis4), PointS2(newBasis1)]
        else:
            return [PointS2(newBasis4), PointS2(newBasis1), PointS2(newBasis2)]
        
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
        return DiskOP2(*[p.sgProjectToPointOP2() for p in self.get3PointsOnDisk()])
    
    def inversiveNormalize(self):
        scale = 1.0 / self.inversiveDistTo(self)
        return DiskS2(self.a * scale, self.b * scale, self.c * scale, self.d * scale)
    
    def normalize(self):
        scale = 1.0 / math.sqrt(inner_product(self.a, self.b, self.c, self.d, self.a, self.b, self.c, self.d))
        return DiskS2(self.a * scale, self.b * scale, self.c * scale, self.d * scale)
    
    def toDiskOP2(self): 
        return DiskOP2(0.5 * (self.a - self.d), self.c, self.b, -(self.a + self.d) * 0.5)
# END DiskS2

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
    
    a: float
    b: float
    c: float
    d: float
    
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
        