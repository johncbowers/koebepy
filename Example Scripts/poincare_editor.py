
# import optparse

# p = optparse.OptionParser()
# p.add_option('--outfile', '-o', default="poincare-out.txt")
# p.add_option('--view', '-v', default='2d')
# options, arguments = p.parse_args()

import sys
import getopt
import pickle

from koebe.geometries.euclidean2 import *

short_options = "i:o:v:"
long_options = ["in-file", "out-file", "view"]

def print_usage():
    print(f"Usage: python {sys.argv[0]} [options]")
    print(f"\toptions:")
    print(f"\t  -i, --in-file <input file>\tAn input file of circles to load on startup.")
    print(f"\t  -o, --out-file <output file>\tAn output file of circles to write to when pressing 'w'.")
    print(f"\t  -v, --view (2d|3d)\tLoad 2D editor view or 3D read-only viewer.")
    print(f"\t  -h, --help\tPrint this message.")

try:
    arguments, values = getopt.getopt(sys.argv[1:], short_options, long_options)
except getopt.error as err:
    print(str(err))
    print_usage()
    sys.exit(2)

show_3d = False
in_file = None
out_file = "poincare-out.txt"
circles = []

def load_file():
    global in_file, circles
    if in_file != None:
        with open(in_file, "rb") as f:
            circles_tuples = pickle.load(f)
            circles = [
                CircleE2(PointE2(x, y), r)
                for x, y, r in circles_tuples
            ]
            f.close()
    else:
        print("No input file has been specified.")

for opt, val in arguments: 
    if opt == "-i" or opt == "--in-file":
        in_file = val
        load_file()
    elif opt == "-o" or opt == "--out-file":
        out_file = val
    elif opt == "-v" or opt == "--view":
        show_3d = val.lower() == "3d"
    elif opt == "-h" or opt == "--help":
        print_usage()
        sys.exit(0) 

if not show_3d:
    from koebe.graphics.p5.euclidean2viewer import *
else:
    from koebe.graphics.p5.spherical2viewer import *

from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointOP3, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

from math import *
from random import *

import numpy as np
from scipy.linalg import null_space
import scipy.optimize as opt
import scipy.linalg as la
from scipy.spatial import ConvexHull

npoints = 30

blackStyle = makeStyle(stroke=(0,0,0), fill=None, strokeWeight=2.0)
blueStyle = makeStyle(stroke=(0,0,255), fill=None, strokeWeight=2.0)
redStyle = makeStyle(stroke=(255,0,0), fill=None, strokeWeight=2.0)

verbose = False

mouse_down = False
selected_idx = -1
closest_idx = -1
closest_dist = float('inf')
remove_zero_edges = False

edit_circle = None
edit_mode = None
edit_offset = None

def refresh_geometry():
    global edit_circle, closest_idx, selected_idx, viewer, circles, remove_zero_edges, verbose
    viewer.clear()
    hyperbolic_boundary = CircleE2(PointE2(viewer.width, viewer.height), viewer.width)
    viewer.add(hyperbolic_boundary, blackStyle)
    viewer.addAll(
        [(C, blackStyle) for C in circles]
    )
    if edit_circle:
        viewer.add(edit_circle, blackStyle)
        all_circles = [hyperbolic_boundary, edit_circle] + circles
    else:
        all_circles = [hyperbolic_boundary] + circles

    # print("===")
    # print(all_circles)
    scale = 1.5 / viewer.width
    all_circles_orig = all_circles
    all_circles = [CircleE2(PointE2((C.center.x - viewer.width) * scale, (C.center.y - viewer.width) * scale), C.radius * scale) for C in all_circles]
    # print(all_circles)
    # for C in all_circles:
    #     viewer.addAll(C.toThreePointsE2())
    
    sphere_disks = [C.toDiskS2() for C in all_circles]
    # print(sphere_disks)
    sphere_disks = [DiskOP2.fromCircleE2(C).toDiskS2() for C in all_circles]
    # print(sphere_disks)
    caps = [d.dualPointOP3.toPointE3() for d in sphere_disks]
    viewer.addAll(sphere_disks)
    viewer.addAll(caps)
    if len(sphere_disks) >= 4:
        conical_caps = [d.dualPointOP3.toPointE3() for d in sphere_disks]
        cap_coords = np.array([[p.x, p.y, p.z] for p in conical_caps])
        hull = ConvexHull(cap_coords)
        edges_not_flat = [[(i, j), (j, k), (k, i)] for i, j, k in hull.simplices]
        edges = [ij for ijk in edges_not_flat for ij in ijk]

        edge_segs = [SegmentE2(all_circles_orig[i].center, all_circles_orig[j].center) for i, j in edges if i != 0 and j != 0]
        viewer.addAll([(e, blueStyle) for e in edge_segs])

        edge_segsE3 = [SegmentE3(caps[i], caps[j]) for i, j in edges]
        viewer.addAll(edge_segsE3)

        orthosS2 = [CPlaneS2.throughThreeDiskS2(
                        sphere_disks[i],
                        sphere_disks[j],
                        sphere_disks[k]            
                    )
                    for i, j, k in hull.simplices]
        viewer.addAll([(o, redStyle) for o in orthosS2])
        orthos = [
            o.dualDiskS2.toDiskOP2().toCircleE2()
            for o in orthosS2 if o.dualDiskS2.toDiskOP2().radiusSq > 0
        ]
        orthos_moved = [
            CircleE2(PointE2(C.center.x / scale + viewer.width, C.center.y / scale + viewer.height), C.radius / scale)
            for C in orthos
        ]
        viewer.addAll([(o, redStyle) for o in orthos_moved])

    
block_poincare = False

def mouse_pressed_handler(event):
    global circles, edit_mode, edit_circle, edit_offset, mouse_down, closest_idx, closest_dist, selected_idx
    # if closest_dist < 225:
    #     selected_idx = closest_idx
    # mouse_down = True
    # refresh_geometry(points)
    mouse_down = True
    evt_pt = PointE2(event.x, event.y)
    if event.is_ctrl_down():
        edit_mode = "add"
        dx = viewer.width - event.x
        dy = viewer.height - event.y
        if not block_poincare or dx*dx + dy*dy < viewer.width * viewer.width:
            edit_circle = CircleE2(evt_pt, 1)
        else:
            edit_mode = None
    else:
        # find the closest circle to the mouse point
        if len(circles) > 0:
            dists = [abs((C.center - evt_pt).norm()-C.radius) for C in circles]
            min_dist = min(dists)
            if min_dist < 10:
                min_idx = dists.index(min_dist)
                edit_circle = circles[min_idx]
                circles = circles[:min_idx] + circles[min_idx+1:]
                if event.is_shift_down():
                    edit_mode = "radius"
                elif event.is_alt_down():
                    edit_mode = None
                    edit_circle = None
                else:
                    edit_mode = "center"
                    edit_offset = edit_circle.center - evt_pt

    refresh_geometry()
t=0

def mouse_moved_handler(event):
    global edit_mode, edit_circle, edit_offset
    # print(f"dragged {t}")
    # t+=1
    if mouse_down:
        evt_pt = PointE2(event.x, event.y)
        Orig = PointE2(viewer.width, viewer.width)
        if edit_mode == "add" or edit_mode == "radius":
            if edit_circle:
                orig_dist = edit_circle.center.distTo(Orig)
                new_radius = edit_circle.center.distTo(evt_pt)
                if block_poincare and orig_dist + new_radius > viewer.width:
                    new_radius = viewer.width - orig_dist
                edit_circle = CircleE2(edit_circle.center, new_radius)
        elif edit_mode == "center":
            new_center = evt_pt + edit_offset
            orig_dist = new_center.distTo(Orig)
            
            if block_poincare and orig_dist + edit_circle.radius > viewer.width:
                delta = orig_dist + edit_circle.radius - viewer.width
                v = new_center - Orig
                new_center = ((v.norm()-delta)/v.norm())*v + Orig

            edit_circle = CircleE2(new_center, edit_circle.radius)
            
        refresh_geometry()

def mouse_released_handler(event):
    global circles, edit_mode, edit_circle, mouse_down, selected_idx
    # mouse_down = False
    # selected_idx = -1
    # refresh_geometry(points)
    if edit_mode == "add" or edit_mode == "radius" or edit_mode == "center":
        circles.append(edit_circle)
    mouse_down = False
    edit_mode = None
    edit_circle = None
    edit_offset = None
    pass

# def mouse_moved_handler(event):
#     global mouse_down, closest_idx, closest_dist, selected_idx
#     # p = PointE2(event.x, event.y)
#     # distSqs = [p.distSqTo(q) for q in points]
#     # closest_dist = min(distSqs)
#     # closest_idx = distSqs.index(closest_dist)
#     # if selected_idx != -1:
#     #     new_points = [points[pIdx] if pIdx != selected_idx else PointE2(event.x, event.y) for pIdx in range(len(points))]
#     #     closest_dist = 0
#     #     refresh_geometry(new_points)
#     # else:
#     #     refresh_geometry(points)
#     pass

def key_pressed_handler(event):
    global remove_zero_edges, circles, in_file, out_file
    # if event.key == " ":
    #     create_random_tutte()
    # elif event.key == "z":
    #     remove_zero_edges = not remove_zero_edges
    #     refresh_points(points)
    if event.key == "w":
        print(f"Writing current disk set to {out_file}.")
        with open(out_file, "wb") as f:
            pickle.dump([(c.center.x, c.center.y, c.radius) for c in circles], f)
            f.close()
        if in_file == None:
            in_file = out_file
    elif event.key == "r":
        print("reloading file")
        load_file()
        refresh_geometry()
    elif event.key == "q":
        sys.exit(0)


if not show_3d:
    viewer = E2Viewer()
else:
    viewer = S2Viewer()
    viewer.scale = 2
    viewer.showBox = False

viewer._mouse_moved_handler = mouse_moved_handler
viewer._mouse_pressed_handler = mouse_pressed_handler
viewer._mouse_released_handler = mouse_released_handler
viewer._mouse_dragged_handler = mouse_moved_handler
viewer._key_pressed_handler = key_pressed_handler
# viewer._frame_update = refresh_geometry

# if not show_3d:
#     circles = []
# else: 
#     circles = [CircleE2(center=PointE2(x=578.734375, y=252.5703125), radius=106.1147867237445), CircleE2(center=PointE2(x=396.8984375, y=710.125), radius=340.00244373116504), CircleE2(center=PointE2(x=992.90625, y=1133.6015625), radius=294.4044921615205), CircleE2(center=PointE2(x=1038.578125, y=446.8515625), radius=273.1841504885029), CircleE2(center=PointE2(x=1375.8203125, y=803.296875), radius=171.55777579162745)]
# circles = [CircleE2(center=PointE2(x=330.859375, y=592.2578125), radius=128.22171702102696), CircleE2(center=PointE2(x=812.265625, y=236.5078125), radius=118.34412391428255), CircleE2(center=PointE2(x=1105.6796875, y=722.1484375), radius=189.1829628175068), CircleE2(center=PointE2(x=552.4609375, y=1285.8828125), radius=187.77890226991772), CircleE2(center=PointE2(x=683.9453125, y=807.890625), radius=113.43631412947641)]

refresh_geometry()
viewer.show()
