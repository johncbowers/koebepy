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
from traitlets import Unicode, Int, Bool

# For sending data to the JavaScript part
import json #json.dumps(obj)

# Packages for drawable objects
from koebe.geometries.euclidean3 import PointE3, SegmentE3
from koebe.geometries.spherical2 import DiskS2, PointS2, CPlaneS2
from koebe.geometries.orientedProjective3 import PointOP3
from koebe.datastructures.dcel import DCEL, Face, Edge, Vertex

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
    
class S2Viewer():
    def __init__(self, width=500, height=500):
        viewer_code = pkgutil.get_data("koebe.graphics.js.js", "spherical2viewer.js").decode("utf8")
        display(Javascript(viewer_code))
        self._sketch = S2Sketch(width=width, height=height)
        self._objs   = []
        self._styles = {}
    
    def _updateJson(self):
        self._sketch.objects = self._toJson()
        self._sketch.objectsDirty = True
    
    def setStyle(self, obj, style):
        self._styles[id(obj)] = style
        self._updateJson()
    
    def getStyle(self, obj):
        if id(obj) in self._styles:
            return self._styles[id(obj)]
        else:
            return None
    
    def show(self):
        display(self._sketch)
    
    def add(self, obj, style = None):
        self._objs.append(obj)
        if (style != None):
            self.setStyle(obj, style)
        self._updateJson()
    
    def addAll(self, objs):
        self._objs.extend(objs)
        self._updateJson()
        
    def _toJson(self):
        return json.dumps([d for d in [_p5_dict(o, self.getStyle(o)) for o in self._objs] if not d == None])
    
    def toggleSphere(self):
        self._sketch.showSphere = not self._sketch.showSphere
    

class S2Sketch(widgets.DOMWidget):
    # TODO Got this from the example I'm working off of, so I'm not sure if they are 
    # necessary, but don't have time to figure it out now. 
    _view_name = Unicode('S2SketchView').tag(sync=True)
    _view_module = Unicode('S2Sketch').tag(sync=True)
    _view_module_version = Unicode('1.0.0').tag(sync=True)
    
    # Viewport width and height
    width  = Int(300).tag(sync=True)
    height = Int(400).tag(sync=True)
    
    # objects is a JSON string containing data for all the objects to draw
    # objectsDirty should be set to true any time the objects string is updated
    # in order to flag the applet that it needs to decode the JSON again
    objects      = Unicode('[]').tag(sync=True)
    objectsDirty = Bool(True).tag(sync=True)
    
    showSphere   = Bool(True).tag(sync=True)
    