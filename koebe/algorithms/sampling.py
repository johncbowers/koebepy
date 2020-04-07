
from koebe.geometries.euclidean3 import PointE3

from koebe.datastructures.dcel import DCEL

import itertools
import random
import math

def faceAreaE3(face):
    """Computes the area of a triangular DCEL face with vertex coordinates given
    as PointE3 objects.
    
    Args:
        face: A triangular face of a DCEL with vertex .data given by PointE3 objects. 
        
    Returns:
        The area of the triangular face. 
    """
    
    p0, p1, p2 = [v.data for v in face.vertices()]
    
    v0 = p1 - p0
    v1 = p2 - p0
    
    return v0.cross(v1).norm() * 0.5

def uniformTriangleSampleE3(face):
    """Computes a uniform sample of a triangular face.
    
    Args:
        face: A DCEL face with three vertices, each containing a PointE3. 
    
    Returns:
        A PointE3 on the face taken uniformly at random.
    """
    r1, r2 = random.random(), random.random()
    sqrtR1 = math.sqrt(r1)
    v0, v1, v2 = [v.data - PointE3.O for v in face.vertices()]
    return ((1 - sqrtR1) * v0 + sqrtR1 * (1 - r2) * v1 + sqrtR1 * r2 * v2).toPointE3()

def binarySearch(A, x):
    low, high = 0, len(A) - 1
    while low <= high:
        mid = int((high + low) / 2)
        if A[mid] >= x:
            high = mid - 1
        else:
            low = mid + 1
    return low

def weightedIndexSampling1D(rho, n):
    """Samples in range(0,len(rho)) where the probability that a given index i is drawn is rho[i] / sum(rho)
    
    Args:
        rho: (List[float]) A density function defined over the indices where each rho[i] > 0 and rho[i] represents the density at index i. 
        n: int The number of samples to draw. 
    """
    acc = [0] + list(itertools.accumulate(rho))
    samples = [binarySearch(acc, random.random() * acc[-1]) - 1 for _ in range(n)]
    return samples

def weightedIndexSampling2D(rho, n):
    """Samples the index set (i, j) of indices into the 2D list rho. The samples will be indices (i, j) into rho.
    
    Args:
        rho: (List[List[float]]) A 2D density function defined over the indices where each rho[i][j] > 0 and rho[i][j] represents the density at index (i, j). 
        n: int The number of samples to draw. 
    """
    indices = [(i, j) for i in range(len(rho)) for j in range(len(rho[i]))]
    flattened_rho = [rho[i][j] for i, j in indices]
    flattened_samples = weightedIndexSampling1D(flattened_rho, n)
    samples = [indices[i] for i in flattened_samples]
    return samples

def weightedSubgridSampling2D(rho, n):
    """Samples a grid using a 2D density function rho. First each grid index (i, j) is drawn using the proportion of the 
    density at rho[i][j]. Then a uniform sample of that grid index (i + random.random(), j + random.random()) is selected.
    
    Args:
        rho: (List[List[float]]) A 2D density function defined over the indices where each rho[i][j] > 0 and rho[i][j] represents the density at index (i, j). 
        n: int The number of samples to draw. 
    """
    indices = weightedIndexSampling2D(rho, n)
    samples = [(i + random.random(), j + random.random()) for i, j in indices]
    return samples
    
def surfaceSampling(dcel, nsamples, face_weight_function = faceAreaE3, face_sampling_function = uniformTriangleSampleE3):
    """Computes a sampling of a DCEL. Faces are weighted using the face_weight_function and a 
    selected by a weighted sampling. Then a sample is drawn by running the face_sampling_function
    on the selected face. 
    
    The default is a triangulated DCEl with PointE3 objects stored at each vertex. The weight
    function is the area of the triangle. The face sampling function samples the triangle uniformly
    at random. 
    
    Args:
        dcel: A triangulated surface. 
        nsamples: The number of samples to draw. 
        face_weight_function: (Face) -> float. A function that computes the (positive) weight of a given face.
        face_sampling_function: (Face) -> Sample. A function that computes a sample of a given face. 
        
    Returns:
        A list of sample points given as a pair (point, face) where point is the point returned
        by the face_sampling_function and face is the Face of the triangle containing it. 
    """
    # Get the actual faces: 
    faces = [f for f in dcel.faces if dcel.outerFace != f]
    areas = [face_weight_function(f) for f in faces]
    
    # Get the accumulated sum of areas: 
    totalArea = sum(areas)
    areaAccSum = [0] + list(itertools.accumulate(areas))
    
    # The sample() function just computes a single sample
    def sample():
        # Select a random area from 0 to totalArea
        tri_area = random.random() * totalArea
        # Grab the triangle whose area contains tri_area in the sum
        tri_idx = binarySearch(areaAccSum, tri_area) - 1
        if tri_idx >= len(faces):
            tri_idx = len(faces) - 1
        # Compute a random point on the given triangle
        return face_sampling_function(faces[tri_idx])
    
    # Return as many samples as requested
    return [sample() for _ in range(nsamples)]
    

def dartLengthE3(dart):
    return dart.origin.data.distTo(dart.dest.data)

def uniformDartSampleE3(dart):
    t = random.random()
    v0 = dart.origin.data - PointE3.O
    v1 = dart.dest.data - PointE3.O
    return (t * v0 + (1 - t) * v1).toPointE3()

def boundarySampling(face, nsamples, dart_weight_function = dartLengthE3, dart_sampling_function = uniformDartSampleE3):
    
    darts = face.darts()
    lengths = [dart_weight_function(d) for d in darts]
    
    totalLength = sum(lengths)
    lengthAccSum = [0] + list(itertools.accumulate(lengths))
    
    def sample():
        dart_length = random.random() * totalLength
        dart_idx = binarySearch(lengthAccSum, dart_length) - 1
        if dart_idx >= len(darts):
            dart_idx = len(darts) - 1
        return dart_sampling_function(darts[dart_idx])
    
    return [sample() for _ in range(nsamples)]