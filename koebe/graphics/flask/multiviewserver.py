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
                    "title": "" if self._scenes[scene_idx].getTitle() == None else self._scenes[scene_idx].getTitle()
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
    print(f"Received event: {request.get_json()}")
    data = request.get_json()
    event_type = data['type']
    scene_id = data['scene_id']
    scene = viewer._scenes[scene_id]
    if event_type == "keyPressed":
        scene.key_pressed(data['key'])
    elif event_type == "keyReleased":
        scene.key_released(data['key'])
    elif event_type == "mouseMoved":
        scene.mouse_moved(data)
    elif event_type == "mouseDragged":
        scene.mouse_dragged(data)
    elif event_type == "mousePressed":
        scene.mouse_pressed(data)
    elif event_type == "mouseReleased":
        scene.mouse_released(data)
    elif event_type == "mouseClicked":
        scene.mouse_clicked(data)
    elif event_type == "mouseDoubleClicked":
        scene.mouse_double_clicked(data)
    
    scene_updates = [
        scene.jsonify() if scene.needsRedraw() else None
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

