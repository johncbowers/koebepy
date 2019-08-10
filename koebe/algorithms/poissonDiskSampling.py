from typing import List

import random

def _distSq(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return dx * dx + dy * dy

def slowUniformDartThrowing(radius: float, stop_count: int = 100, initial_samples = []):
    
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

def slowUniformDartThrowingWithBoundary(radius: float, stop_count: int = 100):
    
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