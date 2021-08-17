"""
Perhaps these should be included in the respective geometries python files, but 
it seems useful to collect all the triangle related functions in the same namespace. 
"""

from math import sqrt


def triangleSignedAreaE2(A, B, C):
    """
    Returns the area of the triangle ABC signed by orientation (ccw is > 0)
    """
    return 0.5 * (A.x * (B.y - C.y) + A.y * (C.x - B.x) + (B.x * C.y - B.y * C.x))

def triangleAreaE2(A, B, C):
    return abs(triangleSignedAreaE2(A, B, C))

def triangleAreaE3(A, B, C):
    a = A.distSqTo(B)
    b = B.distSqTo(C)
    c = C.distSqTo(A)
    AreaSq = (2 * a * b + 2 * b * c + 2 * c * a - a * a - b * b - c * c) * 0.0625
    return sqrt(AreaSq)

def barycentricCoordinatesOf(P, A, B, C, areaFunc):
    """
    Computes the barycentric coordinates of the point P in the triangle ABC. 
    
    WARNING: Only correct if P is on the triangle ABC.

    Parameters:
        P: T - The point at which to compute the barycentric coordinates. 
        A: T - Corner of the triangle. 
        B: T - Corner of the triangle. 
        C: T - Corner of the triangle. 
        areaFunc: (T, T, T) -> U - The area function for the generic point type T. 

    Returns: 
        The barycentric coordinates of u, v, w of P where uA + vB + wC = P.  
    """
    invABC = 1.0 / areaFunc(A, B, C)
    CAP = areaFunc(C, A, P)
    ABP = areaFunc(A, B, P)
    BCP = areaFunc(B, C, P)
    return CAP * invABC, ABP * invABC, BCP * invABC

def barycentricCoordinatesOfE2(P, A, B, C):
    """
    Implementation from Christer Ericson's book Real-Time Collision Detection
    """
    #return barycentricCoordinatesOf(P, A, B, C, areaFunc=triangleSignedAreaE2)
    v0 = B - A
    v1 = C - A
    v2 = P - A
    d00 = v0.dot(v0)
    d01 = v0.dot(v1)
    d11 = v1.dot(v1)
    d20 = v2.dot(v0)
    d21 = v2.dot(v1)
    denom = d00 * d11 - d01 * d01
    inv_denom = 1 / denom
    v = (d11 * d20 - d01 * d21) * inv_denom
    w = (d00 * d21 - d01 * d20) * inv_denom
    u = 1 - v - w
    return u, v, w


def barycentricCoordinatesOfE3(P, A, B, C):
    N  = (B - A).cross(C - A)
    NA = (C - B).cross(P - B)
    NB = (A - C).cross(P - C)
    NC = (B - A).cross(P - A)
    invNm2 = 1 / N.dot(N)
    return N.dot(NA) * invNm2, N.dot(NB) * invNm2, N.dot(NC) * invNm2

def barycentricInterpolate(Adata, Bdata, Cdata, u, v, w):
    return Adata * u + Bdata * v + Cdata * w

def pointOnTrianglePlane(P, A, B, C):
    """
    Projects the point P onto the plane containing traingle A, B, C
    """
    N = (B - A).cross(C - A).normalize()
    return P + (-(P - A).dot(N))*N

def pointInTriangle(P, A, B, C):
    a, b, c = A - P, B - P, C - P
    u = b.cross(c)
    v = c.cross(a)
    w = a.cross(b)
    return u.dot(v) >= 0 and u.dot(w) >= 0

def barycentricTransformE2(P, A, B, C, D, E, F):
    from koebe.geometries.euclidean2 import PointE2
    """
    Transforms a point P with respect to the triangle ABC to the triangle DEF. 
    """
    u, v, w = barycentricCoordinatesOfE2(P, A, B, C)
    return PointE2(u * D.x + v * E.x + w * F.x, 
                   u * D.y + v * E.y + w * F.y)

def barycentricTransformE3(P, A, B, C, D, E, F):
    from koebe.geometries.euclidean3 import PointE3
    """
    Transforms a point P with respect to the triangle ABC to the triangle DEF. 
    """
    u, v, w = barycentricCoordinatesOfE3(P, A, B, C)
    return PointE3(u * D.x + v * E.x + w * F.x, 
                   u * D.y + v * E.y + w * F.y, 
                   u * D.z + v * E.z + w * F.z)

def triangleBasis(A, B, C):
    U = B - A
    V = C - A
    e1 = U.normalize()
    Vp = V.dot(e1) * e1
    e2 = (V - Vp).normalize()
    return e1, e2

    