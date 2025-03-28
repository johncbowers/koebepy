# Packages for drawable objects
from koebe.geometries.euclidean2 import PointE2, SegmentE2, CircleE2, VectorE2, PolygonE2
from koebe.geometries.orientedProjective2 import PointOP2, DiskOP2, SegmentOP2, CircleArcOP2
from koebe.geometries.hyperbolic2 import PointH2, CircleH2, SegmentH2, LineH2
from koebe.datastructures.dcel import DCEL, Face, Edge, Vertex

import math

from .scene import Scene
from .scene import makeStyle as _makeStyle

makeStyle = _makeStyle

### GEOMETRIC OBJECTS TO DICTIONARIES FOR THE P5 SCRIPT

def _p5_pointE2(point):
    return {"type": "PointE2", 
            "point": tuple(point)}

def _pointTypes_to_E2(p):
    if type(p) is PointOP2:
        return tuple(p.toPointE2())
    elif type(p) is PointE2:
        return tuple(p)
    else:
        return ()

def _face_as_vertex_list(face):
    polygon = []
    for dart in face.darts():
        polygon.append(_pointTypes_to_E2(dart.origin.data))
    return polygon

def _p5_face(face, style):
    result = {"type": "Polygon", 
              "vertices": _face_as_vertex_list(face)}
    if style == None:
        result["style"] = makeStyle(fill = "#ccf")

    return result

def _p5_dcel(dcel, style):
    polygons = []
    for face in dcel.faces:
        polygons.append(_face_as_vertex_list(face))
    
    result = {"type": "Polygons",
            "polygons": polygons}
    if style == None:
        result["style"] = makeStyle(stroke = "#000", strokeWeight = 2, fill = "#ccf")
    return result

def _p5_edge(edge, style):
    return _p5_segmentE2((_pointTypes_to_E2(edge.aDart.origin.data), 
                          _pointTypes_to_E2(edge.aDart.dest.data)), 
                         style)

def _p5_segmentE2(seg, style):
    result = {"type": "SegmentE2", 
            "endpoints": tuple(seg)}
    if style == None:
        result["style"] = makeStyle(stroke = "#000", strokeWeight = 2)
    return result

def _p5_circleArcOP2(arc, style):
    if arc == None:
        return None
    if arc.disk.a == 0:
        return _p5_segmentE2(
            SegmentE2(
                arc.source.toPointE2(),
                arc.target.toPointE2()
            ), 
            style
        )
    else:
        rad = arc.radius
        
        srcOP2, trgOP2 = (arc.source, arc.target) if arc.disk.a >= 0 else (arc.target, arc.source)
        src, trg = srcOP2.toPointE2(), trgOP2.toPointE2()
        
        ratio = math.sqrt(src.distTo(trg)) / rad
        
        if ratio < 0.1:
            return _p5_segmentE2(
                SegmentE2(
                    arc.source.toPointE2(),
                    arc.target.toPointE2()
                ), 
                style
            )
        else: 
            radInv = 1.0 / rad
            center = arc.disk.center.toPointE2()
            
            srcV = VectorE2((src.x - center.x) * radInv, (src.y - center.y) * radInv)
            trgV = VectorE2((trg.x - center.x) * radInv, (trg.y - center.y) * radInv)

            srcAngle = srcV.angleFromXAxis()
            targetAngle = trgV.angleFromXAxis()
            
            if srcAngle > targetAngle:
                targetAngle += 2.0 * math.pi
            
            result = {"type": "CircleArcE2", 
                      "center": tuple(center), 
                      "radius": rad,
                      "srcAngle": srcAngle, 
                      "targetAngle": targetAngle}
            
            if style == None:
                result["style"] = makeStyle(stroke = "#000", strokeWeight = 1)
                
            return result

def _p5_circleE2(circle, style):
    result = {"type": "CircleE2", 
              "center": tuple(circle.center), 
              "radius": circle.radius}
    if style == None:
        result["style"] = makeStyle(stroke = "#000", strokeWeight = 1)
    return result

def _p5_polygonE2(polygon, style):
    result = {"type": "PolygonE2", 
              "vertices": [(p.x, p.y) for p in polygon.vertices]}
    if style == None:
        result["style"] = makeStyle(stroke = "#000", strokeWeight = 1)
    return result

def _p5_dict(obj, style):
    
    if type(obj) is Vertex:
        obj = obj.data    
    if type(obj) is PointE2:
        result = _p5_pointE2(obj)
    elif type(obj) is PointH2:
        result = _p5_pointE2(obj.toPointE2())
    elif type(obj) is PointOP2:
        result = _p5_pointE2(obj.toPointE2())
    elif type(obj) is CircleE2:
        result = _p5_circleE2(obj, style)
    elif type(obj) is CircleH2:
        result = _p5_circleE2(obj.toPoincareCircleE2(), style)
    elif type(obj) is DiskOP2:
        result = _p5_circleE2(obj.toCircleE2(), style)
    elif type(obj) is DCEL:
        result = _p5_dcel(obj, style)
    elif type(obj) is Edge:
        result = _p5_edge(obj, style)
    elif type(obj) is Face:
        result = _p5_face(obj, style)
    elif type(obj) is CircleArcOP2:
        result = _p5_circleArcOP2(obj, style)
    elif type(obj) is SegmentE2:
        result = _p5_segmentE2(obj, style)
    elif type(obj) is SegmentOP2:
        result = _p5_segmentE2(SegmentE2(obj.source.toPointE2(), 
                                         obj.target.toPointE2()), style)
    elif type(obj) is SegmentH2:
        result = _p5_circleArcOP2(obj.toPoincareCircleArcOP2(), style)
    elif type(obj) is LineH2:
        result = _p5_circleArcOP2(obj.toPoincareCircleArcOP2(), style)
    elif type(obj) is PolygonE2:
        result = _p5_polygonE2(obj, style)
    else:
        result = None
        
    if result != None and style != None:
        result["style"] = style
        
    return result


### THE ACTUAL VIEWER CLASSES
    
class E2Scene(Scene):
    def __init__(self, width=500, height=500, scale=1.0, title=None, pan_and_zoom=False):
        super().__init__(width = width, 
                         height = height, 
                         scale = scale, 
                         title = title,
                         obj_json_convert_func = _p5_dict, 
                         pan_and_zoom = pan_and_zoom)
    
class PoincareDiskScene(Scene):
    def __init__(self, width=500, height=500, title=None, pan_and_zoom=False):
        super().__init__(width  = width, 
                         height = height, 
                         title = title,
                         scale  = 1.0 / (min(width, height)*0.5-10),
                         pan_and_zoom = pan_and_zoom)
        self.unitDisk = CircleE2(PointE2(0,0), 1.0)
        self.add(self.unitDisk)
        
class UnitScaleE2Scene(E2Scene):
    def __init__(self, width=500, height=500, title=None, pan_and_zoom=False):
        super().__init__(width  = width, 
                         height = height, 
                         title = title, 
                         scale  = 1.0 / (min(width, height)*0.5-10), 
                         pan_and_zoom = pan_and_zoom)