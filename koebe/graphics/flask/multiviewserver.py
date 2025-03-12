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

@viewer.route('/add', methods=['POST'])
def add():
    data = request.get_json()
    num1 = data['num1']
    num2 = data['num2']
    result = num1 + num2
    return jsonify({'result': result})

if __name__ == '__main__':
    viewer.run(debug=True)

