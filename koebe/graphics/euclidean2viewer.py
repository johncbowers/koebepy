#
# Bindings to emit p5.js code
# @author John C. Bowers
#

# Packages for loading JavaScript:
import pkgutil
import koebe.graphics.js.js
from IPython.display import display
from IPython.core.magics.display import Javascript

# Packages for dealing with widgets: 
import ipywidgets as widgets
from traitlets import Unicode, Int, Bool, Float

# For sending data to the JavaScript part
import json #json.dumps(obj)

# Packages for drawable objects
from koebe.geometries.euclidean2 import PointE2, SegmentE2, CircleE2
from koebe.geometries.orientedProjective2 import PointOP2, DiskOP2, SegmentOP2
from koebe.geometries.hyperbolic2 import CircleH2
from koebe.datastructures.dcel import DCEL, Face, Edge, Vertex

from .viewer import Viewer
from .viewer import makeStyle as _makeStyle
# Use should be:
# from euclidean2viewer import E2Viewer
#
# viewer = E2Viewer()
# viewer.show()
#

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
    return _p5_segmentE3((_pointTypes_to_E2(edge.aDart.origin.data), 
                          _pointTypes_to_E2(edge.aDart.dest.data)), 
                         style)

def _p5_segmentE2(seg, style):
    result = {"type": "SegmentE2", 
            "endpoints": tuple(seg)}
    if style == None:
        result["style"] = makeStyle(stroke = "#000", strokeWeight = 2)
    return result

def _p5_circleE2(circle, style):
    result = {"type": "CircleE2", 
              "center": tuple(circle.center), 
              "radius": circle.radius}
    if style == None:
        result["style"] = makeStyle(stroke = "#000", strokeWeight = 1)
    return result

def _p5_dict(obj, style):
    
    if type(obj) is Vertex:
        obj = obj.data    
    if type(obj) is PointE2:
        result = _p5_pointE2(obj)
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
    elif type(obj) is SegmentE2:
        result = _p5_segmentE2(obj, style)
    elif type(obj) is SegmentOP2:
        result = _p5_segmentE2(SegmentE2(obj.source.toPointE2(), 
                                         obj.target.toPointE2()), style)
    else:
        result = None
    if result != None and style != None:
        result["style"] = style
    return result


### THE ACTUAL VIEWER CLASSES
    
class E2Viewer(Viewer):
    def __init__(self, width=500, height=500, scale=1.0):
        super().__init__(width = width, 
                         height = height, 
                         scale = scale, 
                         jsSketchFile = "euclidean2viewer.js", 
                         SketchClass = E2Sketch,
                         obj_json_convert_func = _p5_dict)
    
class PoincareDiskViewer(E2Viewer):
    def __init__(self, width=500, height=500):
        super().__init__(width  = width, 
                         height = height, 
                         scale  = 1.0 / (min(width, height)*0.5-10))
        self.unitDisk = CircleE2(PointE2(0,0), 1.0)
        self.add(self.unitDisk)
        
class UnitScaleE2Sketch(E2Viewer):
    def __init__(self, width=500, height=500):
        super().__init__(width  = width, 
                         height = height, 
                         scale  = 1.0 / (min(width, height)*0.5-10))

class E2Sketch(widgets.DOMWidget):
    # TODO Got this from the example I'm working off of, so I'm not sure if they are 
    # necessary, but don't have time to figure it out now. 
    _view_name = Unicode('E2SketchView').tag(sync=True)
    _view_module = Unicode('E2Sketch').tag(sync=True)
    _view_module_version = Unicode('1.0.0').tag(sync=True)
    
    # Viewport width and height
    width  = Int(300).tag(sync=True)
    height = Int(400).tag(sync=True)
    scale  = Float(1.0).tag(sync=True)
    
    # objects is a JSON string containing data for all the objects to draw
    # objectsDirty should be set to true any time the objects string is updated
    # in order to flag the applet that it needs to decode the JSON again
    objects      = Unicode('[]').tag(sync=True)
    objectsDirty = Bool(True).tag(sync=True)
    