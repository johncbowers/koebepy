from koebe.geometries.euclidean2 import *
from math import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
grayFillStyle = makeStyle(stroke=(230, 230, 230), fill=(230, 230, 230))
blueStyle = makeStyle(stroke=(0,0,255), fill=(0, 0, 255), strokeWeight=2.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)

# Arm lengths
arm1_length = 100
arm2_length = 200

# Obstacles
obstacle1 = CircleE2(PointE2(130, 130), 20)
obstacle2 = CircleE2(PointE2(-50, -50), 20)

# Selected configurations (max 2: start and goal)
configurations = []

# Grid resolution
step = 10
grid_range = range(-250, 250, step)

# Store free configurations
free_points = set()
grid_to_theta = {}


def arm_segments(arm1_length, arm2_length, theta1, theta2):
    # 2dof arm linkage mechanism, first angle is theta1, second angle is theta2
    arm1 = SegmentE2(PointE2(0, 0), PointE2(arm1_length * cos(theta1), arm1_length * sin(theta1)))
    arm2 = SegmentE2(PointE2(arm1_length * cos(theta1), arm1_length * sin(theta1)), 
                     PointE2(arm1_length * cos(theta1) + arm2_length * cos(theta1 + theta2), 
                             arm1_length * sin(theta1) + arm2_length * sin(theta1 + theta2)))
    return arm1, arm2

def draw_mechanism(theta1, theta2, style):
    global mech_scene
    arm1, arm2 = arm_segments(arm1_length, arm2_length, theta1, theta2)
    mech_scene.add(arm1, style)
    mech_scene.add(arm2, style)

def draw_configuration_space():
    global configuration_space_scene
    for idx, (theta1, theta2) in enumerate(configurations):
        theta_pt = PointE2(theta1 * 250 / pi, theta2 * 250 / pi)
        configuration_space_scene.add(theta_pt, redStyle if idx == 0 else blueStyle)


def build_graph():
    graph = {}
    dirs = [(step, 0), (-step, 0), (0, step), (0, -step)]
    for x, y in free_points:
        neighbors = []
        for dx, dy in dirs:
            nx = ((x + dx + 500) % 500) - 250
            ny = ((y + dy + 500) % 500) - 250
            if (nx, ny) in free_points:
                neighbors.append((nx, ny))
        graph[(x, y)] = neighbors
    return graph


def bfs(graph, start, goal):
    queue = deque([start])
    visited = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            path = []
            while current is not None:
                path.append(current)
                current = visited[current]
            return path[::-1]
        for neighbor in graph[current]:
            if neighbor not in visited:
                visited[neighbor] = current
                queue.append(neighbor)
    return []


def draw():
    global mech_scene, configuration_space_scene

    mech_scene.clear()
    configuration_space_scene.clear()

    # Draw obstacles
    mech_scene.add(obstacle1, blackStyle)
    mech_scene.add(obstacle2, blackStyle)

    for idx, (theta1, theta2) in enumerate(configurations):
        draw_mechanism(theta1, theta2, redStyle if idx == 0 else blueStyle)

    if len(configurations) == 2:
        
        # 1. Create a graph of locations in the configuration space. Each valid grid point (as 
        #    you already drew in the lab) is a vertex in the graph. A vertex is connected by an 
        #    edge to the vertices above, below, left, and right of it if the arm can reach that point. 
        #    Don't forget that the graph is a torus, meaning the right-most vertices connect to the left-most
        #    and the top-most vertices connect to the bottom-most.
        # 2. Plot a path from the first configuration to the second configuration in the configuration space
        #    using the graph you created in step 1, and your favorite graph traversal algorithm (think 
        #    back to CS 240 about breadth-first search or depth-first search).
        # 3. First show each intermediate configuration in the configuration space and check that its
        #    working, but after you've got that working insert calls to pushAnimFrame() to animate
        #    the motion of the robot arm. 
        

        graph = build_graph()

        # Convert selected configurations to grid coordinates
        start = (int(configurations[0][0] * 250 / pi / step) * step, int(configurations[0][1] * 250 / pi / step) * step)
        goal = (int(configurations[1][0] * 250 / pi / step) * step, int(configurations[1][1] * 250 / pi / step) * step)

        # Ensure points exist in free space
        if start not in free_points or goal not in free_points:
            print("Start or goal is invalid (in obstacle).")
            return

        path = bfs(graph, start, goal)

        # Animate along the path
        for px, py in path:
            configuration_space_scene.add(PointE2(px, py), redStyle)
            theta1 = px * pi / 250
            theta2 = py * pi / 250
            mech_scene.clear()
            mech_scene.add(obstacle1, blackStyle)
            mech_scene.add(obstacle2, blackStyle)
            draw_mechanism(theta1, theta2, blueStyle)
            mech_scene.pushAnimFrame()
            configuration_space_scene.pushAnimFrame()

    draw_configuration_space()


def mouse_pressed(event):
    theta1 = event['x'] * pi / 250
    theta2 = event['y'] * pi / 250
    configurations.append((theta1, theta2))
    if len(configurations) > 2:
        configurations.pop(0)
    draw()


mech_scene = E2Scene(title="Mechanism")
configuration_space_scene = E2Scene(title="Configuration Space")

configuration_space_scene.set_mouse_pressed(mouse_pressed)

# Precompute free configurations
for i in grid_range:
    for j in grid_range:
        arm1, arm2 = arm_segments(arm1_length, arm2_length, i * pi / 250, j * pi / 250)
        if not (arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2)):
            free_points.add((i, j))
            grid_to_theta[(i, j)] = (i * pi / 250, j * pi / 250)
            configuration_space_scene.addToBackground(PointE2(i, j), grayFillStyle)

viewer.add_scene(mech_scene)
viewer.add_scene(configuration_space_scene)

draw()
viewer.run()