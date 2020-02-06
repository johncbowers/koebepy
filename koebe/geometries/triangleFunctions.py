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
    return barycentricCoordinatesOf(P, A, B, C, areaFunc=triangleAreaE2)

def barycentricCoordinatesOfE3(P, A, B, C):
    return barycentricCoordinatesOf(P, A, B, C, areaFunc=triangleAreaE3)

def barycentricInterpolate(Adata, Bdata, Cdata, u, v, w):
    return Adata * u + Bdata * v + Cdata * w


