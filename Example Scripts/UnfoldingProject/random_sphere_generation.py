import math
import matlab.engine

from koebe.datastructures.dcel import DCEL


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


def flower_orientation_signs(v_point, xyz_map, petals, closed, eps=1e-12):
    """
    For wedges (v, petals[i], petals[i+1]), compute sign of
    dot(cross(p_i - v, p_j - v), v). Positive means CCW wrt outward normal.
    """
    if len(petals) < 2:
        return []

    signs = []
    edge_count = len(petals) if closed else len(petals) - 1
    for i in range(edge_count):
        a_idx = petals[i]
        b_idx = petals[(i + 1) % len(petals)] if closed else petals[i + 1]
        pa = xyz_map[a_idx]
        pb = xyz_map[b_idx]
        va = vec_sub(pa, v_point)
        vb = vec_sub(pb, v_point)
        triple = dot(cross(va, vb), v_point)
        if triple > eps:
            signs.append(1)
        elif triple < -eps:
            signs.append(-1)
        else:
            signs.append(0)
    return signs


def normalize_flower_to_ccw(v, flower, xyz_map):
    """
    Return a CCW flower. For closed flowers, reorder petals by geometric angle
    in the tangent plane at vertex v. This fixes isolated local inversions.
    """
    if len(flower) < 2:
        return list(flower), False

    closed = flower[0] == flower[-1]
    petals = flower[:-1] if closed else flower

    # Open flowers are boundary cases; keep order but flip if mostly CW.
    if not closed:
        signs = flower_orientation_signs(xyz_map[v], xyz_map, petals, False)
        pos = sum(1 for s in signs if s > 0)
        neg = sum(1 for s in signs if s < 0)
        if neg > pos:
            return list(reversed(petals)), True
        return list(flower), False

    if len(petals) <= 2:
        fixed = petals + [petals[0]]
        return fixed, fixed != flower

    v_point = normalize(xyz_map[v])
    ref = (0.0, 0.0, 1.0) if abs(v_point[2]) < 0.95 else (1.0, 0.0, 0.0)
    e1 = normalize(cross(ref, v_point))
    e2 = cross(v_point, e1)

    angle_data = []
    for p in petals:
        p_vec = xyz_map[p]
        tangential = vec_sub(p_vec, (dot(p_vec, v_point) * v_point[0], dot(p_vec, v_point) * v_point[1], dot(p_vec, v_point) * v_point[2]))
        x_coord = dot(tangential, e1)
        y_coord = dot(tangential, e2)
        angle = math.atan2(y_coord, x_coord)
        angle_data.append((angle, p))

    angle_data.sort(key=lambda item: item[0])
    sorted_petals = [p for _, p in angle_data]

    # Preserve the same starting petal as input for stable indexing.
    anchor = petals[0]
    if anchor in sorted_petals:
        k = sorted_petals.index(anchor)
        sorted_petals = sorted_petals[k:] + sorted_petals[:k]

    fixed = sorted_petals + [sorted_petals[0]]
    return fixed, fixed != flower

def construct_dcel_from_gop(flowers, centers, radii):
    # Step 1: Construct vertices of DCEL with data
    dcel = DCEL()

    for i in range(len(flowers)):
        radius = radii[i]
        center = centers[i]





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
flower_lists = [to_int_list(flw) for flw in flower_values]

# Step 2: convert complex centers to xyz on the unit sphere.
xyz_by_vertex = {}
for i, center in enumerate(center_values):
    x, y, z = spherical_angles_to_xyz(center)
    xyz_by_vertex[i + 1] = (x, y, z)
    norm = math.sqrt(x * x + y * y + z * z)

