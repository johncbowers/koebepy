from typing import List

from .sampling import *

import random
import math

def _distSq(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return dx * dx + dy * dy

def slowAdaptiveDartThrowing(radius_function, stop_count: int = 100, initial_samples = []):
    
    samples = initial_samples
    
    fail_count = 0
    while fail_count < stop_count: 
        x, y = random.random(), random.random()
        r = radius_function(x, y)
        for sx, sy, sr in samples:
            rad = max(sr, r)
            if _distSq(x, y, sx, sy) <= rad * rad:
                fail_count += 1
                break
        else:
            fail_count = 0
            samples.append((x,y,r))
        
    return samples

def slowAdaptiveDartThrowingWithBoundary(radius_function, stop_count: int = 100):
    
    # First do a 1D circular sampling
    samples = []
    
    fail_count = 0
    while fail_count < stop_count:
        s = random.random() * 4
        
        x, y = ((s, 0) if s <= 1.0 
                else (1, s - 1) if s <= 2.0
                else (3 - s, 1) if s <= 3.0
                else (0, 4 - s))
        r = radius_function(x, y)
        
        for sx, sy, sr in samples:
            rad = max(sr, r)
            if _distSq(x, y, sx, sy) <= rad * rad:
                fail_count += 1
                break
        else:
            fail_count = 0
            samples.append((x, y, r))
    
    return slowAdaptiveDartThrowing(radius_function, stop_count, samples)

def slowUniformDartThrowing(radius: float, stop_count: int = 500, initial_samples = []):
    
    samples = initial_samples
    radiusSq = radius * radius
    
    fail_count = 0
    while fail_count < stop_count:
        x, y = random.random(), random.random()
        for sx, sy in samples:
            if _distSq(x, y, sx, sy) <= radiusSq:
                fail_count += 1
                break
        else:
            fail_count = 0
            samples.append((x, y))
    
    return samples

def slowUniformDartThrowingWithBoundary(radius: float, stop_count: int = 500):
    
    # First do a 1D circular sampling
    samples = []
    radiusSq = radius * radius
    
    fail_count = 0
    while fail_count < stop_count:
        s = random.random() * 4
        
        x, y = ((s, 0) if s <= 1.0 
                else (1, s - 1) if s <= 2.0
                else (3 - s, 1) if s <= 3.0
                else (0, 4 - s))
        
        for sx, sy in samples:
            if _distSq(x, y, sx, sy) <= radiusSq:
                fail_count += 1
                break
        else:
            fail_count = 0
            samples.append((x, y))
    
    return slowUniformDartThrowing(radius, stop_count, samples)

def slowAmbientSurfaceSampling(dcel, 
                               radius: float = None, 
                               stop_count: int = 500, 
                               initial_samples = [],
                               reject_function = None, 
                               face_weight_function = faceAreaE3, 
                               face_sampling_function = uniformTriangleSampleE3):
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
        A list of sample points. 
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
        tri_idx = binarySearch(areaAccSum, tri_area)
        if tri_idx >= len(faces):
            tri_idx = len(faces) - 1
        # Compute a random point on the given triangle
        return face_sampling_function(faces[tri_idx])
    
    def defaultReject(s1, s2):
        return s1.distSqTo(s2) < radius * radius
    
    if reject_function == None:
        reject_function = defaultReject
    
    samples = initial_samples
    
    fail_count = 0
    while fail_count < stop_count:
        s = sample()
        for x in samples: 
            if reject_function(s, x):
                fail_count += 1
                break
        else:
            fail_count = 0
            samples.append(s)
    return samples

def slowAmbientBoundarySampling(face, 
                                radius: float = None, 
                                stop_count: int = 500, 
                                reject_function = None, 
                                dart_weight_function = dartLengthE3, 
                                dart_sampling_function = uniformDartSampleE3):
    
    darts = face.darts()
    lengths = [dart_weight_function(d) for d in darts]
    
    totalLength = sum(lengths)
    lengthAccSum = [0] + list(itertools.accumulate(lengths))
    
    def sample():
        dart_length = random.random() * totalLength
        dart_idx = binarySearch(lengthAccSum, dart_length)
        if dart_idx >= len(darts):
            dart_idx = len(darts) - 1
        return dart_sampling_function(darts[dart_idx])
        
    def defaultReject(s1, s2):
        return s1.distSqTo(s2) < radius * radius
    
    if reject_function == None:
        reject_function = defaultReject
        
    samples = []
    
    fail_count = 0
    while fail_count < stop_count:
        s = sample()
        for x in samples: 
            if reject_function(s, x):
                fail_count += 1
                break
        else:
            fail_count = 0
            samples.append(s)
    return samples