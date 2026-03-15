
from koebe.geometries.euclidean2 import *

from math import *
from random import *
from collections import defaultdict, deque

from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle

blackStyle = makeStyle(stroke=(0, 0, 0), fill=(255, 255, 255))
grayFillStyle = makeStyle(stroke=(230, 230, 230), fill=(230, 230, 230))
blueStyle = makeStyle(stroke=(0, 0, 255), fill=(0, 0, 255), strokeWeight=2.0)
redStyle = makeStyle(stroke=(255, 0, 0), fill=(255, 0, 0), strokeWeight=2.0)


arm1_length = 100
arm2_length = 200

obstacle1 = CircleE2(PointE2(130, 130), 20)
obstacle2 = CircleE2(PointE2(-50, -50), 20)

configurations = []
valid = set()


def generate_configuration_space():
    global valid
    min_coord, max_coord, step = -250, 240, 10
    for i in range(min_coord, max_coord + 1, step):
        for j in range(min_coord, max_coord + 1, step):
            theta1 = i * pi / 250
            theta2 = j * pi / 250
            arm1, arm2 = arm_segments(arm1_length, arm2_length, theta1, theta2)
            if not (arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or
                    arm2.intersects(obstacle1) or arm2.intersects(obstacle2)):
                pt = PointE2(i, j)
                configuration_space_scene.addToBackground(pt, grayFillStyle)
                valid.add(pt)


def arm_segments(arm1_length, arm2_length, theta1, theta2):
    # 2dof arm linkage mechanism, first angle is theta1, second angle is theta2
    arm1 = SegmentE2(PointE2(0, 0), PointE2(
        arm1_length * cos(theta1), arm1_length * sin(theta1)))
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
        configuration_space_scene.add(
            theta_pt, redStyle if idx == 0 else blueStyle)


def draw():
    #         # 1. Create a graph of locations in the configuration space. Each valid grid point (as
    #         #    you already drew in the lab) is a vertex in the graph. A vertex is connected by an
    #         #    edge to the vertices above, below, left, and right of it if the arm can reach that point.
    #         #    Don't forget that the graph is a torus, meaning the right-most vertices connect to the left-most
    #         #    and the top-most vertices connect to the bottom-most.
    #         # 2. Plot a path from the first configuration to the second configuration in the configuration space
    #         #    using the graph you created in step 1, and your favorite graph traversal algorithm (think
    #         #    back to CS 240 about breadth-first search or depth-first search).
    #         # 3. First show each intermediate configuration in the configuration space and check that its
    #         #    working, but after you've got that working insert calls to pushAnimFrame() to animate
    #         #    the motion of the robot arm.
    mech_scene.clear()

    # Draw obstacles
    mech_scene.addToBackground(obstacle1, blackStyle)
    mech_scene.addToBackground(obstacle2, blackStyle)

    # Build graph of reachable neighbors
    graph = defaultdict(list)
    min_coord, max_coord, step = -250, 250, 10

    def wrap(i):
        if i < min_coord:
            return max_coord
        elif i > max_coord:
            return min_coord
        return i

    for point in valid:
        i, j = int(point.x), int(point.y)
        neighbors = [
            (wrap(i + step), j),
            (wrap(i - step), j),
            (i, wrap(j + step)),
            (i, wrap(j - step))
        ]
        for ni, nj in neighbors:
            neighbor = PointE2(ni, nj)
            if neighbor in valid:
                graph[point].append(neighbor)

    # Convert angle
    def angle_to_point(theta1, theta2):
        i = round((theta1 * 250 / math.pi) / 10) * 10
        j = round((theta2 * 250 / math.pi) / 10) * 10
        return PointE2(i, j)

    def bfs_path(graph, start, goal):
        queue = deque([start])
        came_from = {start: None}
        while queue:
            current = queue.popleft()
            if current == goal:
                break
            for neighbor in graph[current]:
                if neighbor not in came_from:
                    came_from[neighbor] = current
                    queue.append(neighbor)

        if goal not in came_from:
            return None

        path = []
        curr = goal
        while curr:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        return path

    for idx, (theta1, theta2) in enumerate(configurations):
        draw_mechanism(theta1, theta2, redStyle if idx == 0 else blueStyle)

    if len(configurations) == 2:
        start_theta = configurations[0]
        goal_theta = configurations[1]
        start = angle_to_point(*start_theta)
        goal = angle_to_point(*goal_theta)

        if start in valid and goal in valid:
            path = bfs_path(graph, start, goal)
            if path:
                for p in path:
                    theta1 = p.x * pi / 250
                    theta2 = p.y * pi / 250
                    draw_mechanism(theta1, theta2, redStyle)
                    mech_scene.pushAnimFrame()
        else:
            print("not good")

    draw_configuration_space()


def mouse_pressed(event):
    global mouse_down, selected
    theta1 = round(event['x'] / 10) * 10 * math.pi / 250
    theta2 = round(event['y'] / 10) * 10 * math.pi / 250
    configurations.append((theta1, theta2))
    if len(configurations) > 2:
        configurations.pop(0)
    draw()


mech_scene = E2Scene(title="Mechanism")
configuration_space_scene = E2Scene(title="Configuration Space")

configuration_space_scene.set_mouse_pressed(mouse_pressed)


viewer.add_scene(mech_scene)
viewer.add_scene(configuration_space_scene)

generate_configuration_space()
draw()

viewer.run()
