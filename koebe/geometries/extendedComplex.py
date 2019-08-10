#
# Extended Complex Numbers (includes representations at infinity)
#

from typing import Any, Optional, Union, List
from dataclasses import dataclass
from . import spherical2
from . import orientedProjective2

import math

def absSq(z):
    return z.real * z.real + z.imag * z.imag

def _to_complex(z):
    if isinstance(z, complex):
        return z
    elif isinstance(z, ExtendedComplex):
        return z.toComplex()
    else:
        return complex(z, 0)

def _to_extendedcomplex(z):
    if isinstance(z, ExtendedComplex):
        return z
    else:
        return ExtendedComplex(z)
    
@dataclass(frozen=True)
class ExtendedComplex:
    
    __slots__ = ['z', 'w', '_complex']
    
    z: Any
    w: Any
    _complex: Any
    
    def __init__(self, z, w = 1+0j):
        object.__setattr__(self, 'z', _to_complex(z))
        object.__setattr__(self, 'w', _to_complex(w))
        
        object.__setattr__(self, '_complex', None)
        
        if z == 0 and w == 0:
            raise ValueError("z and w cannot both be 0")
        
    def __iter__(self):
        yield self.z
        yield self.w
    
    @property
    def real(self):
        return self.toComplex().real
    
    @property
    def imag(self):
        return self.toComplex().imag 
    
    @classmethod
    def fromExtendedComplex(cls, z):
        return cls(z.z, z.w)
    
    @classmethod
    def fromFloat(cls, z: float) -> "ExtendedComplex":
        return cls(z+0j, 1+0j)
    
    @classmethod
    def fromComplex(cls, z: complex) -> "ExtendedComplex":
        return cls(z, 1+0j)
    
    def toComplex(self):
        if self._complex == None:
            object.__setattr__(self, '_complex', self.z / self.w)
        return self._complex
    
    def arg(self):
        c = self.toComplex()
        return math.atan2(c.imag, c.real)
    
    def sqrt(self):
        c = self.toComplex()
        r = abs(c)
        phi = self.arg()
        return ExtendedComplex(complex(math.sqrt(r) * math.cos(phi / 2.0), 
                                       math.sqrt(r) * math.sin(phi / 2.0)))
    
    def applyMobius(self, 
                    a:"ExtendedComplex", 
                    b:"ExtendedComplex", 
                    c:"ExtendedComplex", 
                    d:"ExtendedComplex") -> "ExtendedComplex":
        return ExtendedComplex(a * self.z + b * self.w, c * self.z + d * self.w)

# Better to use PointS2.sgProjectFromExtendedComplex
#     def toPointS2(self): 
#         zwc = self.z * self.w.conjugate()
#         zcw = self.z.conjugate() * self.w
#         absSqz = absSq(self.z)
#         absSqw = absSq(self.w)
#         hypotSq = absSqz + absSqw
#         return spherical2.PointS2(
#                 ((zwc + zcw) / complex(hypotSq, 0.0)).real,
#                 ((zwc - zcw) / complex(0.0, hypotSq)).real,
#                 (complex(absSqz - absSqw, hypotSq)).real
#         )
    
    
    def __add__(self, other):
        if not isinstance(other, ExtendedComplex):
            other = ExtendedComplex(other, complex(1,0))
        return ExtendedComplex(self.z * other.w + other.z * self.w, self.w * other.w)
    
    def __sub__(self, other):
        if not isinstance(other, ExtendedComplex):
            other = ExtendedComplex(other, complex(1,0))
        return self + (-other)
    
    def __mul__(self, other):
        if not isinstance(other, ExtendedComplex):
            other = ExtendedComplex(other, complex(1,0))
        return ExtendedComplex(self.z * other.z, self.w * other.w)
    
    def __truediv__(self, other):
        if not isinstance(other, ExtendedComplex):
            other = ExtendedComplex(other, complex(1,0))
        return ExtendedComplex(self.z * other.w, self.w * other.z)
    
    
    def __radd__(self, other):
        if not isinstance(other, ExtendedComplex):
            other = ExtendedComplex(other, complex(1,0))
        return ExtendedComplex(self.z * other.w + other.z * self.w, self.w * other.w)
    
    def __rsub__(self, other):
        if not isinstance(other, ExtendedComplex):
            other = ExtendedComplex(other, complex(1,0))
        return other + (-self)
    
    def __rmul__(self, other):
        if not isinstance(other, ExtendedComplex):
            other = ExtendedComplex(other, complex(1,0))
        return ExtendedComplex(self.z * other.z, self.w * other.w)
    
    def __rtruediv__(self, other):
        if not isinstance(other, ExtendedComplex):
            other = ExtendedComplex(other, complex(1,0))
        return ExtendedComplex(other.z * self.w, other.w * self.z)
    
    
    def __neg__(self):
        return ExtendedComplex(-self.z, self.w)
    
    def __abs__(self):
        return abs(self.z) / abs(self.w)
    
    def __pow__(self, b):
        return ExtendedComplex(self.z**b, self.w**b)
    
    def __pos__(self):
        return ExtendedComplex(self.z, self.w)
    
    def conjugate(self):
        return ExtendedComplex(self.z.conjugate(), self.w.conjugate())
    
    def __eq__(self, other):
        if not isinstance(other, ExtendedComplex):
            other = ExtendedComplex(other)
        return self.z * other.w == other.z * self.w # cross multiplication should be the same
    
    @property
    def modulus(self):
        return abs(self)
    
    @property
    def modulusSquared(self):
        return (self.z * self.z.conjugate()).real / (self.w * self.w.conjugate()).real
    
    @property
    def isFinite(self):
        return self.w != complex(0,0)
    
    @property
    def isInfinite(self):
        return self.w == complex(0,0)
    
    @property
    def reciprocal(self):
        return ExtendedComplex(self.w, self.z)
    
    def crossRatioWith(self, z1, z2, z3):
        return ((self - z1) * (z2 - z3)) / ((self - z3) * (z2 - z1))
    
    def toPointOP2(self):
        from .orientedProjective2 import PointOP2
        if self.w.imag == 0:
            return PointOP2(self.z.real, self.z.imag, self.w.real)
        else:
            return PointOP2(self.real, self.imag)
    
# END ExtendedComplex

ExtendedComplex.ZERO      = ExtendedComplex(complex(0, 0), complex(1, 0))
ExtendedComplex.ONE       = ExtendedComplex(complex(1, 0), complex(1, 0))
ExtendedComplex.I         = ExtendedComplex(complex(0, 1), complex(1, 0))
ExtendedComplex.RINFINITY = ExtendedComplex(complex(1, 0), complex(0, 0))
ExtendedComplex.IINFINITY = ExtendedComplex(complex(0, 1), complex(0, 0))

def _onDisk(z):
    return abs(1 - abs(z)) < 1e-8

def _outsideDisk(z):
    return abs(z) - 1 > 1e-8

class MobiusError(Exception):
    pass

@dataclass(frozen=True)
class Mobius:
    
    __slots__ = ['a', 'b', 'c', 'd']
    
    a: ExtendedComplex
    b: ExtendedComplex
    c: ExtendedComplex
    d: ExtendedComplex
        
    @classmethod
    def transformToZeroOneInfinity(cls, z1: ExtendedComplex, z2: ExtendedComplex, z3: ExtendedComplex) -> "Mobius":
        z2mz3 = z2 - z3
        z2mz1 = z2 - z1
        return cls(z2mz3, -z1*z2mz3, z2mz1, -z3*z2mz1)
    
    def apply(self, z: ExtendedComplex, *zs: ExtendedComplex) -> Union[ExtendedComplex, List[ExtendedComplex]]:
        if len(zs) == 0:
            return z.applyMobius(self.a, self.b, self.c, self.d)
        else:
            return ([z.applyMobius(self.a, self.b, self.c, self.d)]
                    + [w.applyMobius(self.a, self.b, self.c, self.d) for w in zs])
    
    def applyToPointS2(self, p: "spherical2.PointS2") -> "spherical2.PointS2":
        z = p.sgProjectToExtendedComplex() # Stereographically project to extended complex
        return spherical2.PointS2.sgProjectFromExtendedComplex(self.apply(z))
    
    @property
    def det(self):
        return (self.a * self.d) - (self.c * self.b)
    
    def normalize(self):
        dett = self.det
        detSqrt = dett.sqrt().reciprocal
        return Mobius(self.a * detSqrt, self.b * detSqrt, self.c * detSqrt, self.d * detSqrt)
    
    @property
    def inverse(self):
        det = self.det
        return Mobius(self.d / det, -(self.b / det), -(self.c / det), self.a / det)
    
    def conjugate(self):
        return Mobius(self.a.conjugate(), 
                      self.b.conjugate(),
                      self.c.conjugate(),
                      self.d.conjugate())
    
    def transpose(self):
        return Mobius(self.a, self.c, self.b, self.d)
    
    def scale(self, factor):
        return Mobius(self.a * factor, self.b * factor, self.c, self.d)
    
    def __mul__(self, other):
        return Mobius(self.a * other.a + self.b * other.c, 
                      self.a * other.b + self.b * other.d, 
                      self.c * other.a + self.d * other.c, 
                      self.c * other.b + self.d * other.d)
    
    # from Mobius.trans_abAB in CirclePack (Ken Stephenson)
    @classmethod
    def transformForTwoPointsOnUnitDisk(cls, 
                                        a: ExtendedComplex, b: ExtendedComplex, 
                                        A: ExtendedComplex, B: ExtendedComplex, 
                                        c: ExtendedComplex, C: ExtendedComplex) -> "Mobius":
        MOB_TOLER = 1e-12

        if not (_onDisk(a) and _onDisk(b) and _onDisk(A) and _onDisk(B)):
            raise MobiusError("One of a, b, A, or B is not on the unit circle.")
        
        if abs(a - b) < MOB_TOLER or abs(A - B) < MOB_TOLER:
            return Mobius(A / a, ExtendedComplex.ZERO, ExtendedComplex.ONE, ExtendedComplex.ZERO).normalize()
        else:
            if abs(c) > 1.001 or abs(C) > 1.001:
                # Value is outside the disc so default to zero
                c = ExtendedComplex.ZERO
                C = ExtendedComplex.ZERO
            
            M1 = Mobius.normalize_abc(a, b, c)
            M2 = Mobius.normalize_abc(A, B, C)
            
            mob = M2.inverse * M1
            return mob.normalize()
        
    # from Mobius.norm_abc in CirclePack (Ken Stephenson)
    @classmethod
    def normalize_abc(cls, a: ExtendedComplex, b: ExtendedComplex, c: ExtendedComplex) -> "Mobius":
        
        MOD1 = .99999999
        MOB_TOLER = 1e-12
        
        if not _onDisk(a) or not _onDisk(b) or _outsideDisk(c):
            raise MobiusError("Either a or b are not on the disk or c is outside the disk.")

        A = a * abs(a)
        B = b * abs(b)
        
        R = Mobius(ExtendedComplex.ONE, A, -ExtendedComplex.ONE, A)
        img = R.apply(B)
        
        T = Mobius(ExtendedComplex.ONE, ExtendedComplex(complex(0, -img.imag)), 
                   ExtendedComplex.ZERO, ExtendedComplex.ONE)
        
        M = T * R
        
        M = M.scale(M.apply(c).reciprocal)
        
        W = Mobius(ExtendedComplex.ONE, -ExtendedComplex.ONE, ExtendedComplex.ONE, ExtendedComplex.ONE)
        
        return W * M
        
        
Mobius.ID = Mobius(1.0, 0.0, 0.0, 1.0)
