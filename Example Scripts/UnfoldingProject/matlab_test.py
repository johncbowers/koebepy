import math
import matlab.engine

from koebe.datastructures.dcel import DCEL, Vertex


def flatten_matlab_array(arr):
    """
    Flatten a matlab array into a python generator. Works for arrays of at
    most two levels of nesting.
    :param arr:
    :return:
    """
    for item in arr:
        if isinstance(item, matlab.double):
            for sub_item in item:
                yield sub_item
        else:
            yield item


def to_int_list(values):
    """Convert a MATLAB numeric row/column to a Python list of ints."""
    out = []
    for item in flatten_matlab_array(values):
        out.append(int(item))
    return out


def spherical_angles_to_xyz(c):
    """
    GOPack randomSphere centers are encoded as theta + i*phi.
    Convert spherical angles (theta, phi) to unit sphere (x, y, z).
    :param c: Complex value with real(theta), imag(phi)
    :return: (x, y, z)
    """
    c = complex(c)
    theta = c.real
    phi = c.imag
    sphi = math.sin(phi)
    x = sphi * math.cos(theta)
    y = sphi * math.sin(theta)
    z = math.cos(phi)
    return x, y, z


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec_norm(a):
    return math.sqrt(dot(a, a))


def normalize(a):
    n = vec_norm(a)
    if n <= 1e-15:
        return (0.0, 0.0, 0.0)
    return (a[0] / n, a[1] / n, a[2] / n)


def construct_dcel_from_packing_info(flower_list, center_list, radius_list) -> DCEL:
    dcel = DCEL()
    for i in range(len(flower_list)):
        vertex = Vertex(dcel)
        # vertex.data =


if __name__ == "__main__":
    eng = matlab.engine.start_matlab()
    eng.addpath("C:/Users/lgabe/OneDrive/Desktop/cs497/GOPack/GOPack/code")

    gop = eng.randomSphere(10)
    eng.riffle(gop, 7, nargout=3)

    eng.workspace["gop"] = gop
    centers = eng.eval("gop.centers", nargout=1)
    radii = eng.eval("gop.radii", nargout=1)
    flowers = eng.eval("gop.flowers", nargout=1)

    center_values = list(flatten_matlab_array(centers))
    radius_values = list(flatten_matlab_array(radii))
    flower_values = list(flatten_matlab_array(flowers))

    # Step 1: inspect flower ordering data exactly as stored by GOPack.

    # Step 2: convert complex centers to xyz on the unit sphere.
    print("Centers in (x, y, z) on unit sphere:")
    for i, center in enumerate(center_values):
        x, y, z = spherical_angles_to_xyz(center)
        center_values[i] = (x, y, z)

    # Step 3: verify cyclic orientation consistency in each flower.
    print("\nFlower orientation audit (CCW wrt outward normal):")
    print("\nRadii:")
    for i, radius in enumerate(radius_values):
        print(f"{i:02d}: r={float(radius):.12f}")