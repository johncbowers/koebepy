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
    
    def __init__(self, width, height, scale, obj_json_convert_func, title=None, pan_and_zoom=False):
        self._objs   = []
        self._background_objs = []
        self._anim   = []
        self._styles = {}
        self._background_styles = {}
        self._title = title
        self.obj_json_convert_func = obj_json_convert_func
        #self._sketch_class = SketchClass
        #self._sketch = mo.ui.anywidget(SketchClass())
        self._key_pressed           = lambda evt: None
        self._key_released          = lambda evt: None
        self._mouse_moved           = lambda evt: None
        self._mouse_dragged         = lambda evt: None
        self._mouse_pressed         = lambda evt: None
        self._mouse_released        = lambda evt: None
        self._mouse_clicked         = lambda evt: None
        self._mouse_double_clicked  = lambda evt: None
        self._needs_redraw = False
        self._needs_background_redraw = False
        self._scale = scale
        self._width = width
        self._height = height
        self._pan_and_zoom = pan_and_zoom
    
    def getTitle(self): return self._title
    def getScale(self): return self._scale
    def getWidth(self): return self._width
    def getHeight(self): return self._height
    def getPanAndZoom(self): return self._pan_and_zoom

    def key_pressed(self, event): self._key_pressed(event)
    def key_released(self, event): self._key_released(event)
    def mouse_moved(self, event): self._mouse_moved(event)
    def mouse_dragged(self, event): self._mouse_dragged(event)
    def mouse_pressed(self, event): self._mouse_pressed(event)
    def mouse_released(self, event): self._mouse_released(event)
    def mouse_clicked(self, event): self._mouse_clicked(event)
    def mouse_double_clicked(self, event): self._mouse_double_clicked(event)
    
    def set_key_pressed(self, handler): self._key_pressed = handler
    def set_key_released(self, handler): self._key_released = handler
    def set_mouse_moved(self, handler): self._mouse_moved = handler
    def set_mouse_dragged(self, handler): self._mouse_dragged = handler
    def set_mouse_pressed(self, handler): self._mouse_pressed = handler
    def set_mouse_released(self, handler): self._mouse_released = handler
    def set_mouse_clicked(self, handler): self._mouse_clicked = handler
    def set_mouse_double_clicked(self, handler): self._mouse_double_clicked = handler

    def _updateJson(self):
        self._json_string = self._toJson()
        #self._sketch.objectsDirty = True
    
    def update(self):
        self._updateJson()
    
    def setStyle(self, obj, style):
        self._styles[id(obj)] = style
        self._needs_redraw = True
    
    def setBackgroundStyle(self, obj, style):
        self._background_styles[id(obj)] = style
        self._needs_background_redraw = True
        
    def setStyles(self, objs, style):
        for obj in objs:
            self.setStyle(obj, style)
        self._needs_redraw = True
    
    def setBackgroundStyles(self, objs, style):
        for obj in objs:
            self.setBackgroundStyle(obj, style)
        self._needs_background_redraw = True
    
    def getStyle(self, obj):
        if id(obj) in self._styles:
            return self._styles[id(obj)]
        else:
            return None
    
    def getBackgroundStyle(self, obj):
        if id(obj) in self._background_styles:
            return self._background_styles[id(obj)]
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
        self._needs_redraw = True
    
    def addToBackground(self, obj, style = None):
        self._background_objs.append(obj)
        if (style != None):
            self.setStyle(obj, style)
        self._needs_background_redraw = True
    
    def addAll(self, objs):
        for obj in objs:
            if isinstance(obj, tuple):
                self._objs.append(obj[0])
                self.setStyle(obj[0], obj[1])
            else:
                self._objs.append(obj)
        self._needs_redraw = True

    def addAllToBackground(self, objs):
        for obj in objs:
            if isinstance(obj, tuple):
                self._background_objs.append(obj[0])
                self.setStyle(obj[0], obj[1])
            else:
                self._background_objs.append(obj)
        self._needs_background_redraw = True          
    
    def pushAnimFrame(self):
        self._anim.append(self._objs)
        self._objs = []
        self._needs_redraw = True
        
    def _toJson(self):
        return json.dumps(
            self.get_json_objects_list()
        )
    
    def _toJsonBackground(self):
        return json.dumps(
            self.get_json_background_objects_list()
        )

    def get_json_objects_list(self):
        frames = self._anim + [self._objs]
        return [[d for d in [self.obj_json_convert_func(o, self.getStyle(o)) for o in frame] if not d == None] 
                for frame in frames]

    def get_json_background_objects_list(self):
        return [d for d in [self.obj_json_convert_func(o, self.getBackgroundStyle(o)) for o in self._background_objs] if not d == None]
    
    def jsonify(self):
        return self._toJson()
    
    def jsonifyBackground(self, needs_background_redraw=True):
        self._needs_background_redraw = needs_background_redraw
        return self._toJsonBackground()
    
    def needsRedraw(self):
        return self._needs_redraw
    
    def clearRedrawFlag(self):
        self._needs_redraw = False
    
    def clearBackgroundRedrawFlag(self):
        self._needs_background_redraw = False

    def clear(self):
        self._objs = []
        self._styles = {}
        self._needs_redraw = True