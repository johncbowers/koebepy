
import pkgutil
import koebe.graphics.js.js
import anywidget
import traitlets
import marimo as mo

# For sending data to the JavaScript part
import json #json.dumps(obj)

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
    

class VertexColoredTriangle:
    def __init__(self, p1, p2, p3, color1, color2, color3):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.color1 = color1
        self.color2 = color2
        self.color3 = color3
    def to_dict(self):
        return {"type": "VertexColoredTriangle", 
                "p1":   tuple(self.p1), 
                "p2":   tuple(self.p2),
                "p3":   tuple(self.p3),
                "color1": self.color1,
                "color2": self.color2,
                "color3": self.color3}
    
class Scene:
    
    def __init__(self, width, height, scale, obj_json_convert_func):
        self._objs   = []
        self._anim   = []
        self._styles = {}
        self.obj_json_convert_func = obj_json_convert_func
        #self._sketch_class = SketchClass
        #self._sketch = mo.ui.anywidget(SketchClass())
    
    def _updateJson(self):
        self._json_string = self._toJson()
        #self._sketch.objectsDirty = True
    
    def update(self):
        self._updateJson()
    
    def setStyle(self, obj, style):
        self._styles[id(obj)] = style
        
    def setStyles(self, objs, style):
        for obj in objs:
            self.setStyle(obj, style)
    
    def getStyle(self, obj):
        if id(obj) in self._styles:
            return self._styles[id(obj)]
        else:
            return None
    
    def show(self, sketch_viewer):
        self._updateJson()
        sketch_viewer.objects = self._toJson()
        sketch_viewer.objectsDirty = True
    
    def add(self, obj, style = None):
        self._objs.append(obj)
        if (style != None):
            self.setStyle(obj, style)
    
    def addAll(self, objs):
        for obj in objs:
            if isinstance(obj, tuple):
                self._objs.append(obj[0])
                self.setStyle(obj[0], obj[1])
            else:
                self._objs.append(obj)
                
    def pushAnimFrame(self):
        self._anim.append(self._objs)
        self._objs = []
        
    def _toJson(self):
        frames = self._anim + [self._objs]
        return json.dumps(
            [[d for d in [self.obj_json_convert_func(o, self.getStyle(o)) for o in frame] if not d == None] 
             for frame in frames]
        )
    
    def jsonify(self):
        return self._toJson()