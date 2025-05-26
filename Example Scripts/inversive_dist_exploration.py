

from koebe.geometries.euclidean3 import PointE3
from koebe.geometries.spherical2 import CPlaneS2, DiskS2

from koebe.graphics.scenes.spherical2scene import S2Scene

from koebe.graphics.flask.multiviewserver import viewer

import math

D1 = DiskS2(0,0,1,1.1/math.sqrt(2))
D2 = DiskS2(0,1,0,1.1/math.sqrt(2))
D3 = DiskS2(1,0,0,1.1/math.sqrt(2))
D4 = (1.0/3.0)*(D1 + D2 + D3)
p4 = D4.dualPointOP3.toPointE3()
p4 = (1/p4.distSqTo(PointE3.O)) * p4
D4 = DiskS2(-p4.x, -p4.y, -p4.z, 1)

scene = S2Scene(show_sphere=False)

scene.add(D1)
scene.add(D2)
scene.add(D3)
scene.add(D4)


#scene.add(CPlaneS2.throughThreeDiskS2(D1, D2, D3))

viewer.add_scene(scene)
viewer.run()
