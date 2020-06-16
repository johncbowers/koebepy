#
# Geometry of the Hyperbolic Plane
#

from dataclasses import dataclass
from .euclidean2 import PointE2, CircleE2
from .extendedComplex import ExtendedComplex
from . import orientedProjective2

from typing import Any
import math

@dataclass(frozen=True)
class PointH2:

    __slots__ = ['coord']
    
    coord: ExtendedComplex
        
    def __init__(self, coord: ExtendedComplex):
        if isinstance(coord, complex):
            object.__setattr__(self, 'coord', ExtendedComplex(coord))
        elif isinstance(coord, ExtendedComplex):
            object.__setattr__(self, 'coord', coord)
#     def toPoincarePointE2(self) -> PointE2:
#         """Computes euclidean point representing this point in the 
#         poincare disk model of the hyperbolic plane. 
        
#         Returns:
#             A euclidean point in the unit disk representing this point.
#         """
#         if self.coord.w == 0: # then this point is infinite
#             z = self.coord.z / abs(self.coord.z)
#         else:
#             z = self.coord.toComplex()


    @classmethod
    def fromComplex(cls, z:complex) -> "PointH2":
        return cls(coord = ExtendedComplex.fromComplex(z))

    @property
    def isInfinite(self) -> bool:
        return self.coord.w == 0
    
    def __abs__(self):
        return self.coord.__abs__()
    
    def toPointE2(self):
        return orientedProjective2.PointOP2(self.coord.real, self.coord.imag).toPointE2()

# END PointH2

PointH2.O = PointH2(ExtendedComplex.ZERO)

@dataclass(frozen=True)
class LineH2:
    
    __slots__ = ['source', 'target']
    
    source: PointH2
    target: PointH2
    
    def __iter__(self):
        yield self.source
        yield self.target
        
    def toPoincareCircleArcOP2(self):
        z = self.source.coord
        w = self.target.coord
        
        unitDisk = orientedProjective2.DiskOP2(1,0,0,-1)
        p1, p2 = (
            orientedProjective2.PointOP2(z.real, z.imag), 
            orientedProjective2.PointOP2(w.real, w.imag)
        )
        disk = orientedProjective2.DiskOP2.orthogonalToDiskAndThroughPoints(
            unitDisk, p1, p2
        )
        sols = unitDisk.intersectWithDiskOP2(disk)
        
        if len(sols) < 2:
            print(f"Couldn't do it for z: {z} and w: {w}")
            return None
        
        q1, q2 = sols
        arc0 = orientedProjective2.CircleArcOP2.fromPointOP2(q1, p1, q2)

        if q1.hy * q2.hw > q2.hy * q1.hw:
            arcDisk = arc0.disk
        else:
            arcDisk = orientedProjective2.DiskOP2(
                -arc0.disk.a, 
                -arc0.disk.b, 
                -arc0.disk.c, 
                -arc0.disk.d
            )

        return orientedProjective2.CircleArcOP2(q1, q2, arcDisk)
# END LineH2

@dataclass(frozen=True)
class SegmentH2:
    
    __slots__ = ['source', 'target']
    
    source: PointH2
    target: PointH2
    
    def __iter__(self):
        yield self.source
        yield self.target
        
    def toPoincareCircleArcOP2(self):
        z = self.source.coord
        w = self.target.coord
        
        unitDisk = orientedProjective2.DiskOP2(1,0,0,-1)
        p1, p2 = (
            orientedProjective2.PointOP2(z.real, z.imag), 
            orientedProjective2.PointOP2(w.real, w.imag)
        )
        disk = orientedProjective2.DiskOP2.orthogonalToDiskAndThroughPoints(
            unitDisk, p1, p2
        )
        sols = unitDisk.intersectWithDiskOP2(disk)
        
        if len(sols) < 2:
            print(f"Couldn't do it for z: {z} and w: {w}")
            return None
        
        q1, q2 = sols
        arc0 = orientedProjective2.CircleArcOP2.fromPointOP2(q1, p1, q2)

        if p1.hy * p2.hw > p2.hy * p1.hw:
            arcDisk = arc0.disk
        else:
            arcDisk = orientedProjective2.DiskOP2(
                -arc0.disk.a, 
                -arc0.disk.b, 
                -arc0.disk.c, 
                -arc0.disk.d
            )

        return orientedProjective2.CircleArcOP2(p1, p2, arcDisk)
# END SegmentH2

@dataclass(frozen=True)
class CircleH2:
    
    __slots__ = ['center', 'xRadius']
    
    center: PointH2
    xRadius: Any
        
    @classmethod
    def withCenterAndHRadius(cls, center, hRadius):
        xRadius = 1 - math.exp(-2.0 * hRadius)
        return cls(center, xRadius)
    
    @classmethod
    def withCenterAndSRadius(cls, center, sRadius):
        xRadius = sRadius if sRadius <= 0.0 else (1 - sRadius * sRadius)
        return cls(center, sRadius)
        
    @property
    def sRadius(self):
        return self.xRadius if self.xRadius <= 0.0 else math.sqrt(1.0 - self.xRadius)
    
    @property
    def hRadius(self):
        if self.xRadius > 0.0:
            if self.xRadius > 1e-4:
                return -0.5 * math.log(1.0 - self.xRadius)
            else:
                return self.xRadius * (1.0 + x * (0.5 + self.xRadius / 3.0)) / 2.0
        else:
            return self.xRadius

    def toPoincareCircleE2(self):
        s_rad = self.sRadius
        if (s_rad <= 0.0): # infinite hyperbolic radius (usually negative of euclidean radius)
            a = 1.0 + s_rad
            e_center = self.center.coord.toComplex() * a
            e_rad = -s_rad # assumes -s_rad is meaningful
        else:
            ahc = abs(self.center)
            n1 = (1.0 + s_rad) * (1.0 + s_rad)
            n2 = n1 - ahc * ahc * self.xRadius * self.xRadius / n1
            e_rad = abs(self.xRadius * (1.0 - ahc * ahc) / n2) # can be <0 due to numerical error
            b = 4 * s_rad / n2
            e_center = b * self.center.coord.toComplex()
        return CircleE2(PointE2(e_center.real, e_center.imag), e_rad)
# END CircleH2
