"""

An implementation of O(n^2) ear clipping. 

WIP: An implementation of O(n log n) polygon triangulation using the monotone polygon subdivision algorithm. 

References; 
    de Berg, M., Cheong, O., van Kreveld, M., and Overmars, M.
    Computational Geometry Algorithms and Applications, 3rd ed.
    Springer-Verlag Berlin Heidelberg, 2008.
"""

from koebe.datastructures.dcel import *
from koebe.geometries.euclidean2 import PointE2, SegmentE2, PolygonE2
from koebe.geometries.commonOps import orientation2, Orientation

from typing import List


def leftHandTurn(p1: PointE2, p2: PointE2, p3: PointE2) -> bool:
    return (orientation2(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y) 
            == Orientation.POSITIVE)

def triangulateByEarClipping(dcelFace: Face):
    
    dcel  = dcelFace.dcel
    darts = dcelFace.darts()
    n     = len(darts)
    
    def definingPoints(dart: Dart) -> Tuple[PointE2]:
        return dart.prev.origin.data, dart.origin.data, dart.dest.data
    
    def triContains(dart: Dart, vert: Vertex) -> bool: 
        p1, p2, p3 = definingPoints(dart)
        p          = vert.data
        return (    leftHandTurn(p1, p2, p) 
                and leftHandTurn(p2, p3, p)
                and leftHandTurn(p3, p1, p))
    
    def isConvex(dart: Dart) -> bool:
        return leftHandTurn(*definingPoints(dart))
    
    def isReflex(dart: Dart) -> bool:
        return not leftHandTurn(*definingPoints(dart))
    
    #convex = set([dart for dart in darts if isConvex(dart)])
    reflex = set([dart for dart in darts if isReflex(dart)])
    
    def isEar(dart: Dart) -> bool:
        if isReflex(dart):
            return False
        isAnEar = True
        for r in reflex:
            if triContains(dart, r):
                isAnEar = False
                break
        return isAnEar
    
    ears = set([dart for dart in darts if isEar(dart)])
    
    for _ in range(n-3):
        anEar = ears.pop()
        
        newFace  = Face(dcel, aDart = anEar)
        newEdge  = Edge(dcel)
        newDart1 = Dart(dcel, 
                        edge = newEdge, 
                        origin = anEar.dest, 
                        face = newFace)
        newDart2 = Dart(dcel, 
                        edge = newEdge,
                        origin = anEar.prev.origin
                        face = dcelFace)
        newDart1.makeTwin(newDart2)
        newDart2.makeNext(anEar.next)
        newDart2.makePrev(anEar.prev.prev)
        newDart1.makeNext(anEar.prev)
        newDart1.makePrev(anEar)
        
        if anEar.prev in reflex: reflex.remove(anEar.prev)
        elif anEar.prev in ears: ears.remove(anEar.prev)
        
        if isReflex(newDart2): reflex.add(newDart2)
        elif isEar(newDart2): ears.add(newDart2)
        
        if isConvex(newDart2.next):
            if newDart2.next in reflex:
                reflex.remove(newDart2.next)
            if newDart2.next not in ears and isEar(newDart2.next):
                ears.add(newDart2.next)
        
    
from enum import Enum
from heapq import *

def below(p: PointE2, q: PointE2) -> bool:
    return p.y < q.y or (p.y == q.y and p.x > q.x)

def above(p: PointE2, q: PointE2) -> bool:
    return p.y > q.y or (p.y == q.y and p.x < q.x)

class VertexType(Enum):
    START = 0
    END = 1
    REGULAR = 2
    SPLIT = 3
    MERGE = 4
    
def vType(d: Dart) -> VertexType:
    if below(d.pred.data, d.origin.data) and below(d.dest.data, d.origin.data): 
        if leftHandTurn(d.pred.data, d.origin.data, d.dest.data):
            return VertexType.START
        else:
            return VertexType.SPLIT
    elif above(d.pred.data, d.origin.data) and above(d.dest.data, d.origin.data):
        if leftHandTurn(d.pred.data, d.origin.data, d.dest.data):
            return VertexType.END
        else:
            return VertexType.SPLIT
    else:
        return VertexType.REGULAR
    
def handleStartVertex(d, T, helper):
    helper[d] = d

def handleEndVertex(d, T, helper):
    if vType(helper[d]) == VertexType.MERGE:
        # Then insert a diagonal between d.origin and helper[d].origin
        pass
    # delete d from T


def makeMonotone(poly: DCEL):
    
    Q = [] # The vertex priority queue
    helper = {}
    
    for d in poly.faces[1].darts():
        # Heap is ordered on max y-coordinate (min x-coordinate to break ties.)
        heappush(Q, (-d.origin.data.y, d.origin.data.x, d)) 
    
    T = BST()
    
    while Q: # While Q is not empty.
        _, _, d = heappop(Q)
        vt = vType(d)
        if vt == VertexType.START:
            handleStartVertex(d, T, helper)
        elif vt == VertexType.END:
            handleEndVertex(d, T, helper)
        elif vt == VertexType.REGULAR:
            handleRegularVertex(d, T, helper)
        elif vt == VertexType.SPLIT:
            handleSplitVertex(d, T, helper)
        else:
            handleMergeVertex(d, T, helper)


        