
from koebe.geometries.euclidean2 import *

from math import *
from random import *
from collections import deque
from time import sleep

from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
grayFillStyle = makeStyle(stroke=(230, 230, 230), fill=(230, 230, 230))
blueStyle = makeStyle(stroke=(0,0,255), fill=(0, 0, 255), strokeWeight=2.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)
purpleStyle = makeStyle(stroke=(128,0,128), fill=(128, 0, 128), strokeWeight=1.0)



arm1_length = 100
arm2_length = 200

obstacle1 = CircleE2(PointE2(130, 130), 20)
obstacle2 = CircleE2(PointE2(-50, -50), 20)

configurations = []
anime = False

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
    global mech_scene, configuration_space_scene, anime, configurations

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
        mech_scene.clearAnimFrames()
        graph = [[1 for _ in range(-250, 250, 10)] for __ in range(-250,250,10)]
        for i in range(-250, 250, 10):
            for j in range(-250, 250, 10):
                arm1, arm2 = arm_segments(arm1_length, arm2_length, i * math.pi / 250, j * math.pi / 250)
                if arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2):
                    graph[(j // 10)+25][(i // 10)+25] = 0


        # 2. Plot a path from the first configuration to the second configuration in the configuration space
        #    using the graph you created in step 1, and your favorite graph traversal algorithm (think 
        #    back to CS 240 about breadth-first search or depth-first search).
        def s_t_g(c):
            x,y = [round(((a*250)/math.pi) / 10) * 10 for a in c]
            return y,x
        def coordinates_to_graph(c):
            nx,ny = [(a // 10)+25 for a in c]
            return nx,ny
        
        l = len(graph)
        start_cord, goal_cord = [s_t_g(x) for x in configurations]
        # print(f"{start_cord = }")
        # print(f"{goal_cord = }")
        start_graph, goal_graph = [coordinates_to_graph(x) for x in [start_cord, goal_cord]]
        print(f"{start_graph = }")
        print(f"{goal_graph = }")
        def bfs(node):
            visited = dict()
            visited[node] = None
            queue = deque()
            queue.append(node)
            while queue:
                n = queue.popleft()
                if n == goal_graph:
                    path = []
                    while n:
                        path.append(n)
                        n = visited[n]
                    return path[::-1]
                r,c = n
                for neigh in [(row, col) for row, col in [(R%l, C%l) for R,C in [(r+1,c), (r,c+1), (r-1,c),(r,c-1)]] if graph[row][col]]:
                    if neigh not in visited:
                        visited[neigh] = n
                        queue.append(neigh)
        
        path = bfs(start_graph)
        if not path:
            print("no good")
            return 0
        else:
            print(f"{path[1:] = }")

        path = path[1:]
        def graph_to_coordinates(c):
            cx,cy = [(a-25)*10 for a in c]
            return cx* math.pi / 250, cy* math.pi / 250
        # t1,t2 = graph_to_coordinates(path[0])
        # draw_mechanism(t2, t1 ,purpleStyle)
        # mech_scene.pushAnimFrame()

        for p in path:
            mech_scene.pushAnimFrame()
            t1,t2 = graph_to_coordinates(p)
            g1,g2 = graph_to_coordinates(goal_graph)
            draw_mechanism(g2, g1, blueStyle)
            draw_mechanism(t2, t1 ,redStyle)
            mech_scene.add(obstacle1, blackStyle)
            mech_scene.add(obstacle2, blackStyle)
        # anime = True
        # for p in path:
        #     t1,t2 = graph_to_coordinates(p)
        #     configurations[0] = t2,t1
        # mech_scene.pushAnimFrame()
        # configurations = []
        
        
        
        # configuration_space_scene.addAll([(graph_to_coordinates(g),purpleStyle)] for g in path)
        

        # 3. First show each intermediate configuration in the configuration space and check that its
        #    working, but after you've got that working insert calls to pushAnimFrame() to animate
        #    the motion of the robot arm. 

        pass 

    draw_configuration_space()



def mouse_pressed(event):
    global mouse_down, selected
    # print(f"{event['x'] = }")
    # print(f"{event['y'] = }")

    theta1 = event['x'] * math.pi / 250
    theta2 = event['y'] * math.pi / 250
    configurations.append((theta1, theta2))
    if len(configurations) > 2:
        configurations.pop(0)
    draw()


def key_pressed(key):
    if key == "c":
        print(f"Key pressed: {key}")
        global configurations, mech_scene
        configurations = []
        mech_scene.clearAnimFrames()
        draw()

# 3. When the user clicks the 'f' key, flip the vertices across the chain of the 
#    polygon edge returned by find_chull_edge. Show the old flip edge in red, 
#    the old chain in blue, and the new chain in black.
def key_released(key):
    global configurations
    if key == "c":
        configurations = []
    draw()

mech_scene = E2Scene(title="Mechanism")
configuration_space_scene = E2Scene(title="Configuration Space")

configuration_space_scene.set_mouse_pressed(mouse_pressed)

for i in range(-250, 250, 10):
    for j in range(-250, 250, 10):
        arm1, arm2 = arm_segments(arm1_length, arm2_length, i * math.pi / 250, j * math.pi / 250)
        if not (arm1.intersects(obstacle1) or arm1.intersects(obstacle2) or arm2.intersects(obstacle1) or arm2.intersects(obstacle2)):
            configuration_space_scene.addToBackground(PointE2(i, j), grayFillStyle)

set_key_pressed_handler(key_pressed)
set_key_released_handler(key_released)


viewer.add_scene(mech_scene)
viewer.add_scene(configuration_space_scene)

draw()

viewer.run()
