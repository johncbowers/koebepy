from koebe.graphics.p5.spherical2viewer import *
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

from math import *
from random import *


# print(f"3,4 {disks[2].inversiveDistTo(disks[3])}")
# print(f"3,5 {disks[2].inversiveDistTo(disks[4])}")
# print(f"4,6 {disks[3].inversiveDistTo(disks[5])}")

# D1 = DiskS2(-1.0748811207324158, -0.0, -0.0, 1)
# D2 = DiskS2(1.0748811207324158, 0.0, -0.0, 1)

# print(f"Back to front: {D1.inversiveDistTo(D2)}")



viewer = S2Viewer()

viewer.scale = 2
viewer.showBox = False

blackStyle = makeStyle(stroke=(0,0,0))
redStyle = makeStyle(stroke=(255,0,0), strokeWeight=2.0)

def rotate_disk(disk, theta):
    c, s = math.cos(theta), math.sin(theta)
    return DiskS2(
        disk.a * c - disk.b * s, 
        disk.a * s + disk.b * c,
        disk.c,
        disk.d
    )

def add_disks(theta):
    global viewer

    viewer._objs = []

    data_from_matthias = [
        [0.0, 0.0, 2.7269530298948657],
        [0.0, 0.0, -2.7269530298948657],
        [1.0748811207324158, 0.0, 0.0],
        [0.7857897585153099, 0.733419306482271, -4.4056396261008384e-18],
        [0.6412440774068765, -0.8626560478545451, -1.473824188854271e-17],
        [1.0573928662071708, -0.19310554161202076, 1.4597634039938443e-17]
    ]

    disks = [
        DiskS2(-x, -y, -z, 1)
        for x, y, z in data_from_matthias
    ]

    disks[4] = rotate_disk(disks[4], theta)
    disks[5] = rotate_disk(disks[5], theta)

    viewer.addAll(disks)

    print([[-d.a, -d.b, -d.c] for d in disks])
    print(disks[3].inversiveDistTo(disks[5]))

theta = 0
add_disks(theta)

def key_pressed_handler(key):
    global packing_showing, theta
    
    if key == "s":
        viewer.toggleSphere()
    elif key == "r":
        viewer._view_x = 0
        viewer._view_y = 0
    elif key == "p":
        if packing_showing: 
            viewer.removeAll(diskSet)
            viewer.removeAll(segs)
            packing_showing = False
        else:
            viewer.addAll(diskSet)
            viewer.addAll(segs)
            packing_showing = True
    elif key == "t":
        theta += math.pi / 16
        add_disks(theta)

viewer._key_pressed_handler = key_pressed_handler


viewer.show()


