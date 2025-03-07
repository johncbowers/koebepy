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

def key_pressed(event):
    global _viewer
    if _viewer:
        _viewer.key_pressed(event)

def mouse_pressed(event):
    global _viewer
    if _viewer:
        _viewer.mouse_pressed(event) 

def mouse_dragged(event):
    global _viewer
    if _viewer: 
        _viewer.mouse_dragged(event)

def mouse_released(event):
    global _viewer
    if _viewer:
        _viewer.mouse_released(event)

def mouse_moved(event):
    global _viewer
    if _viewer:
        _viewer.mouse_moved(event)


class E2Viewer(Viewer):
    def __init__(self, width=800, height=800):
        super().__init__(width = width, 
                         height = height, 
                         scale = 1.0)
        self._view_x = 0
        self._view_y = 0
        self._bx = 0
        self._by = 0
        self._key_pressed_handler = None
        self._mouse_pressed_handler = None
        self._mouse_dragged_handler = None
        self._mouse_released_handler = None
        self._mouse_moved_handler = None
        self._frame_update = None
        self._tx = 0
        self._ty = 0

    def setup(self):
        size(self.width, self.height)

    def drawCircleE2(self, obj):
        style = self.getStyle(obj)
        if style:
            if "stroke" in style and style["stroke"]:
                # print(style["stroke"])
                stroke(*style["stroke"])
            else:
                noStroke()
            if "fill" in style and style["fill"]:
                fill(*style["fill"])
            else:
                noFill()
        else:
            stroke(0, 0, 0)
            noFill()
        # torus(circle.radius, 0.005, 24, 4)
        circle((obj.center.x, obj.center.y), obj.radius*2)

    # def drawDiskS2(self, disk, style=None):
    #     if style is None:
    #         style = self.getStyle(disk)

    #     b1 = disk.normedBasis1.v
    #     b2 = disk.normedBasis2.v
    #     b3 = disk.normedBasis3.v
    #     centerDist = disk.centerE3.distTo(PointE3.O)
    #     diameter = disk.radiusE3 * 2.0

    #     applyMatrix([
    #         b1.x, b2.x, b3.x, 0, 
    #         b1.y, b2.y, b3.y, 0, 
    #         b1.z, b2.z, b3.z, 0, 
    #         0, 0, 0, 1
    #     ])

    #     if disk.d < 0:
    #         translate(0, 0, centerDist)
    #     else:
    #         translate(0, 0, -centerDist)

    #     if style:
    #         if "stroke" in style and style["stroke"]:
    #             # print(style["stroke"])
    #             fill(*style["stroke"])
    #             stroke(*style["stroke"])
    #     else:
    #         fill(0, 0, 0)
    #         stroke(0, 0, 0)
    #     torus(diameter/2.0, 0.01, 24, 3)
    #     #torus(diameter / 2)
        
    # def drawPointE3(self, p):
    #     translate(p.x, p.y, p.z)
    #     box(0.035, 0.035, 0.035)

    # def drawCPlaneS2(self, P):
    #     style = self.getStyle(P)
    #     self.drawDiskS2(P.dualDiskS2, style)

    # def drawDcel(self, dcel):
    #     pass

    def drawSegmentE2(self, seg:SegmentE2):
        style = self.getStyle(seg)
        if style:
            if "stroke" in style and style["stroke"]:
                stroke(*style["stroke"])
            if "strokeWeight" in style and style["strokeWeight"]:
                strokeWeight(style["strokeWeight"])
        else:
            stroke(0)
        line(seg.source.x, seg.source.y, 
             seg.target.x, seg.target.y)

    def drawPointE2(self, obj):
        style = self.getStyle(obj)
        if style:
            if "stroke" in style and style["stroke"]:
                stroke(*style["stroke"])
            else:
                stroke(0,0,0)
            if "strokeWeight" in style and style["strokeWeight"]:
                strokeWeight(style["strokeWeight"])
            else:
                strokeWeight(1.0)
            if "fill" in style and style["fill"]:
                fill(*style["fill"])
            else:
                fill(0, 0, 255)
        else:
            stroke(0,0,0)
            strokeWeight(1.0)
            fill(255, 255, 255)

        circle((obj.x, obj.y), 15)
            

    def drawObj(self, obj):
        if type(obj) is Vertex:
            obj = obj.data
        
        if type(obj) is PointE2:
            self.drawPointE2(obj)
        elif type(obj) is SegmentE2:
            self.drawSegmentE2(obj)
        elif type(obj) is CircleE2:
            self.drawCircleE2(obj)
        # if type(obj) is DiskS2:
        #     self.drawDiskS2(obj)
        # elif type(obj) is PointE3:
        #     self.drawPointE3(obj)
        # elif type(obj) is PointS2:
        #     self.drawPointE3(obj.directionE3.endPoint)
        # elif type(obj) is PointOP3:
        #     self.drawPointE3(obj.toPointE3())
        # elif type(obj) is CircleE2:
        #     self.drawCircleE2(obj)
        # elif type(obj) is CPlaneS2:
        #     self.drawCPlaneS2(obj)
        # elif type(obj) is DCEL:
        #     self.drawDcel(obj, style)
        # elif type(obj) is Edge:
        #     self.drawEdge(obj, style)
        # elif type(obj) is Face:
        #     self.drawFace(obj, style)
        # elif type(obj) is SegmentE3:
        #     self.drawSegmentE3(obj)
        # elif isinstance(obj, VertexColoredTriangle):
        #     result = obj.to_dict()

    def draw(self):
        if self._frame_update:
            self._frame_update()

        translate(self._tx, self._ty)
        scale(self.scale)

        background(237, 246, 252)

        stroke(0,0,0)
        strokeWeight(1.0)
        noFill()

        for obj in self._objs:
            self.drawObj(obj)

    
    def key_pressed(self, event):
        if self._key_pressed_handler:
            self._key_pressed_handler(event)
        # if key == "UP":
        #     self._view_x += 0.1
        # elif key == "DOWN":
        #     self._view_x -= 0.1
        # elif key == "RIGHT":
        #     self._view_y += 0.1
        # elif key == "LEFT":
        #     self._view_y -= 0.1

    def _reposition_event(self, event):
        event.x /= self.scale
        event.y /= self.scale
        event.x -= (self._tx / self.scale)
        event.y -= (self._ty / self.scale)


    def mouse_pressed(self, event):
        self._reposition_event(event)
        if self._mouse_pressed_handler:
            self._mouse_pressed_handler(event)

    def mouse_dragged(self, event):
        self._reposition_event(event)
        if self._mouse_dragged_handler:
            self._mouse_dragged_handler(event)
    
    def mouse_released(self, event):
        self._reposition_event(event)
        if self._mouse_released_handler:
            self._mouse_released_handler(event)

    def mouse_moved(self, event):
        self._reposition_event(event)
        if self._mouse_moved_handler:
            self._mouse_moved_handler(event)

    def _run(self):
        global _viewer
        _viewer = self
        run(renderer="skia")
                