
from koebe.geometries.minkowski21 import SpanM21, VectorM21
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

from math import *
from random import *
from collections import deque

import numpy as np
from scipy.linalg import null_space
import scipy.optimize as opt
import scipy.linalg as la

from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle
from koebe.graphics.scenes.euclidean2scene import E2Scene

npoints = 30
n_grid_points = 24

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
blueStyle = makeStyle(stroke=(0,0,255), fill=(0, 0, 255), strokeWeight=2.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)
grayStyle = makeStyle(stroke=(128,128,128), fill=(128, 128, 128), strokeWeight=0.5)

blackPtStyle = makeStyle(stroke=(0,0,0), fill=(0, 0, 0))
bluePtStyle = makeStyle(stroke=(0,0,255), fill=(0, 0, 255), strokeWeight=2.0)
redPtStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)
greenPtStyle = makeStyle(stroke=(0,255,0), fill=(0, 255, 0), strokeWeight=2.0)
grayPtStyle = makeStyle(stroke=(128,128,128), fill=(128, 128, 128), strokeWeight=2.0)
pinkPtStyle = makeStyle(stroke=(255, 0, 255), fill=(255, 0, 255), strokeWeight=2.0
                        )
verbose = False

mouse_down = False
selected_idx = -1
closest_idx = -1
closest_dist = float('inf')

scale = 200
points = new_points = [scale * p for p in 
                            [PointE2(1, 0), 
                             PointE2(0.5, math.sqrt(3)/2), 
                             PointE2(-0.5, math.sqrt(3)/2), 
                             PointE2(-1, 0), 
                             PointE2(-0.5, -math.sqrt(3)/2), 
                             PointE2(0.5,  -math.sqrt(3)/2), 
                             PointE2(0, 0.5), 
                             PointE2(0.5, 0)]
                        ]


def segmentE2ForLineOP2(l, r, scale):
    """
    Converts a span in the Minkowski (2,1) space into a line in the Klein model, but 
    represents this as a SegmentE2 so that it can be drawn.
    """
    unit_disk = DiskOP2(1, 0, 0, -(r*r))
    isect = unit_disk.intersectWithLineOP2(l)
    if len(isect) == 2:
        p, q = isect
        return SegmentE2(scale * p.toPointE2(), scale * q.toPointE2())
    else:
        return None
    
def ideal_angle_bisector(A, B, C):
    """
    Computes the angle bisector formed for two hyperbolic segments AB and BC with
    ideal endpoints A, B, and C.
    """
    a = A.dualSpanM21().intersectWithOP2()
    c = C.dualSpanM21().intersectWithOP2()

    P = a.intersectWithLineOP2(c)
    
    l = LineOP2.lineThrough(P, B.toPointOP2())

    return l


def scaled_lightvectors(ideal_points, p):
    return [(-1/wi.innerProductWith(p)) * wi for wi in ideal_points]

def iterate_f(ideal_points, p, n_iterations):
    betas = [p]
    for _ in range(n_iterations):
        betas.append((1/len(ideal_points)) * sum(scaled_lightvectors(ideal_points, betas[-1]), start=VectorM21(0,0,0)))
    return betas

def spanToHypLine(spanM21, scale):
    """
    Converts a span in the Minkowski (2,1) space into a line in the Klein model, but 
    represents this as a SegmentE2 so that it can be drawn.
    """
    l = spanM21.intersectWithOP2()
    unit_disk = DiskOP2(1, 0, 0, -1)
    isect = unit_disk.intersectWithLineOP2(l)
    if len(isect) == 2:
        p, q = isect
        return SegmentE2(scale * p.toPointE2(), scale * q.toPointE2())
    else:
        return None


def lineOP2toHypLine(l, scale):
    """
    Converts a span in the Minkowski (2,1) space into a line in the Klein model, but 
    represents this as a SegmentE2 so that it can be drawn.
    """
    unit_disk = DiskOP2(1, 0, 0, -1)
    isect = unit_disk.intersectWithLineOP2(l)
    if len(isect) == 2:
        p, q = isect
        return SegmentE2(scale * p.toPointE2(), scale * q.toPointE2())
    else:
        return None

def refresh_points(new_points):
    global closest_idx, selected_idx, editor_scene, lifting_scene, points, unscaled_points, remove_zero_edges, verbose, scale, xshift, yshift, extent, minx, miny

    points = new_points

    # normalize the first 6 points: 
    for i in range(6):
        points[i] = (scale/points[i].distTo(PointE2.O)) * points[i]

    # convert to minkowski space
    mink_points = [
        VectorM21.fromPointE2((1/scale) * p) 
        for p in points
    ]

    # set up grid
    grid_points = [PointE2.fromPolarCoordinates(0.9999, theta) for theta in [2*math.pi*i/n_grid_points for i in range(n_grid_points)]]
    mink_grid_points = [VectorM21.fromPointE2(p) for p in grid_points]

    # normalize p and q to the hyperboloid
    p = mink_points[6].normalize()
    q = mink_points[7].normalize()

    grid = [iterate_f(mink_points[:6], pt, 8) for pt in mink_grid_points]
    betaps = iterate_f(mink_points[:6], p, 100)
    betaqs = iterate_f(mink_points[:6], q, 10)

    ellipse_pts = scaled_lightvectors(mink_points[:6], p)

    fixed_point = betaps[-1]

    ls = []
    ps = []

    for j in range(1):
        for i in range(4):
            l0 = ideal_angle_bisector(mink_points[j], mink_points[(j+i+1)%6], mink_points[(j+i+2)%6])
            l1 = ideal_angle_bisector(mink_points[(j+i+1)%6], mink_points[(j+i+2)%6], mink_points[j])
            ls.append(l0)
            ls.append(l1)
            p1 = VectorM21.fromPointOP2(l0.intersectWithLineOP2(l1))
            ps.append(p1.normalize())

    centroid = sum(ps, start=VectorM21(0,0,0))

    #fixed_point = centroid

    I1 = SpanM21(1,0,0)

    if isZero(fixed_point.x) and isZero(fixed_point.y):
        I2 = I1
    else:
        fixed_point_inv = fixed_point.invertThrough(I1)
        origin = math.sqrt(abs(fixed_point_inv.normSq())) * VectorM21(0, 0, 1)
        I2 = fixed_point_inv.bisectorWith(origin)
        # print(f"I2: {I2}")
        # print(f"inverted: {fixed_point_inv.invertThrough(I2)}")

    transformed_mink_points = [v.invertThrough(I1).invertThrough(I2) for v in mink_points]

    # betap = (-1/6.0) * sum([(1/wi.innerProductWith(p)) * wi for wi in mink_points[0:6]], start=VectorM21(0,0,0))
    # print(f"XYZ betap: {betap}")
    # betaq = (-1/6.0) * sum([(1/wi.innerProductWith(q)) * wi for wi in mink_points[0:6]], start=VectorM21(0,0,0))
    # print([wi for wi in mink_points[0:6]])
    # print(sum([(1/wi.innerProductWith(p)) for wi in mink_points[0:6]]))
    # print([(1/wi.innerProductWith(p))*wi for wi in mink_points[0:6]])
    # print(sum([(1/wi.innerProductWith(p))*wi for wi in mink_points[0:6]], start=VectorM21(0,0,0)))
    # print(f"betap: {betap}")
    # print(f"betaq: {betaq}")


    editor_scene.clear()

    editor_scene.add(CircleE2(PointE2(0,0), scale), blackStyle)
    #editor_scene.add(spanToHypLine(I1, scale), blackStyle)

    #editor_scene.addAll([(scale * p.toPointE2(), grayPtStyle) for p in mink_grid_points])

    for grid_line in grid:
        editor_scene.addAll([(SegmentE2(scale * grid_line[i].toPointE2(), scale * grid_line[i+1].toPointE2()), grayStyle) for i in range(len(grid_line)-1)])

    for j in range(len(grid[0]) - 1):
        editor_scene.addAll([
            (
                SegmentE2(scale * grid[i][j].toPointE2(), scale * grid[(i+1)%len(grid)][j].toPointE2()), grayStyle
            )
            for i in range(len(grid))
        ])

    editor_scene.addAll(
        [(points[i], 
          blackPtStyle
          ) for i in range(6)]
    )


    editor_scene.addAll([(segmentE2ForLineOP2(obj, 4, scale), grayStyle) for obj in ls])
    editor_scene.addAll([(scale * p.toPointE2(), pinkPtStyle) for p in ps])


    #editor_scene.addAll([(obj, grayStyle) for obj in ideal_angle_bisector(mink_points[0], mink_points[1], mink_points[2])])
    editor_scene.addAll(
        [(points[i], 
        blackStyle if mink_points[i].isLightlike() else
        redStyle if mink_points[i].isSpacelike() else
        blueStyle) for i in range(6, len(points))]
    )

    editor_scene.addAll(
        [(SegmentE2(
            points[i], 
            points[(i+1)%6]), blackStyle) 
            for i in range(6)]
    )

    editor_scene.addAll([(scale * betap.toPointE2(), greenPtStyle) for betap in betaps[1:10]])
    editor_scene.addAll([(scale * betaq.toPointE2(), greenPtStyle) for betaq in betaqs[1:10]])
    editor_scene.add(scale * betaps[-1].toPointE2(), redPtStyle)

    editor_scene.add(scale * centroid.toPointE2(), pinkPtStyle)

    transformed_scene.clear()
    transformed_scene.add(CircleE2(PointE2(0,0), scale), blackStyle)


    for grid_line in grid:
        transformed_scene.addAll([(SegmentE2(scale * grid_line[i].invertThrough(I1).invertThrough(I2).toPointE2(), 
                                             scale * grid_line[i+1].invertThrough(I1).invertThrough(I2).toPointE2()), grayStyle) for i in range(len(grid_line)-1)])

    for j in range(len(grid[0]) - 1):
        transformed_scene.addAll([
            (
                SegmentE2(scale * grid[i][j].invertThrough(I1).invertThrough(I2).toPointE2(), 
                          scale * grid[(i+1)%len(grid)][j].invertThrough(I1).invertThrough(I2).toPointE2()), grayStyle
            )
            for i in range(len(grid))
        ])

    transformed_scene.addAll([(scale * v.toPointE2(), blackPtStyle) for v in transformed_mink_points[:6]])
    transformed_scene.addAll([(scale * v.toPointE2(), bluePtStyle) for v in transformed_mink_points[6:]])
    transformed_scene.addAll(
        [(SegmentE2(
            scale * transformed_mink_points[i].toPointE2(), 
            scale * transformed_mink_points[(i+1)%6].toPointE2()), blackStyle) 
            for i in range(6)]
    )
    transformed_scene.add(PointE2(0,0), redPtStyle)

    lifting_scene.clear()

    # lifting_scene.add(PointE3(0,0,0), blackPtStyle)
    # lifting_scene.add(PointE3(0,0,1), redPtStyle)
    # lifting_scene.add(PointE3(0,0,-1), bluePtStyle)

    lifting_scene.addAll([(mp.toPointE3(), blackPtStyle) for mp in mink_points])
    lifting_scene.addAll(
        [(SegmentE3(
            mink_points[i].toPointE3(), 
            mink_points[(i+1)%6].toPointE3()), blackStyle) 
            for i in range(6)]
    )
    lifting_scene.addAll(
        [(SegmentE3(mp.toPointE3(), PointE3(0,0,0)), blackStyle) for mp in mink_points]
    )
    
    lifting_scene.addAll([(mp.normalize().toPointE3(), redPtStyle) for mp in mink_points[6:]])
    #lifting_scene.addAll([(betap, greenPtStyle) for betap in betaps[1:10]])
    print(betaps[-1])
    print(betaps[-1].normSq())

    #lifting_scene.addAll([(betaq, greenPtStyle) for betaq in betaqs[1:10]])
    lifting_scene.addAll([(betap.projectToLevelE3(1), greenPtStyle) for betap in betaps[1:]])
    lifting_scene.addAll([(betaq.projectToLevelE3(1), greenPtStyle) for betaq in betaqs[1:]])
    lifting_scene.add(betaps[-1].projectToLevelE3(1), redPtStyle)
    lifting_scene.add(betaps[-1].toPointE3(), redPtStyle)
    lifting_scene.add(SegmentE3(betaps[-1].projectToLevelE3(1),betaps[-1].toPointE3()), redStyle)
    
    ellipse_ptsE3 = [p.toPointE3() for p in ellipse_pts]
    lifting_scene.addAll([(SegmentE3(p.toPointE3(), q), grayStyle) for q in ellipse_ptsE3])
    lifting_scene.addAll([(SegmentE3(ellipse_ptsE3[i], ellipse_ptsE3[(i+1)%len(ellipse_ptsE3)]), grayStyle) for i in range(len(ellipse_ptsE3))])
    lifting_scene.addAll([(p, bluePtStyle) for p in ellipse_ptsE3])
    
    dists = [betaps[i].hyperbolicDistanceTo(betaqs[i]) for i in range(10)]

    print("\n\n")
    print(f"d_H(p, q) = {dists[0]}")
    print(f"d_H(f(p), f(q)) = {dists[1]}\n")
    print(f"[d_H(p, q), d_H(f(p), f(q)), d_H(f(f(p)), f(f(q))), ...] = {dists}")
    print(f"ratios: {[dists[i+1]/dists[i] for i in range(9)]}")
    print(f"dists to final: {[betaps[i].hyperbolicDistanceTo(betaps[-1]) for i in range(9)]}")
    print("\n\n")
    
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
    print(event["key"])

editor_scene = E2Scene(title="Hyperbolic Plane")
lifting_scene = S2Scene(title="Minkowski (2,1)")
transformed_scene = E2Scene(title="Centered at fixed point")

lifting_scene.toggleSphere()
lifting_scene.toggleLightCone()

editor_scene.set_mouse_pressed(mouse_pressed_handler)
editor_scene.set_mouse_released(mouse_released_handler)
editor_scene.set_mouse_moved(mouse_moved_handler)
editor_scene.set_mouse_dragged(mouse_moved_handler)
editor_scene.set_key_pressed(key_pressed_handler)

viewer.add_scene(editor_scene)
viewer.add_scene(transformed_scene)
viewer.add_scene(lifting_scene)

refresh_points(points)

viewer.run()
