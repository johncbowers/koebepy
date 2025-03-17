
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

from math import *
from random import *

import numpy as np
from scipy.linalg import null_space
import scipy.optimize as opt
import scipy.linalg as la

from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle
from koebe.graphics.scenes.euclidean2scene import E2Scene

npoints = 30

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
blueStyle = makeStyle(stroke=(0,0,255), fill=(255, 0, 0), strokeWeight=2.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)

verbose = False

mouse_down = False
selected_idx = -1
closest_idx = -1
closest_dist = float('inf')
remove_zero_edges = False


def find_equilibrium_stress(R, pinned_vertices, interior_mask, tol=1e-10):
    """
    Compute a valid equilibrium stress vector given the unpinned rigidity matrix and pinned vertices.
    R: np.array (m x 2n) - Original unpinned rigidity matrix
    pinned_vertices: list of 3 integers - Indices of pinned vertices
    interior_mask: np.array (m,) - Boolean array where True indicates interior edges
    tol: float - Numerical tolerance for zeroing out small values
    Returns: np.array (m,) - A normalized equilibrium stress vector
    """
    
    # Compute the null space of R_pinned^T
    null_space = la.null_space(R.T, rcond=1e-10)
    
    if null_space.shape[1] == 0:
        raise ValueError("No non-trivial equilibrium stress found. Check rigidity matrix.")
    
    # Solve for an equilibrium stress where interior stresses are positive
    num_null_vectors = null_space.shape[1]
    c = np.zeros(num_null_vectors)  # Dummy objective function
    
    A_eq = np.ones((1, num_null_vectors))  # Ensure nontrivial solution
    b_eq = np.array([1])
    
    bounds = [(None, None) for _ in range(num_null_vectors)]  # Allow positive and negative values
    
    # Enforce positivity on interior edges
    A_ub = -null_space
    b_ub = np.zeros(A_ub.shape[0])
    for eIdx in range(len(interior_mask)):
        if not interior_mask[eIdx]:
            A_ub[eIdx, :] *= -1
            #b_ub[eIdx] = -1
    #A_ub = -null_space[interior_mask, :]
    
    res = opt.linprog(c, A_eq=A_eq, b_eq=b_eq, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    
    if not res.success:
        raise ValueError("Failed to find a positive equilibrium stress using linear programming.")
    
    # Construct equilibrium stress from the null space basis
    stress_vector = null_space @ res.x  # Linear combination of basis vectors
    
    # Zero out very small numerical values
    stress_vector[np.abs(stress_vector) < tol] = 0.0
    
    # Normalize the stress vector
    max_abs_stress = np.max(np.abs(stress_vector))
    if max_abs_stress > 0:
        stress_vector /= max_abs_stress
    
    return stress_vector

def rigidity_matrix(G, p):
    return np.array([
        np.array([
            tuple(p[e.j] - p[e.i]) if v == e.i 
            else tuple(p[e.i] - p[e.j]) if v == e.j 
            else (0, 0)
            for v in range(len(tutteGraph.verts))
        ]).flatten() for e in tutteGraph.edges
    ])
    
def create_random_tutte():
    global points, unscaled_points, tutteGraph, npoints
    print("Generating random convex hull of eight points and computing a Tutte embedding... ")
    poly = randomConvexHullE3(npoints) # Generate a random polyhedron with 16 vertices. 
    poly.outerFace = poly.faces[0] # Arbitrarily select an outer face. 
    tutteGraph = tutteEmbeddingE2(poly) # Compute the tutte embedding of the polyhedron. 
    print("\tdone.")
    
    xs = [v.data.x for v in tutteGraph.verts]
    ys = [v.data.y for v in tutteGraph.verts]

    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    extent = max(maxx-minx, maxy-miny)

    unscaled_points = [PointE2(v.data.x, v.data.y) for v in tutteGraph.verts]
    points = [PointE2(500*(v.data.x-minx)/extent -200, 500*(v.data.y-miny)/extent - 250) for v in tutteGraph.verts]

    tutteGraph.markIndices()
    refresh_points(points)


def refresh_points(new_points):
    global closest_idx, selected_idx, editor_scene, lifting_scene, points, unscaled_points, remove_zero_edges, verbose

    points = new_points

    R = rigidity_matrix(tutteGraph, points)
    # print(f"R is {R.shape}")
    # print(f"rank of R is {np.linalg.matrix_rank(R)}")
    # # ns = null_space(R.transpose())

    # edge_ids = [e.idx for e in tutteGraph.verts[10].edges()]
    # nbs = [v.idx for v in tutteGraph.verts[10].neighbors()]
    # stress_vecs = [(points[nbs[i]]-points[10])*ns[edge_ids[i]][3] for i in range(len(nbs))]
    # print(edge_ids)
    # print(nbs)
    # print(ns[0])
    # print(sum(stress_vecs, start=VectorE2(0,0)))

    edges = np.array(
        [
            [v.idx for v in e.endPoints()]
            for e in tutteGraph.edges
        ]
    )

    i, j, k = [v.idx for v in tutteGraph.outerFace.vertices()]
    interior_mask = [tutteGraph.outerFace not in e.incidentFaces() for e in tutteGraph.edges]
    
    try:
        stress = find_equilibrium_stress(R, [i, j, k], interior_mask)
    except Exception as e: 
        print(e)
        stress = np.array([0 for _ in tutteGraph.edges])
    # print((i, j, k))
    # print([e.idx for e in tutteGraph.outerFace.edges()])

    if verbose:
        print("stress: ")
        print(stress)
        print(R.T @ stress)
    # print(R.T.dot(stress))
    # ns[i] *= -1
    # ns[j] *= -1
    # ns[k] *= -1

    # result = linprog(c = [1 for _ in ns[0]], b_ub=[0 for _ in ns], A_ub=-ns, bounds=(-100, 100))
    
    # ns[i] *= -1
    # ns[j] *= -1
    # ns[k] *= -1

    # print((i, j, k))
    # print(ns)
    # print(result.x)
    # print(ns.dot(result.x))
    
    
    segs = [(SegmentE2(*[points[v.idx] for v in e.endPoints()]), 
             blueStyle if stress[e.idx] > 1e-14 else redStyle if stress[e.idx] < -1e-14 else blackStyle
             ) for e in tutteGraph.edges
            if abs(stress[e.idx]) >= 1e-14 or not remove_zero_edges
            ]
            
    editor_scene.clear()
    editor_scene.addAll(segs)
    editor_scene.addAll([
        (points[pIdx], redStyle if pIdx == selected_idx else blackStyle if closest_dist >= 225 or closest_idx != pIdx else blueStyle) for pIdx in range(len(new_points))
    ])

    pointsE3 = [PointE3(p.x, p.y, random()) for p in unscaled_points]

    segsE3 = [(SegmentE3(*[pointsE3[v.idx] for v in e.endPoints()]), blackStyle) for e in tutteGraph.edges
            if abs(stress[e.idx]) >= 1e-14 or not remove_zero_edges
            ]

#PointE2(500*(v.data.x-minx)/extent -200, 500*(v.data.y-miny)/extent - 250)
    lifting_scene.clear()
    lifting_scene.addAll(segsE3)
    
def mouse_pressed_handler(event):
    global mouse_down, closest_idx, closest_dist, selected_idx
    if closest_dist < 225:
        selected_idx = closest_idx
    mouse_down = True
    refresh_points(points)

def mouse_released_handler(event):
    global mouse_down, selected_idx
    mouse_down = False
    selected_idx = -1
    refresh_points(points)

def mouse_moved_handler(event):
    global points, mouse_down, closest_idx, closest_dist, selected_idx
    p = PointE2(event["x"], event["y"])
    distSqs = [p.distSqTo(q) for q in points]
    closest_dist = min(distSqs)
    closest_idx = distSqs.index(closest_dist)
    if selected_idx != -1:
        new_points = [points[pIdx] if pIdx != selected_idx else PointE2(event["x"], event["y"]) for pIdx in range(len(points))]
        closest_dist = 0
        refresh_points(new_points)
    else:
        refresh_points(points)

def key_pressed_handler(event):
    global remove_zero_edges
    if event["key"] == " ":
        create_random_tutte()
    elif event["key"] == "z":
        remove_zero_edges = not remove_zero_edges
        refresh_points(points)


editor_scene = E2Scene(title="Tutte Embedding Editor")
lifting_scene = S2Scene(title="Polyhedral Lifting")
lifting_scene.toggleSphere()

create_random_tutte()

editor_scene.set_mouse_pressed(mouse_pressed_handler)
editor_scene.set_mouse_released(mouse_released_handler)
editor_scene.set_mouse_moved(mouse_moved_handler)
editor_scene.set_mouse_dragged(mouse_moved_handler)

viewer.add_scene(editor_scene)
viewer.add_scene(lifting_scene)

viewer.run()
