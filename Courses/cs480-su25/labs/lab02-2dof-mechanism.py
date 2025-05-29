
from koebe.geometries.euclidean2 import *

from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
grayFillStyle = makeStyle(stroke=(200, 200, 200), fill=(200, 200, 200))
blueStyle = makeStyle(stroke=(0,0,255), fill=(0, 0, 255), strokeWeight=2.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)

theta1 = 0
theta2 = 0
mouse_down = False
selected = False
arm1_length = 100
arm2_length = 100

obstacle1 = CircleE2(PointE2(130, 130), 20)
obstacle2 = CircleE2(PointE2(-50, -50), 20)

def arm_segments(arm1_length, arm2_length, theta1, theta2):
    # 2dof arm linkage mechanism, first angle is theta1, second angle is theta2
    # TODO
    # Create two segments representing the arms of the mechanism.
    # You may want to review the unit circle. 

    # These are dummy arms to fix: 
    arm1 = SegmentE2(PointE2(0, 0), PointE2(0, arm1_length))
    arm2 = SegmentE2(PointE2(0, arm1_length), PointE2(arm2_length, arm1_length))

    return arm1, arm2

def draw_mechanism():
    global mech_scene, theta1, theta2, obstacle1, obstacle2, arm1_length, arm2_length

    arm1, arm2 = arm_segments(arm1_length, arm2_length, theta1, theta2)
    
    mech_scene.add(arm1, blackStyle)
    mech_scene.add(arm2, blackStyle)

    # Draw obstacles
    mech_scene.add(obstacle1, blackStyle)
    mech_scene.add(obstacle2, blackStyle)

def draw_configuration_space():
    global configuration_space_scene, theta1, theta2, arm1_length, arm2_length, selected
    theta_pt = PointE2(theta1 * 250 / math.pi, theta2 * 250 / math.pi)

    configuration_space_scene.add(theta_pt, redStyle if selected else blueStyle)

def draw():
    global mech_scene, configuration_space_scene

    mech_scene.clear()
    configuration_space_scene.clear()

    draw_mechanism()
    draw_configuration_space()

def mouse_pressed(event):
    global mouse_down, selected
    mouse_down = True
    mouse_pt = PointE2(event['x'], event['y'])
    theta_pt = PointE2(theta1 * 250 / math.pi, theta2 * 250 / math.pi)
    selected = mouse_pt.distTo(theta_pt) < 10


def mouse_released(event):
    global mouse_down
    mouse_down = False
    selected = False

def mouse_moved(event):
    global mouse_down, theta1, theta2, selected

    if selected and mouse_down:
        x, y = event['x'], event['y']
        theta1 = x * math.pi / 250
        theta2 = y * math.pi / 250
        draw()
        

mech_scene = E2Scene(title="Mechanism")
configuration_space_scene = E2Scene(title="Configuration Space")

configuration_space_scene.set_mouse_pressed(mouse_pressed)
configuration_space_scene.set_mouse_released(mouse_released)
configuration_space_scene.set_mouse_moved(mouse_moved)
configuration_space_scene.set_mouse_dragged(mouse_moved)

# TODO
# Sample a grid of theta1 values between -250 and 250 each spaced 10 units apart, and a grid of theta2 values
# between -250 and 250 each spaced 10 units apart. For each (theta1, theta2) coordinate,
# use the current arm lengths and the theta1 and theta2 values to create two arm segments using the arm_segments function.
# If the arm segments do not intersect any of the obstacles, add a PointE2 object to the configuration_space_scene.
# When you add the PointE2 object to the configuration_space_scene, use the grayFillStyle.
#
# When you add these, instead of using .add to add them to the scene, use .addToBackground

configuration_space_scene.addToBackground(SegmentE2(PointE2(-250, 0), PointE2(250, 0)), blackStyle)
configuration_space_scene.addToBackground(SegmentE2(PointE2(0, -250), PointE2(0, 250)), blackStyle)

viewer.add_scene(mech_scene)
viewer.add_scene(configuration_space_scene)

draw()

viewer.run()
