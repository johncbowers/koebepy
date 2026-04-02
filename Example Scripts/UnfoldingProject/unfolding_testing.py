
def check_for_intersections(unfolding, tol=1e-8) -> bool:
    """
    Checks for intersections through a brute force search of every pair
    of vertices.
    :param unfolding:
    :param tol:
    :return:
    """
    for i in range(len(unfolding.verts)):
        for j in range(i+1, len(unfolding.verts)):
            v_i = unfolding.verts[i]
            v_j = unfolding.verts[j]
            point_i = v_i.data.center
            point_j = v_j.data.center

            distance = point_i.distTo(point_j)
            sum_radii = v_i.data.radius + v_j.data.radius
            if sum_radii-tol > distance:
                return False
                # print(f"Overlap between {point_i} and {point_j} at tolerance {tol}"
                #       f"distance {distance} less than the sum of their radii {sum_radii}")
    return True

def inversive_distances_test(unfolding, packing, debug=False) -> bool:
    """
    Verifies an unfolding using the inversive distances test.
    :param unfolding:
    :param packing:
    :return:
    """

    inversive_distances_sphere = []
    inversive_distances_plane = []
    for i in range(len(unfolding.verts) - 1):
        for j in range(i + 1, len(unfolding.verts)):
            if unfolding.verts[j].parent != unfolding.verts[i] and unfolding.verts[i].parent != unfolding.verts[j] and \
                    unfolding.verts[i].data != None and unfolding.verts[j].data != None:
                inversive_distances_sphere.append(packing.verts[i].data.inversiveDistTo(packing.verts[j].data))
                inversive_distances_plane.append(unfolding.verts[i].data.inversiveDistTo(unfolding.verts[j].data))

    passed = True
    for i in range(len(inversive_distances_plane)):
        if inversive_distances_plane[i] < inversive_distances_sphere[i]:
            passed = False
            if debug:
                print(
                f"{i} {inversive_distances_plane[i]} {inversive_distances_sphere[i]} {inversive_distances_plane[i] - inversive_distances_sphere[i]} {inversive_distances_plane[i] > inversive_distances_sphere[i]}")

    if debug:
        print(
            f"Passes inversive distance test: {passed}")
        print(f"Minimum inversive distance detected in the sphere: {min(inversive_distances_sphere)}")
        print(f"Minimum inversive distance detected in the plane: {min(inversive_distances_plane)}")
    return passed

