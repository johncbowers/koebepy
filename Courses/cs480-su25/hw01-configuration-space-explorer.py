
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
purpleStyle = makeStyle(stroke=(128, 0, 128), fill=(128, 0, 128), strokeWeight=1.5)


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
        # TODO:
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
            mech_scene.clear()

            graph = [[] for _ in range(-250, 250, 10)] # make list of empty lists
            for i in range(50):
                for _ in range(50):
                    graph[i].append(1)


            for x in range(-250, 250, 10):
                for y in range(-250, 250, 10):
                    arm1, arm2 = arm_segments(arm1_length, arm2_length, (x * math.pi) / 250, (y * math.pi) / 250)
                    if arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2):
                        graph[y//10 + 25][x//10 + 25] = 0
            print("check")
            print(f"graph[39][21] should be 0, is {graph[39][21]}")
            print(f"graph[21][39] should be 1, is {graph[21][39]}")
            print(graph[0])

            start_graph = 0,0
            end_graph = 1,1
            fx,fy = configurations[0]
            cx = fx * 250 / math.pi
            cy = fy * 250 / math.pi
            gy, gx = round(cx / 10) * 10, round(cy / 10) * 10
            start_graph = gx//10 + 25, gy//10 + 25


            fx,fy = configurations[1]
            cx = fx * 250 / math.pi
            cy = fy * 250 / math.pi
            gy, gx = round(cx / 10) * 10, round(cy / 10) * 10
            end_graph = gx//10 + 25, gy//10 + 25
            print(start_graph)
            print(end_graph)


            def search(start):
                visited = dict()
                visited[start] = None
                queue = deque()
                queue.append(start)
                while (queue):
                    a = queue.popleft()
                    if a == end_graph:
                        path = []
                        while a:
                            path.append(a)
                            a = visited[a]

                        return path[::-1]
                    else:
                        ar, ac = a
                        north = (ar + 1) % 50, ac
                        south = (ar - 1) % 50, ac
                        west = ar, (ac - 1) % 50
                        east = ar, (ac + 1) % 50
                        neigh = [north, south, east, west]
                        good_neigh = []
                        for n in neigh:
                            # if n good add to good
                            if graph[n[0]][n[1]] == 1:
                                good_neigh.append(n)
                        #print(f"{good_neigh = }")
                        for n in good_neigh:
                            if n not in visited:
                                visited[n] = a
                                queue.append(n)
                return "bad"

            print(search(start_graph))
            path = search(start_graph)
            if not path:
                print("bad path :(")
                return 0
            else:
                for i in path:
                    cx = (i[0] - 25) * 10 * math.pi / 250
                    cy = (i[1] - 25) * 10 * math.pi / 250
                    draw_mechanism(cy, cx, purpleStyle)
                    mech_scene.add(obstacle1, blackStyle)
                    mech_scene.add(obstacle2, blackStyle)

                    for idx, (theta1, theta2) in enumerate(configurations):
                        draw_mechanism(theta1, theta2, redStyle if idx == 0 else blueStyle)
                    mech_scene.pushAnimFrame()


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
