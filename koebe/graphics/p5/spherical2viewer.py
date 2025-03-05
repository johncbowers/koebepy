from .viewer import Viewer
from .viewer import makeStyle as _makeStyle

from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.datastructures.dcel import *
from koebe.geometries.orientedProjective3 import *

from p5 import *

makeStyle = _makeStyle

_viewer = None

def setup():
    global _viewer
    if _viewer:
        _viewer.setup()

def draw():
    global _viewer
    if _viewer:
        _viewer.draw()

def key_pressed():
    global _viewer
    if _viewer:
        _viewer.key_pressed()

def mouse_pressed():
    global _viewer
    if _viewer:
        _viewer.mouse_pressed() 

def mouse_dragged():
    global _viewer
    if _viewer: 
        _viewer.mouse_dragged()

def mouse_released():
    global _viewer
    if _viewer:
        _viewer.mouse_released()

class S2Viewer(Viewer):
    def __init__(self, width=800, height=800):
        super().__init__(width = width, 
                         height = height, 
                         scale = 1.0)
        self.showSphere = True
        self.showBox = True
        self._view_x = 0
        self._view_y = 0
        self._bx = 0
        self._by = 0
        self._key_pressed_handler = None

    def toggleSphere(self):
        self.showSphere = not self.showSphere

    def setup(self):
        size(self.width, self.height)

    def drawCircleE2(self, circle):
        style = self.getStyle(circle)
        translate(circle.center.x, circle.center.y, -1)
    
        if style:
            if "stroke" in style and style["stroke"]:
                # print(style["stroke"])
                fill(*style["stroke"])
        else:
            fill(0, 0, 0)
        torus(circle.radius, 0.005, 24, 4)

    def drawDiskS2(self, disk, style=None):
        if style is None:
            style = self.getStyle(disk)

        b1 = disk.normedBasis1.v
        b2 = disk.normedBasis2.v
        b3 = disk.normedBasis3.v
        centerDist = disk.centerE3.distTo(PointE3.O)
        diameter = disk.radiusE3 * 2.0

        applyMatrix([
            b1.x, b2.x, b3.x, 0, 
            b1.y, b2.y, b3.y, 0, 
            b1.z, b2.z, b3.z, 0, 
            0, 0, 0, 1
        ])

        if disk.d < 0:
            translate(0, 0, centerDist)
        else:
            translate(0, 0, -centerDist)

        if style:
            if "stroke" in style and style["stroke"]:
                # print(style["stroke"])
                fill(*style["stroke"])
                stroke(*style["stroke"])
        else:
            fill(0, 0, 0)
            stroke(0, 0, 0)
        torus(diameter/2.0, 0.01, 24, 3)
        #torus(diameter / 2)
        
    def drawPointE3(self, p):
        translate(p.x, p.y, p.z)
        box(0.035, 0.035, 0.035)

    def drawCPlaneS2(self, P):
        style = self.getStyle(P)
        self.drawDiskS2(P.dualDiskS2, style)

    def drawDcel(self, dcel):
        pass

    def drawSegmentE3(self, seg:SegmentE3):
        style = self.getStyle(seg)
        if style:
            if "stroke" in style and style["stroke"]:
                stroke(*style["stroke"])
            if "strokeWeight" in style and style["strokeWeight"]:
                strokeWeight(style["strokeWeight"])
        else:
            stroke(0)
        line3d(seg.source.x, seg.source.y, seg.source.z, 
             seg.target.x, seg.target.y, seg.target.z)

    def drawObj(self, obj):
        if type(obj) is Vertex:
            obj = obj.data
        
        if type(obj) is DiskS2:
            self.drawDiskS2(obj)
        elif type(obj) is PointE3:
            self.drawPointE3(obj)
        elif type(obj) is PointS2:
            self.drawPointE3(obj.directionE3.endPoint)
        elif type(obj) is PointOP3:
            self.drawPointE3(obj.toPointE3())
        elif type(obj) is CircleE2:
            self.drawCircleE2(obj)
        elif type(obj) is CPlaneS2:
            self.drawCPlaneS2(obj)
        # elif type(obj) is DCEL:
        #     self.drawDcel(obj, style)
        # elif type(obj) is Edge:
        #     self.drawEdge(obj, style)
        # elif type(obj) is Face:
        #     self.drawFace(obj, style)
        elif type(obj) is SegmentE3:
            self.drawSegmentE3(obj)
        # elif isinstance(obj, VertexColoredTriangle):
        #     result = obj.to_dict()

    def draw(self):
        background(237, 246, 252)
        scale(1.0, -1.0, 1.0)
        scale(200 * self.scale)
        strokeWeight(0.005 / self.scale)

        rotateX(self._view_x)
        rotateY(self._view_y)

        pushStyle()
        noStroke()
        lights()

        if self.showSphere:
            # blinn_phong_material()
    
            fill(220, 220, 220)
            sphere(0.999, 24, 16)
            # locX = mouse_x - width/2
            # locY = height/2 - mouse_y
            # light_specular(0, 0, 255)
            # point_light(360, 360*1.5, 360, locX, locY, 400)

        for obj in self._objs:
            pushMatrix()
            self.drawObj(obj)
            popMatrix()

        if self.showBox:
            noFill()
            stroke(0)
            box(2.0, 2.0, 2.0)

        popStyle()
    
    def key_pressed(self):
        global key
        if self._key_pressed_handler:
            self._key_pressed_handler(key)
        # if key == "UP":
        #     self._view_x += 0.1
        # elif key == "DOWN":
        #     self._view_x -= 0.1
        # elif key == "RIGHT":
        #     self._view_y += 0.1
        # elif key == "LEFT":
        #     self._view_y -= 0.1

    def mouse_pressed(self):
        self._bx = mouse_x
        self._by = mouse_y

    def mouse_dragged(self):
        offset_x = mouse_x - self._bx
        offset_y = mouse_y - self._by
        self._view_x -= offset_y/100.0
        self._view_y += offset_x/100.0
        self._bx = mouse_x
        self._by = mouse_y
    
    def mouse_released(self):
        pass

    def _run(self):
        global _viewer
        _viewer = self
        run(mode='P3D')
                