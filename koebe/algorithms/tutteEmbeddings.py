from koebe.geometries.euclidean2 import PointE2

from scipy.sparse import coo_matrix
from scipy.sparse.linalg import inv
import numpy as np
import math

def sparse_laplacian(self):
    print("Creating vertToIdx array...")
    vertToIdx = dict((v, k) for k, v in enumerate(self.verts))
    print("Creating vertToDeg array...")
    vertToDeg = [len(v.outDarts()) for v in self.verts]
    print("Creating mat...")
    #mat = [[0 for _ in range(len(self.verts))] for _ in range(len(self.verts))]
    
    row_array = []
    col_array = []
    dat_array = []

    print("Done.")
    for i in range(len(self.verts)):
        u = self.verts[i]
        neighbors = u.neighbors()
        
        #mat[i][i] = len(neighbors)
        row_array.append(i)
        col_array.append(i)
        dat_array.append(len(neighbors))
        
        for v in neighbors:
            row_array.append(i)
            col_array.append(vertToIdx[v])
            dat_array.append(-1)
    
    print(f"Returning coo_matrix with shape ({len(self.verts)}, {len(self.verts)})")
    return coo_matrix((np.array(dat_array), (np.array(row_array), np.array(col_array))), shape=(len(self.verts), len(self.verts))).tocsc()

def tutteEmbeddingE2(graphDCEL, in_place = False, verbose = False):
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
        if verbose: print("Duplicating DCEL...")
        graph = graphDCEL.duplicate()
        if verbose: print("done.")
    else:
        graph = graphDCEL
    
    if verbose: print("Reordering vertices...")
    graph.reorderVerticesByBoundaryFirst()
    if verbose: print("done.")

    boundaryVerts = graph.boundaryVerts()

    k = len(boundaryVerts)
    
    if verbose: print("Laying out boundary...")
    boundaryCoords = [[math.cos(theta), math.sin(theta)]
                      for theta in [i * 2 * math.pi / k for i in range(k)]]
    if verbose: print("done.")
    
    if verbose: print("Computing graph laplacian...")
    L = sparse_laplacian(graph)
    if verbose: print("done.")

    if verbose: print("Computing Tutte embedding...")

    if verbose: print("Computing P1...")
    P1 = np.matrix(boundaryCoords)

    if verbose: print("Computing L1...")
    L1 = L[0:k, 0:k]

    if verbose: print("Computing B...")
    B = L[k:,0:k]

    if verbose: print("Computing L2...")
    L2 = L[k:,k:]

    if verbose: print("Computing -inv(L2)")
    nInvL2 = -inv(L2)

    if verbose: print("Computing nInvL2*B*P1")
    P2 = nInvL2*B*P1

    if verbose: print("Concatenating P1 and P2")
    P = np.concatenate((P1, P2))

    if verbose: print("done.")

    if verbose: print("Setting .data attributes...")
    for i in range(len(graph.verts)):
        if not in_place:
            graph.verts[i].data = PointE2(P[i,0],P[i,1])
        else:
            graph.verts[i].tutte_data = PointE2(P[i,0],P[i,1])
    if verbose: print("done.")
    return graph