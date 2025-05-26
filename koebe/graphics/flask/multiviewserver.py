from flask import Flask, render_template, request, jsonify

class ViewerFlask(Flask):
    def __init__(self, App):
        super().__init__(App)
        self._next_id = 0
        self._scenes = []

    def add_scene(self, scene):
        self._scenes.append(scene)
        
    def jsonify_scenes(self):
        return [ {
                    "id": scene_idx, 
                    "type": type(self._scenes[scene_idx]).__name__, 
                    "objects": self._scenes[scene_idx].jsonify(), 
                    "background_objects": self._scenes[scene_idx].jsonifyBackground(needs_background_redraw=False) if self._scenes[scene_idx]._needs_background_redraw else "[]",
                    "title": "" if self._scenes[scene_idx].getTitle() == None else self._scenes[scene_idx].getTitle(),
                    "show_sphere": str(self._scenes[scene_idx].showSphere()).lower() if hasattr(self._scenes[scene_idx], "showSphere") else "false",
                    "show_light_cone": str(self._scenes[scene_idx].showLightCone()).lower() if hasattr(self._scenes[scene_idx], "showLightCone") else "false",
                    "scale": self._scenes[scene_idx].getScale(), 
                    "width": self._scenes[scene_idx].getWidth(),
                    "height": self._scenes[scene_idx].getHeight(), 
                    "pan_and_zoom": str(self._scenes[scene_idx].getPanAndZoom()).lower()
                 } 
                 for scene_idx in range(len(self._scenes))
                 ]

viewer = ViewerFlask(__name__)

@viewer.route('/')
def index():
    global viewer
    context = {"scenes":viewer.jsonify_scenes()}
    return render_template('multiview.html', **context)

# A route for getting keyboard and mouse events from p5.js in the
# browser, back to the server. 
@viewer.route('/event', methods=['POST'])
def event():
    
    data = request.get_json()
    event_type = data['type']

    if event_type == "key_pressed":
        if _key_pressed_handler is not None:
            _key_pressed_handler(data['key'])
    elif event_type == "key_released":
        if _key_released_handler is not None:
            _key_released_handler(data['key'])
    else:
        scene_id = data['scene_id']
        scene = viewer._scenes[scene_id]
        
        if event_type == "mouse_moved":
            scene.mouse_moved(data)
        elif event_type == "mouse_dragged":
            scene.mouse_dragged(data)
        elif event_type == "mouse_pressed":
            scene.mouse_pressed(data)
        elif event_type == "mouse_released":
            scene.mouse_released(data)
        elif event_type == "mouse_clicked":
            scene.mouse_clicked(data)
        elif event_type == "mouse_double_clicked":
            scene.mouse_double_clicked(data)
    
    scene_updates = [
        scene.jsonify() if scene.needsRedraw() else ""
        for scene in viewer._scenes
    ]

    for scene in viewer._scenes:
        scene.clearRedrawFlag()

    return jsonify({'result': "success", 'scene_updates': scene_updates})

@viewer.route('/add', methods=['POST'])
def add():
    data = request.get_json()
    num1 = data['num1']
    num2 = data['num2']
    result = num1 + num2
    return jsonify({'result': result})

if __name__ == '__main__':
    viewer.run(debug=True)

_key_pressed_handler = None
_key_released_handler = None

def set_key_pressed_handler(handler):
    global _key_pressed_handler
    _key_pressed_handler = handler

def set_key_released_handler(handler):
    global _key_released_handler
    _key_released_handler = handler