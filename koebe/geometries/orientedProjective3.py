#
# Oriented projective 3-space primitives
#

import math
from . import euclidean3
from .commonOps import determinant2, isZero, are_dependent4, inner_product4

class LineOP3:
    def __init__(self, p01, p02, p03, p12, p13, p23):
        self.p01 = p01
        self.p02 = p02
        self.p03 = p03
        self.p12 = p12
        self.p13 = p13
        self.p23 = p23
        
    def __iter__(self):
        yield self.p01
        yield self.p02
        yield self.p03
        yield self.p12
        yield self.p13
        yield self.p23
    
    @classmethod
    def fromPointOP3(cls, p1, p2):
        return cls(
            determinant2(p1.hx, p1.hy, p2.hx, p2.hy), # p01 
            determinant2(p1.hx, p1.hz, p2.hx, p2.hz), # p02
            determinant2(p1.hx, p1.hw, p2.hx, p2.hw), # p03
            determinant2(p1.hy, p1.hz, p2.hy, p2.hz), # p12
            determinant2(p1.hy, p1.hw, p2.hy, p2.hw), # p13
            determinant2(p1.hz, p1.hw, p2.hz, p2.hw)  # p23
        )
    
    @classmethod
    def fromPlaneOP3(cls, p1, p2):
        return cls(
            +determinant2(p1.Z, p1.W, p2.Z, p2.W), # p01 Mz
            -determinant2(p1.Y, p1.W, p2.Y, p2.W), # p02 My
            +determinant2(p1.Y, p1.Z, p2.Y, p2.Z), # p03 -Nx
            +determinant2(p1.X, p1.W, p2.X, p2.W), # p12 Mx
            -determinant2(p1.X, p1.Z, p2.X, p2.Z), # p13 -Ny
            +determinant2(p1.X, p1.Y, p2.X, p2.Y)  # p23 -Nz
        )
    
    def dualLineOP3(self):
        return LineOP3(
             self.p23, 
            -self.p13, 
             self.p12,
             self.p03, 
            -self.p02, 
             self.p01
        )
    
    def getIntersectionWithUnit2Sphere(self):

        # TODO Decide if this should be done with homogeneous coordinates
        v = euclidean3.VectorE3(-self.p03, -self.p13, -self.p23)
        m = euclidean3.VectorE3(-self.p12,  self.p02, -self.p01)
        
        # TODO (Sarah) Compute the intersections of this line with the 2-sphere: 

        # obtain a point on the line by choosing a point parallel to the x, y, or z plane
        # three points of intersection between the line and the x=0, y=0, and z=0 planes

        # ex: basis1 : VectorE3 by lazy { least_dominant(VectorE3(a, b, c)).vec.cross(VectorE3(a, b, c)) }
        # larger than or equal to

        # x = 0 plane
        if (abs(v.x) >= abs(v.y) and abs(v.x) >= abs(v.z)):
            px = 0.0
            py =  m.z / v.x
            pz = -m.y / v.x
        # y = 0 plane
        elif (abs(v.y) >= abs(v.x) and abs(v.y) >= abs(v.z)):
            px = -m.z / v.y
            py = 0.0
            pz = m.x / v.y
        # z = 0 plane
        else:
            px = m.y / v.z
            py = -m.x / v.z
            pz = 0.0

        p = euclidean3.VectorE3(px, py, pz)

        # want the point where p+tv intersects the unit sphere, i.e. where ||p|| = 1;  p.p = 1

        # determine whether line intersects sphere at 0, 1, or 2 points
        rad = math.sqrt( 4*math.pow(p.dot(v), 2.0) - 4.0*(p.dot(p)- 1)*(v.dot(v)) )

        # if intersects at one point (line is tangent to the unit sphere)
        if (isZero(rad)):

            t = -p.dot(v)/v.dot(v)
            u = (p + t * v).toPointE3()

            return [u]
        # if line intersects the sphere at two points
        elif rad > 0.0:

            t1 = (-2 * (p.dot(v)) + math.sqrt(4 * math.pow(p.dot(v), 2.0) - 4.0 * (p.dot(p) - 1) * (v.dot(v)))) / (2 * v.dot(v))
            t2 = (-2 * (p.dot(v)) - math.sqrt(4 * math.pow(p.dot(v), 2.0) - 4.0 * (p.dot(p) - 1) * (v.dot(v)))) / (2 * v.dot(v))

            # plugging back into the parametrized eq. for the line p + tv
            u1 = (p + t1 * v).toPointE3()
            u2 = (p + t2 * v).toPointE3()

            return [u1, u2]
        # if line does not intersect the sphere
        else:
            return []
        
# END LineOP3

class PointOP3:
    
    def __init__(self, hx, hy, hz, hw = 1.0):
        self.hx = hx
        self.hy = hy
        self.hz = hz
        self.hw = hw
        
    def __iter__(self):
        yield self.hx
        yield self.hy
        yield self.hz
        yield self.hw
    
    @classmethod
    def fromPointOP3(cls, p):
        return cls(p.hx, p.hy, p.hz, p.hw)
    
    @classmethod
    def fromPointE3(cls, p):
        return cls(p.x, p.y, p.z)
    
    def __sub__(self, p):
        if isinstance(p, VectorOP3):
            return VectorOP3(
                self.hx * p.hw - p.hx * self.hw, 
                self.hy * p.hw - p.hy * self.hw, 
                self.hz * p.hw - p.hz * self.hw, 
                self.hw * p.hw
            )
        elif isinstance(p, PointOP3):
            return PointOP3(
                self.hx * p.hw - p.hx * self.hw, 
                self.hy * p.hw - p.hy * self.hw, 
                self.hz * p.hw - p.hz * self.hw, 
                self.hw * p.hw
            )
        else:
            raise TypeError("PointOP3 subtraction is only defined for PointOP3 and VectorOP3")
    
    def __add__(self, v):
        return PointOP3(
                self.hx * v.hw - v.hx * self.hw, 
                self.hy * v.hw - v.hy * self.hw, 
                self.hz * v.hw - v.hz * self.hw, 
                self.hw * v.hw
            )
    
    def __eq__(self, p):
        return (
            are_dependent4(
                self.hx, self.hy, self.hz, self.hw, 
                p.hx, p.hy, p.hz, p.hw
            )
            and inner_product4(self.hx, self.hy, self.hz, self.hw, 
                               p.hx, p.hy, p.hz, p.hw) > 0
        )
    
    def __ne__(self, p):
        return not self == p
    
    def normSq(self):
        return (self.hx * self.hx 
                + self.hy * self.hy
                + self.hz * self.hz
               ) / (self.hw * self.hw)
    
    def norm(self):
        return math.sqrt(self.normSq())
    
    def isIdeal(self):
        return self.hw == 0.0
    
    def toPointE3(self):
        fact = 1.0 / self.hw
        return euclidean3.PointE3(
            self.hx * fact, 
            self.hy * fact, 
            self.hz * fact
        )
    
    def unitSphereInversion(self):
        # TODO haven't checked if this is correct
        return PointOP3(self.hx, self.hy, self.hz, self.hw * self.normSq())
    
# END PointOP3

class PlaneOP3:
    def __init__(self, X, Y, Z, W):
        self.X = X
        self.Y = Y
        self.Z = Z
        self.W = W
        
    def __iter__(self):
        yield self.X
        yield self.Y
        yield self.Z
        yield self.W
    
    @classmethod
    def fromPointOP3(cls, p1, p2, p3):
        return cls(
            X = + determinant(
                    p1.hy, p1.hz, p1.hw,
                    p2.hy, p2.hz, p2.hw,
                    p3.hy, p3.hz, p3.hw
            ),
            Y = - determinant(
                    p1.hx, p1.hz, p1.hw,
                    p2.hx, p2.hz, p2.hw,
                    p3.hx, p3.hz, p3.hw
            ),
            Z = + determinant(
                    p1.hx, p1.hy, p1.hw,
                    p2.hx, p2.hy, p2.hw,
                    p3.hx, p3.hy, p3.hw
            ),
            W = - determinant(
                    p1.hx, p1.hy, p1.hz,
                    p2.hx, p2.hy, p2.hz,
                    p3.hx, p3.hy, p3.hz
            )
        )
    
    def isIncident(p: PointOP3):
        return isZero(  self.X * p.hx 
                      + self.Y * p.hy 
                      + self.Z * p.hz 
                      + self.W * p.hw)
# END PlaneOP3

class VectorOP3:
    def __init__(self, hx, hy, hz, hw = 1.0):
        self.hx = hx
        self.hy = hy
        self.hz = hz
        self.hw = hw
        
    def __iter__(self):
        yield self.hx
        yield self.hy
        yield self.hz
        yield self.hw
    
    @classmethod
    def fromVectorOP3(self, v):
        return VectorOP3(v.hx, v.hy, v.hz, v.hw)
    
    @classmethod
    def fromVectorE3(self, v):
        return VectorOP3(v.x, v.y, v.z)
    
    def __eq__(self, v):
        return (
            are_dependent4(hx, hy, hz, hw, v.hx, v.hy, v.hz, v.hw)
            and inner_product4(hx, hy, hz, hw, v.hx, v.hy, v.hz, v.hw) > 0
        )
    
    def __ne__(self, v):
        return not self == v
    
    def __add__(self, v):
        return VectorOP3(
            self.hx * v.hw + v.hx * self.hw, 
            self.hy * v.hw + v.hy * self.hw, 
            self.hz * v.hw + v.hz * self.hw, 
            self.hw * v.hw
        )
    
    def __mul__(self, d):
        return VectorOP3(
            self.hx * d, 
            self.hy * d, 
            self.hz * d, 
            self.hw
        )
    
    def __rmul__(self, d):
        return self * d
    
    def isIdeal(self):
        return self.hw == 0.0
    
    def toVectorE3(self):
        fact = 1.0 / self.hw
        return euclidean3.VectorE3(self.hx * fact, self.hy * fact, self.hz * fact)
# END VectorOP3

# class objects
PointOP3.O = PointOP3(0, 0, 0, 1)