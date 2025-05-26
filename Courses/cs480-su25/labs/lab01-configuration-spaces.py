
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *

from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
# from koebe.graphics.scenes.euclidean3scene import E3Scene, makeStyle
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle
from koebe.graphics.scenes.euclidean2scene import E2Scene

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
blueStyle = makeStyle(stroke=(0,0,255), fill=(255, 0, 0), strokeWeight=2.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)
greenStyle = makeStyle(stroke=(0,255,0), fill=(0, 255, 0), strokeWeight=2.0)

ship_position = PointE2(0, 0)
ship_rotation = 0

def ship_polygon(ship_position, ship_rotation):
    forward_vector = VectorE2(cos(ship_rotation), sin(ship_rotation))
    
    nose_cone_point = forward_vector * 30 
    ship_left_point = forward_vector.rotate(-pi/2) * 15
    ship_right_point = forward_vector.rotate(pi/2) * 15

    barycenter = (nose_cone_point + ship_left_point + ship_right_point) * (1/3) - PointE2.O

    return PolygonE2([
        ship_position + (p - barycenter)
        for p in [nose_cone_point, ship_left_point, ship_right_point]
    ])

def obstacle_polygon(position, scale=1):
    # asteroid shape PolygonE2 with twelve points
    # draw asteroid that looks like the original asteroids game
    return PolygonE2([
        position + scale * PointE2( 12,  -8),
        position + scale * PointE2(  8, -16),
        position + scale * PointE2( -2, -18),
        position + scale * PointE2(-16, -10),
        position + scale * PointE2(-24,   0),
        position + scale * PointE2(-20,  10),
        position + scale * PointE2(-12,  18),
        position + scale * PointE2( -2,  14),
        position + scale * PointE2(  6,  20),
        position + scale * PointE2( 18,  14),
        position + scale * PointE2( 24,   4),
        position + scale * PointE2( 20,  -4),
    ])

def generate_asteroid_scene_geometry(asteroids_scene, configuration_space_1, configuration_space_2, configuration_space_3):
    global ship_position, ship_rotation

    ship_poly = ship_polygon(ship_position, ship_rotation)

    asteroids_scene.add(ship_poly, blackStyle)
    
    # Generate the same obstacle polygons but in a list: 
    obstacles = [
        obstacle_polygon(PointE2(100, 100)),
        obstacle_polygon(PointE2(-200, 100), scale=1.5),
        obstacle_polygon(PointE2(200, 200), scale=2),
        obstacle_polygon(PointE2(-100, -200), scale=0.5),
        obstacle_polygon(PointE2(-100, 200), scale=0.75),
        obstacle_polygon(PointE2(100, -200), scale=0.25)
    ]

    # Add the obstacles to the scene
    asteroids_scene.addAll([(ob, redStyle if ob.intersects(ship_poly) else blackStyle) for ob in obstacles])

    # TODO
    # Sample a grid of x values between -250 and 250 and y values between -250 and 250 each spaced 10 units apart. 
    # For each (x, y) coordinate, use the current ship's rotation and the x, y coordinate and add a PointE2 object
    # to the configuration_space_1 scene if the ship polygon at (x, y) with rotation ship_rotation does not intersect
    # any of the obstacles. When you add the PointE2 object to the configuration_space_1 scene, use the blackStyle. 

    # Show the actual ship position in the configuration space:
    configuration_space_1.add(ship_position, redStyle)

    # TODO
    # Sample a grid of x values between -250 and 250 each spaced 10 units apart, and a grid of rotation values
    # between 0 and 360 degrees each spaced 7 degrees apart. For each (x, theta) coordinate,
    # use the current ship's y coordinate and the x coordinate and theta value to create a PointE2 object. (Use the radians(degrees)
    # function to convert degrees to radians.) If the ship polygon at (x, y) with rotation theta does not intersect
    # any of the obstacles, add a PointE2 object to the configuration_space_2 scene. When you add the PointE2 object
    # to the configuration_space_2 scene, use the blackStyle.
    # To convert the theta value of the rotation to a viewer point, you can use the formula: 500 * (theta / 360) - 250)

    # Show the actual ship position in teh configuration space
    configuration_space_2.add(PointE2(ship_position.x, 500 * (degrees(ship_rotation) / 360) - 250), redStyle)

    # TODO
    # Sample a grid of x values between -250 and 250 each spaced 25 units apart, a grid of y values between -250 and 250 each spaced 25 units apart,
    # and a grid of rotation values between 0 and 360 degrees each spaced 18 degrees apart. For each (x, y, theta) coordinate,
    # use the current ship's position and the x, y coordinate and theta value to create a PointE3 object. (Use the radians(degrees)
    # function to convert degrees to radians.) If the ship polygon at (x, y) with rotation theta does not intersect
    # any of the obstacles, add a PointE3 object to the configuration_space_3 scene. When you add the PointE3 object
    # to the configuration_space_3 scene, use the greenStyle.
    # To convert the x and y coordinates to viewer points, you can use the formula: x / 250 and y / 250.
    # To convert the theta value of the rotation to a viewer point, you can use the formula: theta / 180 - 1.0)
    
    # Show the actual ship position in the configuration space
    configuration_space_3.add(PointE3(ship_position.x / 250, ship_position.y / 250, degrees(ship_rotation) / 180 - 1.0), redStyle)

def draw(asteroids_scene, configuration_space_1, configuration_space_2, configuration_space_3):
    generate_asteroid_scene_geometry(asteroids_scene, configuration_space_1, configuration_space_2, configuration_space_3)

def key_pressed_handler(key):
    pass

def key_released_handler(key):
    if key == "a":
        global ship_rotation
        ship_rotation += 0.3
    elif key == "d":
        ship_rotation -= 0.3
    elif key == "w":
        global ship_position
        forward_vector = VectorE2(cos(ship_rotation), sin(ship_rotation))
        ship_position += forward_vector * 25
    
    ship_scene.clear()
    configuration_space_1.clear()
    configuration_space_2.clear()
    configuration_space_3.clear()

    draw(ship_scene, configuration_space_1, configuration_space_2, configuration_space_3)

ship_scene = E2Scene(title="Asteroids Simulation")
configuration_space_1 = E2Scene(title="Configuration Space 1")
configuration_space_2 = E2Scene(title="Configuration Space 2")
configuration_space_3 = S2Scene(title="Configuration Space 3")
configuration_space_3.toggleSphere()
#lifting_scene = E3Scene(title="Polyhedral Lifting")

set_key_pressed_handler(key_pressed_handler)
set_key_released_handler(key_released_handler)

draw(ship_scene, configuration_space_1, configuration_space_2, configuration_space_3)

viewer.add_scene(ship_scene)
viewer.add_scene(configuration_space_1)
viewer.add_scene(configuration_space_2)
viewer.add_scene(configuration_space_3)
#viewer.add_scene(lifting_scene)

viewer.run()
