
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

#graph implementation 
class Graph: 
    def __init__(self):
        self.graph = {}

    def add_node(self, coord):
        if coord not in self.graph:
            self.graph[coord] = []

    def add_edge(self, coord1, coord2):
        self.add_node(coord1)
        self.add_node(coord2)

        if coord2 not in self.graph[coord1]:
            self.graph[coord1].append(coord2)
        if coord1 not in self.graph[coord2]:
            self.graph[coord2].append(coord1)
    def get_neighbors(self, coord):
        return self.graph.get(coord, [])

    def bfs(self, start, goal):
        if start not in self.graph or goal not in self.graph:
            return None
            
        queue = deque([(start, [start])])
        visited = set()
        
        while queue:
            current, path = queue.popleft()
            
            if current == goal:
                return path
                
            if current not in visited:
                visited.add(current)
                for neighbor in self.graph[current]:
                    if neighbor not in visited:
                        queue.append((neighbor, path + [neighbor]))
        
        return None
        
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
        mech_scene.clearAnimFrames()
        for t1 in range(-250, 250, 10):
            for t2 in range(-250, 250, 10):
                cur_theta1 = t1/250 * math.pi
                cur_theta2 = t2/250 * math.pi
                arm1, arm2 = arm_segments(arm1_length, arm2_length, cur_theta1, cur_theta2)
                if not (arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2)):
                    pos = PointE2(t1, t2)
                    configuration_space_scene.addToBackground(pos, grayFillStyle)
                

        #building graph
        config_graph = Graph()

        for i in range(-250, 250, 10):
            for j in range(-250, 250, 10):
                arm1, arm2 = arm_segments(arm1_length, arm2_length, i * math.pi / 250, j * math.pi / 250)
                if not (arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2)):
                    config_graph.add_node((i, j))
                    
                    arm1, arm2 = arm_segments(arm1_length, arm2_length, (i - 10) * math.pi / 250, j * math.pi / 250)
                    if not (arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2)):
                        config_graph.add_edge((i, j), ((i - 10), j))
                        
                    arm1, arm2 = arm_segments(arm1_length, arm2_length, i * math.pi / 250, (j - 10) * math.pi / 250)
                    if not (arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2)):
                        config_graph.add_edge((i, j), (i, (j - 10)))
                    if j == 240:
                        arm1, arm2 = arm_segments(arm1_length, arm2_length, i * math.pi / 250, -math.pi)
                        if not (arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2)):
                            config_graph.add_edge((i, j), (i, -250))
                    if i == 240:
                        arm1, arm2 = arm_segments(arm1_length, arm2_length, -math.pi, j * math.pi / 250)
                        if not (arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2)):
                            config_graph.add_edge((i, j), (-250, j))
                    

        #rounding to find nearest graph node to start/end locations
        start = (round(configurations[0][0] / math.pi * 250, -1), round(configurations[0][1] / math.pi * 250, -1))
        end = (round(configurations[1][0] / math.pi * 250, -1), round(configurations[1][1] / math.pi * 250, -1))

        #routing and showing path in configuration space
        path = config_graph.bfs(start, end)
        for cord in path:
            pos = PointE2(cord[0], cord[1])
            configuration_space_scene.add(pos, redStyle)

        #animating path
        for cord in path:
            draw_mechanism(cord[0] * math.pi/250, cord[1] * math.pi/250, redStyle)
            draw_mechanism(end[0] * math.pi/250 , end[1] * math.pi/250 , blueStyle)
            mech_scene.add(obstacle1, blackStyle)
            mech_scene.add(obstacle2, blackStyle)
            mech_scene.pushAnimFrame()
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
        pass 

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
