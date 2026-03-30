import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


# Cube vertices in folded configuration
V = {
    0: np.array([-0.5, -0.5, -0.5], dtype=float),
    1: np.array([0.5, -0.5, -0.5], dtype=float),
    2: np.array([0.5, 0.5, -0.5], dtype=float),
    3: np.array([-0.5, 0.5, -0.5], dtype=float),
    4: np.array([-0.5, -0.5, 0.5], dtype=float),
    5: np.array([0.5, -0.5, 0.5], dtype=float),
    6: np.array([0.5, 0.5, 0.5], dtype=float),
    7: np.array([-0.5, 0.5, 0.5], dtype=float),
}

# Face definitions (vertex ids in order)
# Cross unfolding tree:
# center = Front, neighbors = Top/Bottom/Left/Right, and Back attached to Top.
FACES = {
    "Front": [3, 2, 6, 7],
    "Top": [4, 5, 6, 7],
    "Bottom": [0, 1, 2, 3],
    "Left": [0, 3, 7, 4],
    "Right": [1, 2, 6, 5],
    "Back": [0, 1, 5, 4],
}

# Unfolding tree edges: (parent, child, hinge edge vertex ids, target angle in radians)
# Angle sign chosen so all faces flatten into the Front face plane, creating a cross net.
TREE = [
    ("Front", "Top", (7, 6), -np.pi / 2),
    ("Front", "Bottom", (3, 2), np.pi / 2),
    ("Front", "Left", (3, 7), -np.pi / 2),
    ("Front", "Right", (2, 6), np.pi / 2),
    ("Top", "Back", (4, 5), -np.pi / 2),
]

PARENT = {child: parent for parent, child, _, _ in TREE}
HINGE = {child: edge for _, child, edge, _ in TREE}
TARGET_ANGLE = {child: angle for _, child, _, angle in TREE}

# Cube edges (for coloring cut vs non-cut)
ALL_EDGES = {
    tuple(sorted(e))
    for e in [
        (0, 1), (1, 2), (2, 3), (0, 3),
        (4, 5), (5, 6), (6, 7), (4, 7),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
}

UNCUT_EDGES = {tuple(sorted(edge)) for _, _, edge, _ in TREE}
CUT_EDGES = ALL_EDGES - UNCUT_EDGES

FACE_COLORS = {
    "Front": "#f7f7f7",
    "Top": "#d9ead3",
    "Bottom": "#cfe2f3",
    "Left": "#fce5cd",
    "Right": "#ead1dc",
    "Back": "#fff2cc",
}


def rotation_matrix(axis, theta):
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    x, y, z = axis
    c = np.cos(theta)
    s = np.sin(theta)
    C = 1.0 - c
    return np.array(
        [
            [c + x * x * C, x * y * C - z * s, x * z * C + y * s],
            [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
            [z * x * C - y * s, z * y * C + x * s, c + z * z * C],
        ],
        dtype=float,
    )


def rotate_points(points, p0, p1, theta):
    axis = p1 - p0
    R = rotation_matrix(axis, theta)
    shifted = points - p0
    return shifted @ R.T + p0


def path_to_root(face_name):
    path = []
    cur = face_name
    while cur in PARENT:
        path.append(cur)
        cur = PARENT[cur]
    path.reverse()
    return path


def transform_face(face_name, t):
    # Start from folded face coordinates
    vids = FACES[face_name]
    pts = np.array([V[i] for i in vids], dtype=float)

    # Apply ancestor hinge rotations in root->leaf order
    applied = []
    for node in path_to_root(face_name):
        e0, e1 = HINGE[node]
        theta = TARGET_ANGLE[node] * t

        # Hinge axis points must be transformed by already applied rotations
        a = V[e0].copy()
        b = V[e1].copy()
        for prev_node in applied:
            pe0, pe1 = HINGE[prev_node]
            ptheta = TARGET_ANGLE[prev_node] * t
            ap = V[pe0]
            bp = V[pe1]
            a = rotate_points(a[None, :], ap, bp, ptheta)[0]
            b = rotate_points(b[None, :], ap, bp, ptheta)[0]

        pts = rotate_points(pts, a, b, theta)
        applied.append(node)

    return pts, vids


def get_face_geometry(t):
    return {name: transform_face(name, t) for name in FACES}


def draw_frame(ax, t):
    ax.cla()
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(-2.0, 2.0)
    ax.set_zlim(-2.0, 2.0)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=24, azim=-58)
    ax.set_title("Cube Cross Unfolding (Cut Tree Edges in Red)")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    geom = get_face_geometry(t)

    # Draw faces
    for name, (pts, _) in geom.items():
        poly = Poly3DCollection([pts], alpha=0.42, facecolor=FACE_COLORS[name], edgecolor="none")
        ax.add_collection3d(poly)

    # Draw edges with cut tree coloring
    for _, (pts, vids) in geom.items():
        for i in range(4):
            j = (i + 1) % 4
            edge = tuple(sorted((vids[i], vids[j])))
            color = "red" if edge in CUT_EDGES else "black"
            lw = 2.6 if edge in CUT_EDGES else 1.8
            seg = np.vstack([pts[i], pts[j]])
            ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], color=color, linewidth=lw)

    # Legend-like annotation
    ax.text2D(0.02, 0.95, "Red: cut edges", transform=ax.transAxes, color="red")
    ax.text2D(0.02, 0.91, "Black: uncut (hinge) edges", transform=ax.transAxes, color="black")


def main():
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection="3d")

    n_frames = 180

    def smoothstep(x):
        return x * x * (3.0 - 2.0 * x)

    def update(frame):
        # Forward unfold and then fold back for continuous visualization
        phase = frame / (n_frames - 1)
        if phase <= 0.5:
            t = smoothstep(phase * 2.0)
        else:
            t = smoothstep((1.0 - phase) * 2.0)
        draw_frame(ax, t)
        return []

    FuncAnimation(fig, update, frames=n_frames, interval=40, blit=False, repeat=True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
