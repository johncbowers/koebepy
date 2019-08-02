#
# Geometry of the Hyperbolic Plane
#

from dataclasses import dataclass
from .euclidean2 import PointE2, CircleE2
from .extendedComplex import ExtendedComplex
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

# END PointH2

PointH2.O = PointH2(ExtendedComplex.ZERO)

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
