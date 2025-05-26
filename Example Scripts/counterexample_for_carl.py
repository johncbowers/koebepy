

from koebe.geometries.euclidean3 import PointE3, SegmentE3
from koebe.geometries.spherical2 import CPlaneS2, DiskS2

from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle

from koebe.graphics.flask.multiviewserver import viewer

import math


#
# Set up the geometric objects
#

h = 0.73
h2 = math.sqrt(2*h**2)
zh = 0.165

D0 = DiskS2(h, zh, h, 1)
D1 = DiskS2(-h, zh, h, 1)
D2 = DiskS2(-h, zh, -h, 1)
D3 = DiskS2(h, zh, -h, 1)

#1.0182
D4 = DiskS2(h2,-zh,  0, 1)
D5 = DiskS2(0,-zh,  h2, 1)
D6 = DiskS2(-h2,-zh,  0, 1)
D7 = DiskS2(0,-zh,  -h2, 1)

disks = [D0, D1, D2, D3, D4, D5, D6, D7]
caps = [d.dualPointOP3.toPointE3() for d in disks]

edges = [
    (0, 1), (1, 2), (2, 3), (3, 0), 
    (4, 5), (5, 6), (6, 7), (7, 4),
    (4, 0), (0, 5), (5, 1), (1, 6), (6, 2), (2, 7), (7, 3), (3, 4)
]

faces = [(0, 1, 2, 3), (4, 5, 6, 7), (4, 0, 5), (0, 5, 1), (5, 1, 6), (1, 6, 2), (6, 2, 7), (2, 7, 3), (7, 3, 4), (3, 4, 0)]

orthos = [CPlaneS2.throughThreeDiskS2(disks[face[0]], disks[face[1]], disks[face[2]]) for face in faces]

#
# Style parameters to be used in the scene
#

blackStyle = makeStyle(stroke=(0,0,0), fill=None, strokeWeight=5.0)
blueStyle = makeStyle(stroke=(0,0,255), fill=None, strokeWeight=5.0)
redStyle = makeStyle(stroke=(255,0,0), fill=None, strokeWeight=1.0)
grayStyle = makeStyle(stroke=(128,128,128), fill=None, strokeWeight=0.5)

#
# Set up the scene
# 

scene = S2Scene(show_sphere=True)
#scene.toggleSphere()

scene.addAll([(d, blackStyle) for d in disks])
scene.addAll(caps)
scene.addAll([
    (SegmentE3(caps[i], caps[j]), blueStyle) for i, j in edges
])
scene.addAll([(o, redStyle) for o in [orthos[1], orthos[2], orthos[4], orthos[6], orthos[8]]])
scene.add(PointE3(0, 1, 0))

scene.addAll([
    (SegmentE3(caps[i], PointE3(0,1,0)), blueStyle) for i in [4, 5, 6, 7]
])

scene.addAll([
    (SegmentE3(caps[i], PointE3(0,-1,0)), blueStyle) for i in range(4)
])

viewer.add_scene(scene)
viewer.run()
