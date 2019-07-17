#
# Classes for working in Euclidean 2-space
#

import math

class PointE2:
    
    def __init__(self, x = 0.0, y = 0.0):
        self.x = x
        self.y = y
        
    def __iter__(self):
        yield self.x
        yield self.y
    
    @classmethod
    def fromPointE2(cls, p):
        return cls(p.x, p.y)
    
    def __sub__(self, other):
        return VectorE2(self.x - other.x,
                        self.y - other.y)
    
    def distSqTo(self, p):
        dx = p.x - self.x
        dy = p.y - self.y
        return dx * dx + dy * dy
    
    def distTo(self, p):
        return math.sqrt(self.distSqTo(p))
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __ne__(self, other):
        return not self == other
# TODO After SegmentE2 and DiskE2 are implemented, uncomment
#     def distSqToSegmentE2(self, seg):
#         return self.distSqTo(seg.closestPointE2To(self))
#     def distToSegmentE2(self, seg):
#         return math.sqrt(self.distSqToSegmentE2(seg))
#     def distToDiskE2(self, disk):
#         return self.distTo(disk.center) - disk.radius
  
# END PointE2
PointE2.O = PointE2()

class VectorE2:
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def __iter__(self):
        yield self.x
        yield self.y
    
    def __add__(self, other):
        return VectorE2(self.x + other.x, 
                        self.y + other.y)
    
    def __sub__(self, other):
        return VectorE2(self.x - other.x,
                        self.y - other.y)
    
    def __mul__(self, a):
        return VectorE2(self.x * a, self.y * a)
    
    def __rmul__(self, a):
        return VectorE2(self.x * a, self.y * a)
    
    def __truediv__(self, a):
        return VectorE2(self.x / a, self.y / a)
    
    def __neg__(self):
        return VectorE2(-self.x, -self.y)
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __ne__(self, other):
        return not self == other
    
    def dot(self, p):
        return self.x * p.x + self.y * p.y
    
    def normSq(self):
        return self.x * self.x + self.y * self.y
    
    def norm(self):
        return math.sqrt(self.normSq())
    
    def angleFromXAxis(self):
        normInv = 1.0 / self.norm()
        if self.y >= 0:
            return math.acos(self.dot(VectorE2(1.0, 0.0)) * normInv)
        else:
            return 2 * math.pi - math.acos(self.dot(VectorE2(1.0, 0.0)) * normInv)
     
# END VectorE2
