from koebe.geometries.euclidean2 import PointE2
import numpy as np
import math

def tutteEmbeddingE2(graphDCEL, in_place = False):
    """Computes a Tutte embedding of a graph. The vertices incident to graphDCEL.outerFace
    are evenly spaced along the unit circle. The locations of the vertices are given as PointE2 objects.
    
    Args:
        graphDCEL: The graph to embed. It should be topologically a disk. The outer face is placed in convex position.
        in_place: Defaults to False. If set to True, then the graphDCEL object is not duplicated before embedding, and
            and the vertex data for each vertex is replaced with Euclidean points for the embedding.
    Returns:
        A DCEL with vertex data set to the point locations for the Tutte embedding. If in_place is False, the combinatorics
        are a duplicate of the input graphDCEL. Otherwise, it simply returns a handle to graphDCEL. 
    """
    if not in_place:
        graph = graphDCEL.duplicate()
    else:
        graph = graphDCEL
    
    graph.reorderVerticesByBoundaryFirst()

    boundaryVerts = graph.boundaryVerts()

    k = len(boundaryVerts)
    
    boundaryCoords = [[math.cos(theta), math.sin(theta)]
                      for theta in [i * 2 * math.pi / k for i in range(k)]]

    L = np.matrix(graph.laplacian())
    P1 = np.matrix(boundaryCoords)
    L1 = L[0:k,0:k]
    B = L[k:,0:k]
    L2 = L[k:,k:]
    P2 = -np.linalg.inv(L2)*B*P1
    P = np.concatenate((P1, P2))

    for i in range(len(graph.verts)):
        graph.verts[i].data = PointE2(P[i,0],P[i,1])
    
    return graph