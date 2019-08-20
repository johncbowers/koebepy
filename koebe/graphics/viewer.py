
import pkgutil
import koebe.graphics.js.js
from IPython.display import display
from IPython.core.magics.display import Javascript

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
    
class Viewer:
    
    def __init__(self, width, height, scale, jsSketchFile, SketchClass, obj_json_convert_func):
        viewer_code = pkgutil.get_data("koebe.graphics.js.js", jsSketchFile).decode("utf8")
        display(Javascript(viewer_code))
        self._sketch = SketchClass(width=width, height=height, scale=scale)
        self._objs   = []
        self._styles = {}
        self.obj_json_convert_func = obj_json_convert_func
    
    def _updateJson(self):
        self._sketch.objects = self._toJson()
        self._sketch.objectsDirty = True
    
    def setStyle(self, obj, style, updateJson=True):
        self._styles[id(obj)] = style
        if (updateJson):
            self._updateJson()
        
    def setStyles(self, objs, style):
        for obj in objs:
            self.setStyle(obj, style)
    
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
            self.setStyle(obj, style, False)
        self._updateJson()
    
    def addAll(self, objs):
        for obj in objs:
            if isinstance(obj, tuple):
                self._objs.append(obj[0])
                self.setStyle(obj[0], obj[1], False)
            else:
                self._objs.append(obj)
        self._updateJson()
        
    def _toJson(self):
        return json.dumps([d for d in [self.obj_json_convert_func(o, self.getStyle(o)) for o in self._objs] if not d == None])