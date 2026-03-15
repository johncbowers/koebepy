from koebe.geometries.euclidean2 import *

from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
grayFillStyle = makeStyle(stroke=(230, 230, 230), fill=(230, 230, 230))
blueStyle = makeStyle(stroke=(0,0,255), fill=(0, 0, 255), strokeWeight=2.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)


arm1_length = 100
arm2_length = 200

obstacle1 = CircleE2(PointE2(130, 130), 20)
obstacle2 = CircleE2(PointE2(-50, -50), 20)

configurations = []

def arm_segments(arm1_length, arm2_length, theta1, theta2):
    # 2dof arm linkage mechanism, first angle is theta1, second angle is theta2
    arm1 = SegmentE2(PointE2(0, 0), PointE2(arm1_length * cos(theta1), arm1_length * sin(theta1)))
    arm2 = SegmentE2(PointE2(arm1_length * cos(theta1), arm1_length * sin(theta1)), 
                     PointE2(arm1_length * cos(theta1) + arm2_length * cos(theta1 + theta2), 
                             arm1_length * sin(theta1) + arm2_length * sin(theta1 + theta2)))
    return arm1, arm2

def draw_mechanism(theta1, theta2, style):
    global mech_scene, obstacle1, obstacle2, arm1_length, arm2_length

    arm1, arm2 = arm_segments(arm1_length, arm2_length, theta1, theta2)
    
    mech_scene.add(arm1, style)
    mech_scene.add(arm2, style)


def draw_configuration_space():
    global configuration_space_scene, theta1, theta2, arm1_length, arm2_length, selected
    # theta_pt = PointE2(theta1 * 250 / math.pi, theta2 * 250 / math.pi)

    # configuration_space_scene.add(theta_pt, redStyle if selected else blueStyle)
    for idx, (theta1, theta2) in enumerate(configurations):
        theta_pt = PointE2(theta1 * 250 / math.pi, theta2 * 250 / math.pi)
        configuration_space_scene.add(theta_pt, redStyle if idx == 0 else blueStyle)

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
        # 1. Build the configuration space graph (valid points and adjacency)
        valid_points = []
        point_to_index = {}
        for i in range(-250, 250, 10):
            for j in range(-250, 250, 10):
                arm1, arm2 = arm_segments(arm1_length, arm2_length, i * math.pi / 250, j * math.pi / 250)
                if not (arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2)):
                    point_to_index[(i, j)] = len(valid_points)
                    valid_points.append((i, j))

        # Build adjacency list with torus wrapping
        graph = {idx: [] for idx in range(len(valid_points))}
        for idx, (x, y) in enumerate(valid_points):
            neighbors = [
                (x, ((y + 10 + 250) % 500 - 250)),  # up
                (x, ((y - 10 + 250) % 500 - 250)),  # down
                (((x + 10 + 250) % 500 - 250), y),  # right
                (((x - 10 + 250) % 500 - 250), y)   # left
            ]
            for nx, ny in neighbors:
                if (nx, ny) in point_to_index:
                    graph[idx].append(point_to_index[(nx, ny)])

        # 2. Find path using BFS
        def theta_to_grid(theta):
            return int(round(theta * 250 / math.pi / 10) * 10)

        start_theta1, start_theta2 = configurations[0]
        end_theta1, end_theta2 = configurations[1]
        start_grid = (theta_to_grid(start_theta1), theta_to_grid(start_theta2))
        end_grid = (theta_to_grid(end_theta1), theta_to_grid(end_theta2))

        if start_grid in point_to_index and end_grid in point_to_index:
            start_idx = point_to_index[start_grid]
            end_idx = point_to_index[end_grid]

            # BFS
            queue = deque([(start_idx, [start_idx])])
            visited = {start_idx}
            path = None
            while queue:
                current, path_so_far = queue.popleft()
                if current == end_idx:
                    path = path_so_far
                    break
                for neighbor in graph[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path_so_far + [neighbor]))

            if path:
                # 3. Draw path in configuration space
                path_points = [valid_points[idx] for idx in path]
                for i in range(len(path_points) - 1):
                    x1, y1 = path_points[i]
                    x2, y2 = path_points[i + 1]
                    configuration_space_scene.add(SegmentE2(PointE2(x1, y1), PointE2(x2, y2)), redStyle)

                # Show many keyframes of the mechanism along the path 
                num_keyframes = min(20, len(path))
                keyframe_indices = [int(i * (len(path) - 1) / (num_keyframes - 1)) for i in range(num_keyframes)]
                for idx in keyframe_indices:
                    mech_scene.clear()  
                    x, y = valid_points[path[idx]]
                    theta1 = x * math.pi / 250
                    theta2 = y * math.pi / 250
                    draw_mechanism(theta1, theta2, blueStyle)
                    mech_scene.pushAnimFrame()  
            else:
                print("No path found between the two configurations.")
        else:
            print("Start or end configuration is not in valid configuration space.")

    draw_configuration_space()

def mouse_pressed(event):
    global mouse_down, selected
    theta1 = event['x'] * math.pi / 250
    theta2 = event['y'] * math.pi / 250
    configurations.append((theta1, theta2))
    if len(configurations) > 2:
        configurations.pop(0)
    draw()

mech_scene = E2Scene(title="Mechanism")
configuration_space_scene = E2Scene(title="Configuration Space")

configuration_space_scene.set_mouse_pressed(mouse_pressed)

for i in range(-250, 250, 10):
    for j in range(-250, 250, 10):
        arm1, arm2 = arm_segments(arm1_length, arm2_length, i * math.pi / 250, j * math.pi / 250)
        if not (arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2)):
            configuration_space_scene.addToBackground(PointE2(i, j), grayFillStyle)

viewer.add_scene(mech_scene)
viewer.add_scene(configuration_space_scene)

draw()

viewer.run()
