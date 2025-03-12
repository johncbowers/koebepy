#
# Bindings to emit p5.js code
# @author John C. Bowers
#

# Packages for loading JavaScript:
import pkgutil

# For sending data to the JavaScript part
import json #json.dumps(obj)

# Packages for drawable objects
from koebe.geometries.euclidean3 import PointE3, SegmentE3
from koebe.geometries.spherical2 import DiskS2, PointS2, CPlaneS2
from koebe.geometries.orientedProjective3 import PointOP3
from koebe.datastructures.dcel import DCEL, Face, Edge, Vertex

from .scene import Scene, VertexColoredTriangle
from .scene import makeStyle as _makeStyle

makeStyle = _makeStyle

# Use should be:
# from spherical2viewer import S2Viewer
#
# viewer = S2Viewer()
# viewer.show()
#

### GEOMETRIC OBJECTS TO DICTIONARIES FOR THE P5 SCRIPT

def _p5_pointE3(point):
    return {"type": "PointE3", 
            "point": tuple(point)}
    
def _p5_diskS2(disk):
    return {"type":       "DiskS2",
            "disk":       tuple(disk),
            "b1":         tuple(disk.normedBasis1.v),
            "b2":         tuple(disk.normedBasis2.v),
            "b3":         tuple(disk.normedBasis3.v),
            "centerDist": disk.centerE3.distTo(PointE3.O),
            "diameter":   disk.radiusE3 * 2.0}

def _p5_cPlaneS2(cplane, style):
    result = _p5_diskS2(cplane.dualDiskS2)
    if style == None:
        result["style"] = makeStyle(stroke = "#ff0000", strokeWeight = 4)
    return result

def _pointTypes_to_E3(p):
    if type(p) is PointOP3:
        return tuple(p.toPointE3())
    elif type(p) is PointE3:
        return tuple(p)
    elif type(p) is DiskS2:
        return tuple(p.dualPointOP3.toPointE3())
    else:
        return ()

def _face_as_vertex_list(face):
    polygon = []
    for dart in face.darts():
        polygon.append(_pointTypes_to_E3(dart.origin.data))
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
    return _p5_segmentE3((_pointTypes_to_E3(edge.aDart.origin.data), 
                          _pointTypes_to_E3(edge.aDart.dest.data)), 
                         style)

def _p5_segmentE3(seg, style):
    result = {"type": "SegmentE3", 
            "endpoints": tuple(seg)}
    if style == None:
        result["style"] = makeStyle(stroke = "#000", strokeWeight = 2)
    return result

def _p5_dict(obj, style):
    
    if type(obj) is Vertex:
        obj = obj.data
    
    if type(obj) is DiskS2:
        result = _p5_diskS2(obj)
    elif type(obj) is PointE3:
        result = _p5_pointE3(obj)
    elif type(obj) is PointS2:
        result = _p5_pointE3(obj.directionE3.endPoint)
    elif type(obj) is PointOP3:
        result = _p5_pointE3(obj.toPointE3())
    elif type(obj) is CPlaneS2:
        result = _p5_cPlaneS2(obj, style)
    elif type(obj) is DCEL:
        result = _p5_dcel(obj, style)
    elif type(obj) is Edge:
        result = _p5_edge(obj, style)
    elif type(obj) is Face:
        result = _p5_face(obj, style)
    elif type(obj) is SegmentE3:
        result = _p5_segmentE3(obj, style)
    elif isinstance(obj, VertexColoredTriangle):
        result = obj.to_dict()
    else:
        result = None
    if result != None and style != None:
        result["style"] = style
    return result

### STYLE HANDLING

def makeStyle(stroke = None, strokeWeight = 1, fill = None):
    return {"stroke":       stroke, 
            "strokeWeight": strokeWeight, 
            "fill":         fill}

class DefaultStyles:
    
    RED_STROKE = makeStyle(stroke = "#ff0000", strokeWeight = 1)
    GREEN_STROKE = makeStyle(stroke = "#00ff00", strokeWeight = 1)
    BLUE_STROKE = makeStyle(stroke = "#0000ff", strokeWeight = 1)
    
    RED_FILL = makeStyle(fill = "#ff0000")
    GREEN_FILL = makeStyle(fill = "#00ff00")
    BLUE_FILL = makeStyle(fill = "#0000ff")

### THE ACTUAL VIEWER CLASSES
    
class S2Scene(Scene):
    def __init__(self, width=500, height=500, title=None):
        super().__init__(width = width, 
                         height = height, 
                         scale = 1.0, 
                         title = title, 
                         obj_json_convert_func = _p5_dict)

    def toggleSphere(self):
        self._sketch.showSphere = not self._sketch.showSphere
