#
# Extended Complex Numbers (includes representations at infinity)
#

import spherical2

def absSq(z):
    return z.real * z.real + z.imag * z.imag

class ExtendedComplex:
    
    def __init__(self, z, w):
        self.z = z
        self.w = w
        if z == 0 and w == 0:
            raise ValueError("z and w cannot both be 0")
    
    @classmethod
    def fromExtendedComplex(cls, z):
        return cls(z.z, z.w)
    
    def toComplex(self):
        return self.z / self.w
    
    def applyMobius(a:complex, b:complex, c:complex, d:complex) -> "ExtendedComplex":
        return ExtendedComplex(a * z + b * w, c * z + d * w)
    
    def toPointS2(): 
        zwc = self.z * self.w.conjugate()
        zcw = self.z.conjugate() * self.w
        absSqz = absSq(self.z)
        absSqw = absSq(self.w)
        hypotSq = absSqz + absSqw
        return spherical2.PointS2(
                ((zwc + zcw) / complex(hypotSq, 0.0)).real,
                ((zwc - zcw) / complex(0.0, hypotSq)).real,
                (complex(absSqz - absSqw, hypotSq)).real
        )