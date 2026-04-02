import math
import matlab.engine

from koebe.algorithms.circlepackings.layout import compute_tangencies, canonical_spherical_layout
from koebe.datastructures.dcel import DCEL, Vertex, Dart, Face, Edge
from koebe.geometries.euclidean2 import CircleE2, PointE2
from koebe.geometries.orientedProjective2 import DiskOP2
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
    Convert spherical angles encoded as theta + i*phi
    to unit sphere coordinates (x, y, z).
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
    flower_list_zero = [[int(petal) - 1 for petal in flower] for flower in flower_list]

    def triangles_from_flowers(flower_list):
        tried = set()
        for j, flower in enumerate(flower_list, start=0):
            for k in range(1, len(flower)):
                key = tuple(sorted([j, flower[k-1], flower[k]]))
                if key not in tried:
                    tried.add(key)
                    yield j, flower[k-1], flower[k]

    def successor_map_from_flowers(flowers_zero):
        succ = {}
        for v, flower in enumerate(flowers_zero):
            if len(flower) < 2:
                succ[v] = {}
                continue
            local = {}
            for k in range(1, len(flower)):
                local[flower[k - 1]] = flower[k]
            succ[v] = local
        return succ

    def orient_triangle_from_flowers(triangle, succ):
        a, b, c = triangle
        # If flower at a says b is followed by c, keep (a,b,c), else flip.
        if succ.get(a, {}).get(b) == c:
            return a, b, c
        if succ.get(a, {}).get(c) == b:
            return a, c, b
        # Fallback checks if a's flower is missing/incomplete.
        if succ.get(b, {}).get(c) == a:
            return a, b, c
        if succ.get(c, {}).get(a) == b:
            return a, b, c
        return a, b, c


    # Step 1: Build out vertices and data
    dcel = DCEL()
    for i in range(len(flower_list)):
        vertex = Vertex(dcel)
        z = complex(center_list[i])
        eucl_circle = CircleE2(PointE2(z.real, z.imag), float(radius_list[i]))
        vertex.data = DiskOP2.fromCircleE2(eucl_circle).toDiskS2()

    # Step2: Construct darts and DCEL structure from triangles

    vertex_indices_to_darts: dict[(int, int): Dart] = {}

    successor_map = successor_map_from_flowers(flower_list_zero)

    for triangle in triangles_from_flowers(flower_list_zero):
        triangle = orient_triangle_from_flowers(triangle, successor_map)

        face = Face(dcel)

        # Make darts
        darts = []
        for j in range(len(triangle)):
            dart = Dart(dcel, origin=dcel.verts[triangle[j-1]], face=face)
            face.aDart = dart
            darts.append(dart)

        # Fix darts
        for (dart_idx, dart) in enumerate(darts):
            origin_idx = dart_idx-1
            dest_idx = dart_idx
            # Connect to twin if it exists, and create corresponding edge
            twin_key = tuple(sorted([triangle[origin_idx], triangle[dest_idx]]))
            twin = vertex_indices_to_darts.get(twin_key, None)
            if twin is None:
                vertex_indices_to_darts[twin_key] = dart
                edge = Edge(dcel, dart)
                dart.edge = edge
            else:
                dart.makeTwin(twin)
                dart.edge = twin.edge

            dart.makePrev(darts[dart_idx - 1])
    return dcel

def build_dcel_with_gop(num_pts, canonicalize=True, n_iterations=50) -> DCEL:
    eng = matlab.engine.start_matlab()
    eng.addpath("C:/Users/lgabe/OneDrive/Desktop/cs497/GOPack/GOPack/code")

    gop = eng.randomSphere(num_pts)
    eng.riffle(gop, 10, nargout=3)

    eng.workspace["gop"] = gop
    centers = eng.eval("gop.centers", nargout=1)
    radii = eng.eval("gop.radii", nargout=1)
    flowers = eng.eval("gop.flowers", nargout=1)

    center_values = list(flatten_matlab_array(centers))
    radius_values = list(flatten_matlab_array(radii))
    flower_values = list(flatten_matlab_array(flowers))


    dcel = construct_dcel_from_packing_info(flower_values, center_values, radius_values)
    dcel.markIndices()

    mismatch_count = 0
    for i, flower in enumerate(flower_values, start=0):
        expected = set(int(petal) - 1 for petal in flower[:-1])
        actual = set(vert.idx for vert in dcel.verts[i].neighbors())
        ok = expected == actual
        if not ok:
            mismatch_count += 1


    if mismatch_count != 0:
        raise RuntimeError(f"Neighbor validation failed for {mismatch_count} vertices")

    compute_tangencies(dcel)
    if canonicalize:
        dcel = canonical_spherical_layout(dcel, n_iterations=n_iterations)
        dcel.markIndices()
        compute_tangencies(dcel)

    return dcel



if __name__ == "__main__":
    build_dcel_with_gop(10)