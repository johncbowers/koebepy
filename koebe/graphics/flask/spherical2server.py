from flask import Flask, render_template, request, jsonify

viewer = Flask(__name__)
viewer.objects = "[[]]"

def _loadScene(scene):
    global viewer
    viewer.objects = scene.jsonify()

viewer.loadScene = _loadScene

@viewer.route('/')
def index():
    global viewer
    context = {"objects":viewer.objects}
    return render_template('spherical2view.html', **context)

@viewer.route('/add', methods=['POST'])
def add():
    data = request.get_json()
    num1 = data['num1']
    num2 = data['num2']
    result = num1 + num2
    return jsonify({'result': result})

if __name__ == '__main__':
    viewer.run(debug=True)

