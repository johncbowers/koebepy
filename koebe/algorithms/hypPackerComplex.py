# Thurston style hyperbolic circle packings. 
# Adapted from Ken Stephenson's CirclePack program. 

import math

from ..datastructures.dcel import Vertex, Dart, DCEL
#from ..geometries.extendedComplex import ExtendedComplex, Mobius
from ..geometries.hyperbolic2 import PointH2, CircleH2

import cmath

from collections import deque

from typing import Optional, Union, List

from dataclasses import dataclass

OKERR = 1e-9 # Some other tolerance from CirclePack
MOB_TOLER = 1e-12 # Tolerance for Mobius transformations to consider points too close

    

# Computes the cosine of the face angle at x1 given a triangle
# formed by mutually tangent circles of radius x1, x2, and x3
# HyperbolicMath.h_comp_x_cos in CirclePack
def _cosFaceAngle(x1: float, x2: float, x3: float) -> float:
    """Computes the cosine of the face angle for a triple of hyperbolic circles. 
    
    Args:
        x1: The radius of the circle at which to compute the cosine face angle. 
        x2: The second circle's radius. 
        x3: The third circle's radius. 
    
    Returns:
        The cosine of the face angle at x1. 
    """
    if x1 <= 0: # x1 is a horocycle
        return 1.0
    elif x2 <= 0 and x3 <= 0: # both neighbors are horocycles
        return (2.0 * x1 - 1.0)
    elif x2 <= 0: # Only x2 is a horocycle
        x = x3 - x1 * x3
        return ((x1 - x) / (x1 + x))
    elif x3 <= 0: # Only x3 is a horocycle
        x = x2 - x1 * x2
        return ((x1 - x) / (x1 + x))
    else:
        ans = (x1 * (x1 + (1.0 - x1) * (x2 + x3 - x2 * x3)) 
                  / ((x1 + x3 - x1 * x3) * (x1 + x2 - x1 * x2)))
        ans = 2.0 * ans - 1.0
        if ans > 1.0:
            return 1.0
        elif ans < -1.0:
            return -1.0
        else: 
            return ans

# Computes the hyperbolic face angle at the origin of outDart
def _faceAngleForOriginOf(outDart: Dart, withRadius: Optional[float] = None) -> float:
    """Computes the face angle at the origin of a given dart.
    
    This function computes the face angle at the origin of parameter outDart
    in the face incident to outDart. It will use outDart.origin.data[1] as 
    the radius of the origin unless optional parameter withRadius is set to
    something other than None. In that case, it uses withRadius as the radius
    of the circle at the origin.
    
    Args:
        outDart: The outgoing dart from the face angle. 
        withRadius: If not None (which is the default), the radius to use for 
            the origin of outDart. 
    
    Returns:
        The face angle at the origin of outDart. 
    """
    return math.acos(
               _cosFaceAngle(
                    outDart.origin.data[1] if withRadius == None else withRadius, 
                    outDart.dest.data[1], 
                    outDart.prev.origin.data[1]
               )
           )

# if vRad is None, uses the stored label radius for vert. 
# otherwise uses vRad as vert's radius. 
# PackData.h_anglesum_overlap in CirclePack
def _angleSumFor(vertex: Vertex, withRadius: Optional[float] = None) -> float:
    """Computes the angle sum at a given vertex. 
    
    Note that if optional parameter withRadius is set to None (the default) then 
    vertex.data[1] is used as the radius for this vertex. Otherwise, the parameter 
    withRadius is used as the radius for vertex. 
    
    Args:
        vertex: The vertex to compute the angle sum for. 
        withRadius: The radius to use for vertex (None is default, and uses vertex.data[1] instead.)
        
    Returns:
        The angle sum at vertex.
    """
    return sum([_faceAngleForOriginOf(dart, withRadius) for dart in vertex.outDarts()])

# Computes the new radius for a vertex
# PackData.h_radcalc in CirclePack
def _newRadiusEstimate(vertex: Vertex, guessRadius: float, aim: float, num_iterations: int = 3) -> float:
    """Computes a new radius for a vertex that moves its angle sum closer to aim. 
    
    Args:
        vertex: The vertex at which to compute a new radius. 
        guessRadius: A guess at what radius to use (usually the current radius.)
        aim: The goal angle sum. 
        num_iterations: The total number of iterations to use in modifying from guessRadius (default is 3). 
    
    Returns:
        A new radius that brings vertex's angle sum closer to aim. 
    """
    global OKERR
    
    lower, upper, factor = 0.5, 0.5, 0.5
    bestcurv = lowcurv = upcurv = _angleSumFor(vertex, withRadius=guessRadius)
    
    if bestcurv > (aim + OKERR):
        lower = 1.0 - factor + guessRadius * factor
        lowcurv = _angleSumFor(vertex, withRadius=lower)
        if lowcurv > aim:
            return lower
    elif bestcurv < (aim - OKERR):
        upper = guessRadius * factor
        upcurv = _angleSumFor(vertex, withRadius=upper)
        if upcurv < aim:
            return upper
    else:
        return guessRadius
    
    r = guessRadius
    
    for _ in range(num_iterations):
        if bestcurv > (aim + OKERR):
            upper = r
            upcurv = bestcurv
            r -= (bestcurv - aim) * (lower - r) / (lowcurv - bestcurv)
        elif bestcurv < (aim - OKERR):
            lower = r
            lowcurv = bestcurv
            r += (aim - bestcurv) * (upper - r) / (upcurv - bestcurv)
        else:
            return r
        bestcurv = _angleSumFor(vertex, withRadius=r)

    return r
            
class PackingError(Exception):
    """A class for any exceptions encountered during circle packing."""
    pass

_REPACK_DEBUG = False

def repack(dcel: DCEL, num_passes: int = 1000, tolerance: float = 3e-10) -> (DCEL, int):
    """Computes a hyperbolic maximal packing label of the given DCEL. 
    
    This function assumes that the DCEL is a triangulated disk with the boundary given
    by the vertices and darts incident to diskDcel.outerFace. 
    
    It also assumes that at each vertex, the .data attribute is a list [z, r] where
    z is the current circle center and r is the current hyperbolic radius if not a boundary
    circle, or r is negative otherwise. 
    
    It also assumes that v.aim is set to 2*math.pi for any interior vertex and -1 for any
    boundary vertex. 
    
    Args:
        diskDcel: The input DCEL. Should be a triangulated disk with all boundary vertices 
            incident to the outerFace. 
        numPasses: maximum number of iterations to perform. Default is 1000.
        tolerance: the tolerance for which the average_error must fall below
    Raises:
        PackingError if there are no vertices to repack. 
        
    Returns:
        (dcel, loopCount) where dcel is a new dcel with the packing data stored on the vertices, 
        and loopCount is the number of iterations performed before the packing  procedure hit an 
        average error below the tolerance.
    """
    global _REPACK_DEBUG
    
    # Which vertices to repack? 
    repack_verts = [v for v in dcel.verts if v.aim > 0]
    
    if len(repack_verts) == 0:
        raise PackingError("Nothing to repack (all boundary vertices).")
    
    # Get the initial angleSum and error:
    for v in repack_verts: 
        v.angleSum = _angleSumFor(v)
        v.angleSumError = v.angleSum - v.aim
    
    loopIdx = 0
    recip_repack_v_len = 1.0 / len(repack_verts)
    average_error = sum([abs(v.angleSumError) for v in repack_verts]) * recip_repack_v_len
    
    while loopIdx < num_passes and average_error > tolerance:
        if _REPACK_DEBUG:
            print(f"Starting repack pass {loopIdx}.")
        # Loop over all non boundary vertices
        for v in repack_verts:
            # Compute the current angle sum and error for the vertex. 
            v.angleSum = _angleSumFor(v)
            v.angleSumError = v.angleSum - v.aim # aim is TWO_PI if non-boundary, o/w its -1
            
            # If the error is greater than the average error, then compute a new radius
            # for the vertex and update its angle sum and angle sum error. 
            if abs(v.angleSumError) >= average_error - tolerance:
                v.data[1] = _newRadiusEstimate(v, v.data[1], v.aim, 5)
                v.angleSum = _angleSumFor(v)
                v.angleSumError = v.angleSum - v.aim
        
        # Compute the average error on the vertices and update the loopIdx
        average_error = sum([abs(v.angleSumError) for v in repack_verts]) * recip_repack_v_len
        loopIdx += 1
        
    return dcel, loopIdx

def _place_circles(dcel: DCEL, centerDartIdx: int) -> None:
    """Computes and stores the centers for each vertex in dcel. 
    
    Args:
        dcel: A DCEL that is a triangulated disk with each Vertex's .data field set to [ctr, rad] where rad is the radius for the circle at that vertex in a computed packing label and ctr is a dummy tuple to be replaced by this computation.
        centerDartIdx: The index of the dart to place at the origin of the disk. The dart's .origin vertex is placed directly on the origin and the dart's .dest vertex is placed along the positive x-axis. This must not be a boundary dart. 

    Raises:
        PackingError if all vertices are incident to the outer face or if the selected dart at index centerDartIdx is a boundary dart. 
    """
    if centerDartIdx < 0:
        # Then we need to find a dart that is not a boundary dart. 
        center_dart = None
        for v in dcel.verts:
            if v.aim > 0:
                center_dart = v.outDarts()[0]
                break
        if center_dart == None:
            raise PackingError("All vertices are incident to the outer face.")
    else:
        # First place the dart at index centerDartIdx at the origin with
        # destination sitting on the positive x-axis. 
        center_dart = dcel.darts[centerDartIdx]
        if center_dart.origin.aim < 0:
            raise PackingError("Can't start layout from a horocycle. Select a vertex of finite radius to center at the origin.")
            
    _place_dart_at_origin(center_dart)
    
    # BFS the dual graph of the dcel to place each face
    # in our BFS queue we add the dart incident to an unplaced face
    # with the invariant that each dart in the queue has already had
    # both its origin and destination placed. Therefore the only 
    # remaining vertex to place is dart.next.dest. This may have already 
    # been placed, of course, so we need to keep track of both what
    # faces we have visited and what vertices we have placed. 
    for vert in dcel.verts:
        vert._is_placed = False
    center_dart.origin._is_placed = True
    for face in dcel.faces:
        face._visited = False
    dcel.outerFace._visited = True # We do not want to try to place the outer face. 
    
    Q = deque([center_dart])
    if center_dart.twin.face != dcel.outerFace:
        Q.append(center_dart.twin)
    
    while len(Q) > 0:
        next_dart = Q.popleft()
        vertex_to_place = next_dart.next.dest
        if not vertex_to_place._is_placed:
            vertex_to_place.data = _compute_center(next_dart.origin.data[0], 
                                                   next_dart.dest.data[0], 
                                                   next_dart.origin.data[1], 
                                                   next_dart.dest.data[1],
                                                   vertex_to_place.data[1])
            vertex_to_place.placing_dart = next_dart
            vertex_to_place._is_placed = True
            #TODO We could here compute the maximum error in placement by how different the
            #     _compute_center is placing on subsequent calls. For now, I'm just placing each
            #     circle once and only once. 
        next_dart.face._visited = True
        for dart in [next_dart.next, next_dart.prev]:
            if not dart.twin.face._visited:
                Q.append(dart.twin)
    

def maximalPacking(diskDcel: DCEL, num_passes: int = 1000, tolerance: float = 3e-10, centerDartIdx: int = -1) -> (DCEL, int):
    """Computes a hyperbolic maximal packing of the given DCEL. 
    
    This function assumes that the DCEL is a triangulated disk with the boundary given
    by the vertices and darts incident to diskDcel.outerFace. 
    
    Args:
        diskDcel: The input DCEL. Should be a triangulated disk with all boundary vertices 
            incident to the outerFace. 
        numPasses: maximum number of iterations to perform. Default is 1000.
        tolerance: 
    Returns:
        A tuple (dcel, loopCount) where dcel is a new DCEL structure where each vertex 
        stores a list [z, r] as its .data object where z is a complex specifying the 
        center of the circle for the vertex and r is its radius; and loopCount is the
        number of iterations performed before the packing procedure hit an average error
        below the tolerance.
    """
    TWO_PI = 2.0 * math.pi
    # Following the convention in CirclePack we will store at each vertex a pair [c, r] where c
    # is the complex number for the center of the circle and r is the radius. If r is positive than 
    # the radius is finite, and the euclidean radius is gi ven by x = 1 - exp(-2r). If r is negative
    # then the circle is a horocycle (infinite radius) and the euclidean radius is -r
    dcel = diskDcel.duplicate(
                vdata_transform = (lambda v : [0j, 1]), # centered at 0j with radius 1
                edata_transform = (lambda e : None),
                fdata_transform = (lambda f : None)
             )
    
    bdryVerts = set(dcel.outerFace.vertices())
    
    # From PackData.set_aim_default():
    for v in dcel.verts:
        v.data = [0j, 0.5]
        v.aim = TWO_PI
    for b in bdryVerts:
        b.data = [0j, -5]
        b.aim = -1.0
    
    repack_iterations = repack(dcel, num_passes, tolerance)
    _place_circles(dcel, centerDartIdx)
    
    # Finally, let's convert the ((x+iy), r) data to CircleH2 types
    for v in dcel.verts:
        data = v.data
        v.data = CircleH2(PointH2(data[0]), data[1])
    
    return dcel, repack_iterations

def _set_center(v: Vertex, z: complex) -> None:
    """Sets the center data of vertex v.
    
    Args: 
        v: The Vertex to set the .data[0] on. 
        z: The new center. 
    """
    absz = abs(z)
    if (absz > 1.0):
        v.data[0] = z * (1.0 / absz)
    else:
        v.data[0] = z
        
def _set_radius(v: Vertex, rad: float) -> None:
    """Sets the radius data of Vertex v.
    
    Args:
        v: The Vertex to set the radius data on. 
        rad: The hypberolic radius to set. (Note: will be stored as an x-radius.)
    """
    # converts rad from hyperbolic radius to x-radius. 
    if rad > 0.0:
        v.data[1] = (1 - math.exp(-2.0 * rad) 
                     if rad > 1e-4 
                     else 2.0 * rad * (1.0 - rad * (1.0 - 2.0 * rad / 3.0)))
    elif rad <= 0.0:
        v.data[1] = rad

def _place_dart_at_origin(aDart: Dart) -> complex:
    """Places the origin of aDart at the origin and the destination along the positive x-axis.
    
    Assumes that the origin of aDart does not have infinite radius. 
    
    Args:
        aDart: The dart to lay down starting at the origin along the positive x-axis. 
    
    """
    a = aDart.origin
    k = aDart.next.origin
    
    x1 = a.data[1]
    x2 = k.data[1]
    s1 = _x_to_s_rad(x1)
    s2 = _x_to_s_rad(x2)
    
    _set_center(a, 0j)
    
    if s2 <= 0: # If the second has infinite radius
        _set_center(k, complex(1,0))
        erad = x1 / ((1.0 + s1) * (1.0 + s1))
        _set_radius(k, -1.0 * (1.0 - erad * erad) / (2.0 + 2.0 * erad))
    else:
        x12 = x1 * x2
        x1p2 = x1 + x2
        s12 = s1 * s2
        x = (x1p2 - x12) / (s12 * (1 + s12)) - (2 * x1p2 - 2 * x12) / (4 * s12)
        s = x + math.sqrt(x * (x + 2))
        _set_center(k, (1+0j)*s / (s + 2))

# (a - z) / (1 - z * conj(a))
# = (-z + a) / (-z * conj(a) + 1)
# Mobius.mob_trans in CirclePack
def _mob_trans(z: complex, a: complex) -> complex: 
    """Convenience function for applying a mobius transformation that fixes the disk to a complex number z.
    
    Args:
        z: The complex number to apply the Mobius transformation to. 
        a: The parameter for the transformation. 
    
    Returns: 
        (-z + a) / (-z * conjugate(a) + 1)
    """
    return (complex(-1, 0)*z + a)/(-a.conjugate()*z+complex(1,0))

# Mobius.mobDiscInvValue in CirclePack
def _mobDiskInvValue(w: complex, a: complex, b: complex) -> complex:
    """Convenience routine: computes the preimage of w under mobius transformation of the disk that
    maps a to zero and b to the positive x-axis. 
    
    Args:
        w: The point to invert.
        a: the point to send to 0. 
        b: the point to place on the positive x-axis. 
    
    Returns:
        The preimage of w under the appropriate Mobius transformation.
    """
    global MOB_TOLER
    z = _mob_trans(b, a)
    # Check if b is very close to a:
    c = abs(z)
    if c < MOB_TOLER:
        return a
    else:
        z = z * (1.0 / c)
        return _mob_trans(z * w, a)

def _eucl_circle_3(z1: complex, z2: complex, z3: complex) -> (complex, float):
    """Find the euclidean center/radius for circle through 3 points in the euclidean plane.
    
    Args:
        z1: complex  
        z2: complex 
        z3: complex
    Returns:
        A tuple (c, r) where c is the euclidean center and r is the euclidean radius of the
        circle passing through z1, z2, and z3. 
    """
    
    a1 = z2.real - z1.real
    a2 = z3.real - z2.real
    b1 = z2.imag - z1.imag
    b2 = z3.imag - z2.imag
    det = 2.0 * (a1 * b2 - b1 * a2)
    
    if (abs(det) < 1e-13):
        raise PackingError("Circle has 0 radius.")
    
    dum = abs(z2)
    dum = dum * dum
    
    c1 = abs(z1)
    c1 = (-c1 * c1)
    c1 += dum
    
    c2 = abs(z3)
    c2 = c2 * c2
    c2 -= dum
    
    c_real = (b2 * c1 - b1 * c2) / det
    c_imag = (a1 * c2 - a2 * c1) / det
    c_rad = math.sqrt((c_real-z1.real)*(c_real-z1.real)+(c_imag-z1.imag)*(c_imag-z1.imag))
    return (complex(c_real, c_imag), c_rad)
    
# HyperbolicMath.h_compcenter in CirclePack
def _compute_center(z1: complex, z2: complex, x1: float, x2: float, x3:float) -> (complex, float):
    """Computes the Poincare disk center of a circle given its two tangent neighbors. 
    
    Places the circle in counterclockwise orientation from the first two. 
    
    Args:
        z1: The hyperbolic center of circle 1 given as a point in the Poincare disk. 
        z2: The hyperbolic center of circle 2 given as a point in the Poincare disk. 
        x1: The x-radius of circle 1. 
        x2: The x-radius of circle 2. 
        x3: The x-radius of the circle to place. 
    
    Returns:
        A tuple (ctr, rad) where ctr is the center of the third circle given as a point in the Poincare disk and rad is the x-radius of the point. 
    """
    # Hack for now. We need to run a pylint to find the type bugs
#     if isinstance(z1, complex):
#         z1 = ExtendedComplex(z1)
    
#     if isinstance(z2, complex):
#         z2 = ExtendedComplex(z2)
    
    s1, s2, s3 = _x_to_s_rad(x1), _x_to_s_rad(x2), _x_to_s_rad(x3)
    sgn = 1.0
    
    if s1 <= -1.0 or s2 <= -1.0:
        raise PackingError("error in computing center: horocycle radius <= -1.0")
    
    a = z1
    b = z2
    
    if s1 <= 0 and s2 > 0: # if the second circle is finite but first infinite:
        # switch order. 
        a, b, s1, s2, x1, x2 = z2, z1, s2, s1, x2, x1
        sgn = -1.0
    if s1 > 0:
        cc = _cosFaceAngle(x1, x2, x3)
        
        if s3 > 0: # third circle is finite
            x13 = x1 * x3
            x1p3 = x1 + x3
            s13 = s1 * s3
            acstuff = (x1p3 - x13) / (s13 * (1 + s13)) - (2 * x1p3 - 2 * x13) / (4 * s13)
            side_p1 = acstuff + math.sqrt(acstuff * (acstuff + 2))
            ahc = side_p1 / (side_p1 + 2) # abs value of hyp center
            #center as if z1 is at the origin. 
            if a == b:
                z3 = complex(cc*ahc*ahc, sgn*math.sqrt(1-cc*cc)*ahc)
            else:
                z3 = complex(cc*ahc, sgn*math.sqrt(1-cc*cc)*ahc)
            z3 = _mobDiskInvValue(z3, a, b) # move to the right place
            return (z3, x3)
        else: 
            r = (1 - s1) / (1 + s1)
            sc = (r * r + 1 + 2 * r) / (2 * (1 + r))
            cc2 = cc * cc
            c = complex(sc * cc, sc * sgn * math.sqrt(1-cc2))
            rad = 1 - sc
            w1 = c - rad
            w2 = c + rad
            w3 = c + rad*1j
            w1 = _mobDiskInvValue(w1, a, b)
            w2 = _mobDiskInvValue(w2, a, b)
            w3 = _mobDiskInvValue(w3, a, b)
            ctr, rad = _eucl_circle_3(w1, w2, w3)
            return (ctr * (1.0 / abs(ctr)), -rad)
    elif s3 > 0: # first two horocycles, third infinite
        erad = (1.0 - s3) / (1.0 + s3)
        hororad = (1.0 - erad * erad) / (2.0 * (1 + erad))
        dist12 = math.sqrt(2*hororad*hororad)
        d = 1.0 - hororad
        theta = math.acos((2.0*d*d - dist12*dist12)/(2.0*d*d))
        
        d1 = 1.0 - 2.0 * hororad
        d2 = 1.0 + 2.0 * s1
        
        t = (d2 - d1) / (d2 * d1 - 1.0)
        newZ = -t / 1;
        theta = cmath.phase((theta * 1j - t) / (-t * theta * 1j + 1))
        #ExtendedComplex(complex(0,theta)).apply(1, -t, -t, 1).arg()
        origTheta = (z2 / z1).arg()
        t = (math.sin(theta) / (1.0 - math.cos(theta)) 
             - math.sin(origTheta) / (1.0 - math.cos(origTheta)))
        nextZ = (complex(2,t)*newZ + complex(0,-t))/(complex(0,t)*newZ+complex(2,-t))
#         newZ.applyMobius(
#             ExtendedComplex(complex(2,t)), 
#             ExtendedComplex(complex(0,-t)), 
#             ExtendedComplex(complex(0,t)), 
#             ExtendedComplex(complex(2,-t))
#         )
        return (nextZ * z1, x3)
    else:
        return _h_horo_center(z1, z2, -s2, 1, 1, 1)
    

class MobiusError(Exception):
    pass

@dataclass(frozen=True)
class Mobius:
    
    __slots__ = ['a', 'b', 'c', 'd']
    
    a: complex
    b: complex
    c: complex
    d: complex
        
    @classmethod
    def transformToZeroOneInfinity(cls, z1: complex, z2: complex, z3: complex) -> "Mobius":
        z2mz3 = z2 - z3
        z2mz1 = z2 - z1
        return cls(z2mz3, -z1*z2mz3, z2mz1, -z3*z2mz1)
    
    def apply(self, z: complex, *zs: complex) -> Union[complex, List[complex]]:
        if len(zs) == 0:
            return (self.a * z + self.b) / (self.c * z + self.d)
        else:
            return ([(self.a * z + self.b) / (self.c * z + self.d)]
                    + [(self.a * w + self.b) / (self.c * w + self.d) for w in zs])
      
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
                                        a: complex, b: complex, 
                                        A: complex, B: complex, 
                                        c: complex, C: complex) -> "Mobius":
        MOB_TOLER = 1e-12

        if not (_onDisk(a) and _onDisk(b) and _onDisk(A) and _onDisk(B)):
            raise MobiusError("One of a, b, A, or B is not on the unit circle.")
        
        if abs(a - b) < MOB_TOLER or abs(A - B) < MOB_TOLER:
            return Mobius(A / a, complex(0,0), complex(1,0), complex(0,0)).normalize()
        else:
            if abs(c) > 1.001 or abs(C) > 1.001:
                # Value is outside the disc so default to zero
                c = complex(0,0)
                C = complex(0,0)
            
            M1 = Mobius.normalize_abc(a, b, c)
            M2 = Mobius.normalize_abc(A, B, C)
            
            mob = M2.inverse * M1
            return mob.normalize()
        
    # from Mobius.norm_abc in CirclePack (Ken Stephenson)
    @classmethod
    def normalize_abc(cls, a: complex, b: complex, c: complex) -> "Mobius":
        
        MOD1 = .99999999
        MOB_TOLER = 1e-12
        
        if not _onDisk(a) or not _onDisk(b) or _outsideDisk(c):
            raise MobiusError("Either a or b are not on the disk or c is outside the disk.")

        A = a * abs(a)
        B = b * abs(b)
        
        R = Mobius(coplex(1,0), A, -complex(1,0), A)
        img = R.apply(B)
        
        T = Mobius(complex(1,0), complex(0, -img.imag), 
                   complex(0,0), complex(1,0))
        
        M = T * R
        
        M = M.scale(M.apply(c).reciprocal)
        
        W = Mobius(complex(1,0), -complex(1,0), complex(1,0), complex(1,0))
        
        return W * M
        
# Comment from Ken's code: 
# TODO: some confusion on what this does and whether there's an error.
# All three circles are horocycles, so centers z1, z2 should be on 
# unit circle. Idea is to compute data for third circle. Third center
# should be on unit circle, radius returned should be the negative of its
# euclidean radius. e2 is positive euclidean radius of circle 2. (??) 
# Inversive distances passed as usual (oj = inv_dist between edge opposite j). 
# HyperbolicMath.h_horo_center in CirclePack
def _h_horo_center(z1: complex, z2: complex, e2: float, o1: float, o2: float, o3: float):
    """Computes the center of the horocycle incident to two other horocycles.
    
    Note (John): This seems overly complicated since by the time this is used in the layout
    code we already know the euclidean radii for horocycles with centers z1 and z2, so we could
    just pass those radii in and do all of this in euclidean land, I think. 
    
    Args:
        z1: The center of horocycle 1. 
        z2: The center of horocycle 2. 
        e2: The euclidean radius of horocycle 2. 
        o1: The inversive distance between 2 and 3. 
        o2: The inversive distance between 1 and 3. 
        o3: The inversive distance between 1 and 2. 

    Returns:
        (c, r) where c is the hyperbolic center of horocycle 3 and r is the negative of the
        euclidean radius. 
    """
    if (z1.real * z1.real + z1.imag * z1.imag < .999999999999
        or z2.real * z2.real + z2.imag * z2.imag < .999999999999):
        raise PackingError("z1 or z2 are too far from the unit circle to be accurate")

    # Original comment from Ken's code: 
    # Don't follow some of this: third circle is supposed to be a horocycle,
    # so s-rad should be zero. Let's assume that (don't need x_rad3, which
    # used to be passed in here as an argument).  
    #         double S3=HyperbolicMath.x_to_s_rad(x_rad3);

    #         if (S3<=0) srad2=0.0;
    #         else srad2=(S3)*(S3);
        
    srad2 = 0.0
    R = 2 / (o3 + 3.0)
    d = math.sqrt(0.25 + R * R + R * o3)
    r = ((2.0 * (d + R * o3) + 1.0) * (1.0 - srad2)
        / (8.0 * d * (1.0 + srad2) + ((2.0 - 4.0 * d) * o1 - 4.0 * R * o2) * (srad2 - 1.0)))
    a_sq = 0.25 + r * (r + o1)
    ectr_real = (0.5 * (1 - d) 
                 - (1.0 / (2.0 * d)) 
                 * (0.25 + r * o1 - R * R - 2.0 * R * r * o2))
    ectr = complex(ectr_real, math.sqrt(a_sq - (ectr_real-0.5)*(ectr_real-0.5)))

    # Find 3 points on the original second circle (this is where e2 is used)
    ecent = (1.0 - e2) * z2
    
    p1 = ecent + complex(0, e2)
    p2 = complex(ecent.imag, ecent.real + e2)
    p3 = complex(ecent.imag, ecent.real - e2)

    One = complex(1,0)
    negOne = -One
    Two = complex(2, 0)
    
    M1 = Mobius.transformForTwoPointsOnUnitDisk(z1, z2, negOne, One, Two, Two)
    
    w1, w2, w3 = M1.apply(p1, p2, p3)
    
    tc = _eucl_circle_3(w1, w2, w3)
    rad = tc[1]
    pp = (1.0 - 2*rad)
    
    M2 = Mobius(One, complex(-pp, 0.0), complex(-pp, 0.0), One)
    
    w1, w2, w3 = M2.apply(w1, w2, w3)
    
    tc = _eucl_circle_3(w1, w2, w3)
    rad = tc[1]
    
    h = abs(ectr)
    
    if h > 1e-14:
        p1 = ectr * ((h + r) / h)
        p2 = ectr * ((h - r) / h)
        p3 = ectr + complex(r, 0)
    else:
        p1 = ectr + complex(-r, 0)
        p2 = ectr + complex( r, 0)
        p3 = ectr + complex( 0,-r)
    
    m1 = M1.inverse()
    m2 = M2.inverse()
    
    p1, p2, p3 = m1.apply(*m2.apply(p1, p2, p3))
    
    tc = _eucl_circle_3(p1, p2, p3)
    rad = tc[1]
    
    return (p1, -rad)
#
# RADIUS REPRESENTATION CONVERSIONS
#
# x radius appears to be the way radii are stored in the algorithms above
# s radius is the sqrt(1 - x)
# h is the normal hyperbolic radius that people are used to, which is related to x by
#   x = 1 - exp(-2h)
#
def _h_to_x_rad(h: float) -> float:
    return 1 - math.exp(-2.0 * h)

def _s_to_x_rad(s: float) -> float:
    return s if s <= 0.0 else (1.0 - s * s)

def _x_to_s_rad(x: float) -> float:
    return x if x <= 0.0 else math.sqrt(1.0 - x)

def _x_to_h_rad(x: float) -> float:
    if x > 0.0:
        if x > 1e-4:
            return -0.5 * math.log(1.0 - x)
        else:
            return x * (1.0 + x * (0.5 + x / 3.0)) / 2.0
    else:
        return x

def hyperbolic_circle_to_euclidean(h_center: complex, x_rad: float) -> (complex, float):
    s_rad = _x_to_s_rad(x_rad)
    if (s_rad <= 0.0): # infinite hyperbolic radius (usually negative of euclidean radius)
        a = 1.0 + s_rad
        e_center = h_center * a
        e_rad = -s_rad # assumes -s_rad is meaningful
    else: 
        ahc = abs(h_center)
        n1 = (1.0 + s_rad) * (1.0 + s_rad)
        n2 = n1 - ahc * ahc * x_rad * x_rad / n1
        e_rad = abs(x_rad * (1.0 - ahc * ahc) / n2) # can be <0 due to numerical error
        b = 4 * s_rad / n2
        e_center = b * h_center
    return (e_center, e_rad)

def euclidean_circle_to_hyperbolic(e_center: complex, e_rad: float) -> (complex, float):
    aec = abs(e_center)
    dist = aec + e_rad
    if dist > 1 + 1e-12: # Not in the unit disc, push inwards to be a horocycle
        aec /= dist
        e_rad /= dist
        dist = 1.0
    if 0.999999999999 < dist: # horocycle
        x_rad = (-e_rad)
        h_center = e_center * (1.0 / aec)
    else:
        c2 = aec * aec
        r2 = e_rad * e_rad
        if aec < 1e-13: # at the origin
            h_center = complex(0,0)
        else:
            b = math.sqrt((1.0 + 2.0*aec + c2 - r2) / (1.0 - 2.0 * aec + c2 - r2))
            ahc = (b - 1) / (b + 1)
            b = ahc / aec
            h_center = e_center * b
        x_rad = _s_to_x_rad(math.sqrt((1 - 2.0 * e_rad + r2 - c2) / (1.0 + 2.0 * e_rad + r2 - c2)))
    return (h_center, x_rad)