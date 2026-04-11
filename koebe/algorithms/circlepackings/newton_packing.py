"""Newton-method Euclidean circle packing solver.

Computes a Euclidean circle packing by Newton iteration on the angle-sum
equations.  Variables are log-radii u_i = log(r_i) for interior vertices;
boundary vertices keep fixed radii.

Quadratic convergence replaces the linear convergence of the Thurston
iteration used in hypPacker.

Reference:
    G. Orick, "Computational Circle Packing: Geometry and Discrete
    Analytic Function Theory," PhD thesis, University of Tennessee, 2010.
"""

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from koebe.datastructures.dcel import DCEL
from koebe.geometries.euclidean2 import PointE2, CircleE2

TWO_PI = 2.0 * math.pi


# ---------------------------------------------------------------------------
# Flat mesh representation
# ---------------------------------------------------------------------------

@dataclass
class PackingMesh:
    """Flat-array representation of a triangulation for the Newton solver.

    Vertices are numbered so that interior vertices occupy indices
    0 .. n_interior-1 and boundary vertices follow.
    """
    n_verts: int
    n_interior: int
    n_faces: int
    faces: np.ndarray           # (n_faces, 3) vertex indices per triangle
    u: np.ndarray               # (n_verts,) log-radii
    interior: np.ndarray        # (n_verts,) bool mask, True for interior
    vert_to_idx: dict           # DCEL Vertex → flat index
    idx_to_vert: list           # flat index → DCEL Vertex


def _extract_mesh(dcel: DCEL) -> PackingMesh:
    """Convert a DCEL triangulated disk into flat NumPy arrays.

    Interior vertices are numbered first, then boundary vertices.
    """
    dcel.markIndices()
    boundary_set = set(dcel.outerFace.vertices())

    interior_verts = [v for v in dcel.verts if v not in boundary_set]
    boundary_verts = [v for v in dcel.verts if v in boundary_set]
    ordered = interior_verts + boundary_verts

    vert_to_idx = {v: i for i, v in enumerate(ordered)}
    n_interior = len(interior_verts)
    n_verts = len(ordered)

    # Build face array, skipping the outer face.
    face_list = []
    for f in dcel.faces:
        if f is dcel.outerFace:
            continue
        verts = f.vertices()
        if len(verts) != 3:
            raise ValueError(
                f"Non-triangle face with {len(verts)} vertices; "
                "input must be a triangulation."
            )
        face_list.append([vert_to_idx[v] for v in verts])

    faces = np.array(face_list, dtype=np.int32)
    u = np.zeros(n_verts)

    interior = np.zeros(n_verts, dtype=bool)
    interior[:n_interior] = True

    return PackingMesh(
        n_verts=n_verts,
        n_interior=n_interior,
        n_faces=len(face_list),
        faces=faces,
        u=u,
        interior=interior,
        vert_to_idx=vert_to_idx,
        idx_to_vert=ordered,
    )


# ---------------------------------------------------------------------------
# Per-triangle geometry
# ---------------------------------------------------------------------------

def _compute_face_data(mesh: PackingMesh):
    """Compute angles, areas, and edge lengths for every triangle.

    For a triangle with vertex radii (r_i, r_j, r_k), edge lengths are
    l_ij = r_i + r_j (mutual tangency), and the area follows from Heron's
    formula with semi-perimeter s = r_i + r_j + r_k:
        A = sqrt(s * r_i * r_j * r_k).

    Returns:
        angles:  (n_faces, 3) angle at each local vertex position.
        areas:   (n_faces,)   triangle areas.
        edges:   (n_faces, 3) edge length opposite each local vertex.
        cosines: (n_faces, 3) cosine of each angle.
    """
    r = np.exp(mesh.u)

    vi = mesh.faces[:, 0]
    vj = mesh.faces[:, 1]
    vk = mesh.faces[:, 2]

    ri, rj, rk = r[vi], r[vj], r[vk]

    # Edge opposite each local vertex.
    a = rj + rk   # opposite vertex 0
    b = rk + ri   # opposite vertex 1
    c = ri + rj   # opposite vertex 2

    s = ri + rj + rk
    areas = np.sqrt(np.maximum(s * ri * rj * rk, 0.0))

    cos_A = np.clip((b**2 + c**2 - a**2) / (2.0 * b * c), -1.0, 1.0)
    cos_B = np.clip((a**2 + c**2 - b**2) / (2.0 * a * c), -1.0, 1.0)
    cos_C = np.clip((a**2 + b**2 - c**2) / (2.0 * a * b), -1.0, 1.0)

    angles = np.column_stack([np.arccos(cos_A), np.arccos(cos_B), np.arccos(cos_C)])
    edges = np.column_stack([a, b, c])
    cosines = np.column_stack([cos_A, cos_B, cos_C])

    return angles, areas, edges, cosines


def _compute_angle_sums(mesh: PackingMesh, angles: np.ndarray) -> np.ndarray:
    """Sum angles at each vertex across all incident faces."""
    theta = np.zeros(mesh.n_verts)
    for col in range(3):
        np.add.at(theta, mesh.faces[:, col], angles[:, col])
    return theta


# ---------------------------------------------------------------------------
# Jacobian assembly
# ---------------------------------------------------------------------------

def _compute_jacobian(mesh: PackingMesh, angles: np.ndarray,
                      areas: np.ndarray, edges: np.ndarray,
                      cosines: np.ndarray):
    r"""Assemble the Jacobian :math:`\partial\theta/\partial u` for interior vertices.

    In a triangle (i, j, k) with area A and edge a = l_{jk} opposite
    vertex i, the partial derivatives of the angle at i are:

    .. math::
        \frac{\partial \alpha_i}{\partial u_j}
            = \frac{r_j \, a \, (1 - \cos\alpha_j)}{2A}

        \frac{\partial \alpha_i}{\partial u_k}
            = \frac{r_k \, a \, (1 - \cos\alpha_k)}{2A}

        \frac{\partial \alpha_i}{\partial u_i}
            = \frac{-r_i \, a \, (\cos\alpha_j + \cos\alpha_k)}{2A}

    These follow from the chain rule through the law of cosines composited
    with the tangent-circle edge-length relation l_{ij} = r_i + r_j and
    the substitution u_i = log r_i.  The Jacobian is symmetric (the
    angle-sum function is the gradient of a strictly concave functional;
    see Chow–Luo 2003).

    Returns:
        J: sparse CSC matrix of shape (n_interior, n_interior).
    """
    r = np.exp(mesh.u)
    n_int = mesh.n_interior

    rows, cols, vals = [], [], []

    for f_idx in range(mesh.n_faces):
        v = mesh.faces[f_idx]
        c = cosines[f_idx]
        A = areas[f_idx]
        e = edges[f_idx]

        if A < 1e-30:
            continue                       # skip degenerate triangles

        inv2A = 1.0 / (2.0 * A)

        for p in range(3):                 # local vertex position
            i = v[p]
            j = v[(p + 1) % 3]
            k = v[(p + 2) % 3]

            if i >= n_int:
                continue                   # angle-sum row for boundary: skip

            a_opp = e[p]                   # edge opposite vertex i

            # Diagonal contribution: d(alpha_i)/d(u_i)
            diag_val = -r[i] * a_opp * (c[(p + 1) % 3] + c[(p + 2) % 3]) * inv2A
            rows.append(i)
            cols.append(i)
            vals.append(diag_val)

            # Off-diagonal: d(alpha_i)/d(u_j)
            if j < n_int:
                val_j = r[j] * a_opp * (1.0 - c[(p + 1) % 3]) * inv2A
                rows.append(i)
                cols.append(j)
                vals.append(val_j)

            # Off-diagonal: d(alpha_i)/d(u_k)
            if k < n_int:
                val_k = r[k] * a_opp * (1.0 - c[(p + 2) % 3]) * inv2A
                rows.append(i)
                cols.append(k)
                vals.append(val_k)

    J = coo_matrix((vals, (rows, cols)), shape=(n_int, n_int)).tocsc()
    return J


# ---------------------------------------------------------------------------
# Newton solver
# ---------------------------------------------------------------------------

def _newton_solve(mesh: PackingMesh, tol: float = 1e-12,
                  max_iter: int = 50, quiet: bool = True) -> np.ndarray:
    r"""Newton iteration driving angle-sum residuals to zero.

    Solves :math:`\theta_i(u) = 2\pi` for every interior vertex *i*.
    Each step solves :math:`J \, \Delta u = -(\theta - 2\pi)` and applies
    a backtracking line search to ensure the residual decreases.

    Returns:
        The converged log-radii array ``mesh.u`` (modified in place).
    """
    for iteration in range(max_iter):
        angles, areas, edge_lens, cosines = _compute_face_data(mesh)
        theta = _compute_angle_sums(mesh, angles)

        residual = theta[:mesh.n_interior] - TWO_PI
        err = np.max(np.abs(residual))

        if not quiet:
            print(f"  Newton iter {iteration}: max|residual| = {err:.2e}")

        if err < tol:
            if not quiet:
                print(f"  Converged in {iteration} iteration(s).")
            return mesh.u

        J = _compute_jacobian(mesh, angles, areas, edge_lens, cosines)

        try:
            delta = spsolve(J, -residual)
        except Exception as exc:
            raise RuntimeError(
                f"Sparse solve failed at Newton iteration {iteration}"
            ) from exc

        # Backtracking line search.
        step = 1.0
        u_backup = mesh.u.copy()

        for _ in range(20):
            mesh.u[:mesh.n_interior] = u_backup[:mesh.n_interior] + step * delta
            angles_new, areas_new, _, _ = _compute_face_data(mesh)

            if np.any(areas_new <= 0):
                step *= 0.5
                continue

            theta_new = _compute_angle_sums(mesh, angles_new)
            new_err = np.max(np.abs(theta_new[:mesh.n_interior] - TWO_PI))

            if new_err < err:
                break
            step *= 0.5
        else:
            # Line search exhausted; accept the full Newton step.
            mesh.u[:mesh.n_interior] = u_backup[:mesh.n_interior] + delta

    if not quiet:
        print(f"  Warning: did not converge in {max_iter} iterations "
              f"(err = {err:.2e}).")

    return mesh.u


# ---------------------------------------------------------------------------
# Euclidean layout
# ---------------------------------------------------------------------------

def _place_third_vertex(centers: np.ndarray, r: np.ndarray,
                        va: int, vb: int, vc: int) -> None:
    """Place vertex *vc* given two already-placed tangent circles *va*, *vb*.

    The new vertex is placed to the LEFT of the directed edge va → vb,
    which corresponds to the interior side of a counter-clockwise face.
    """
    ax, ay = centers[va]
    bx, by = centers[vb]

    d_ab = r[va] + r[vb]
    d_ac = r[va] + r[vc]
    d_bc = r[vb] + r[vc]

    dx, dy = bx - ax, by - ay
    d = math.sqrt(dx * dx + dy * dy)
    if d < 1e-30:
        centers[vc] = [ax + d_ac, ay]
        return

    cos_a = np.clip((d_ac**2 + d_ab**2 - d_bc**2) / (2.0 * d_ac * d_ab),
                    -1.0, 1.0)
    sin_a = math.sqrt(1.0 - cos_a * cos_a)

    ux, uy = dx / d, dy / d     # unit vector along va → vb
    px, py = -uy, ux             # left-perpendicular

    centers[vc] = [
        ax + d_ac * (cos_a * ux + sin_a * px),
        ay + d_ac * (cos_a * uy + sin_a * py),
    ]


def _layout_euclidean(mesh: PackingMesh) -> np.ndarray:
    """Lay out tangent circles in the plane by BFS over the dual face graph.

    Starts from face 0: vertex 0 is placed at the origin, vertex 1 on the
    positive x-axis.  Each subsequent vertex is placed via
    :func:`_place_third_vertex`.

    Returns:
        centers: (n_verts, 2) array of circle centres.
    """
    r = np.exp(mesh.u)
    centers = np.full((mesh.n_verts, 2), np.nan)
    placed = np.zeros(mesh.n_verts, dtype=bool)
    visited = np.zeros(mesh.n_faces, dtype=bool)

    # Build face adjacency via an edge → face lookup.
    edge_to_face = {}
    for f_idx in range(mesh.n_faces):
        for p in range(3):
            va = mesh.faces[f_idx, p]
            vb = mesh.faces[f_idx, (p + 1) % 3]
            key = (min(va, vb), max(va, vb))
            edge_to_face.setdefault(key, []).append((f_idx, p))

    adj = np.full((mesh.n_faces, 3), -1, dtype=np.int32)
    for entries in edge_to_face.values():
        if len(entries) == 2:
            (f1, p1), (f2, p2) = entries
            adj[f1, p1] = f2
            adj[f2, p2] = f1

    # Seed with face 0.
    v = mesh.faces[0]
    centers[v[0]] = [0.0, 0.0]
    centers[v[1]] = [r[v[0]] + r[v[1]], 0.0]
    placed[v[0]] = placed[v[1]] = True
    _place_third_vertex(centers, r, v[0], v[1], v[2])
    placed[v[2]] = True
    visited[0] = True

    queue: deque = deque()
    for p in range(3):
        nf = adj[0, p]
        if nf >= 0:
            queue.append(nf)

    while queue:
        f_idx = queue.popleft()
        if visited[f_idx]:
            continue
        visited[f_idx] = True

        v = mesh.faces[f_idx]
        unplaced = [p for p in range(3) if not placed[v[p]]]

        if len(unplaced) == 1:
            p_new = unplaced[0]
            p_a = (p_new + 1) % 3
            p_b = (p_new + 2) % 3
            _place_third_vertex(centers, r, v[p_a], v[p_b], v[p_new])
            placed[v[p_new]] = True

        for p in range(3):
            nf = adj[f_idx, p]
            if nf >= 0 and not visited[nf]:
                queue.append(nf)

    return centers


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def newton_packing(disk_dcel: DCEL, tol: float = 1e-12, max_iter: int = 50,
                   boundary_radius: float = 1.0,
                   quiet: bool = True) -> DCEL:
    """Compute a Euclidean circle packing and project to S².

    This is a drop-in replacement for the sequence
    ``maximalPacking`` + ``canonical_spherical_projection`` used in
    ``hypPacker``.  The Newton solver achieves quadratic convergence
    (typically < 15 iterations) instead of the linear convergence of
    Thurston iteration.

    After solving for radii and laying out circles in the Euclidean plane,
    each :class:`CircleE2` is lifted to a :class:`DiskS2` via stereographic
    projection (``CircleE2.toDiskS2()``).  The result is **not**
    canonicalised; call :func:`canonical_spherical_layout` afterwards if
    a canonical position is needed.

    Args:
        disk_dcel:       Triangulated disk DCEL (boundary = ``outerFace``).
        tol:             Convergence tolerance on max angle-sum residual.
        max_iter:        Maximum Newton iterations.
        boundary_radius: Fixed Euclidean radius for all boundary vertices.
        quiet:           If True, suppress iteration output.

    Returns:
        A new DCEL with :class:`DiskS2` vertex data representing the circle
        packing on S² (via stereographic projection).
    """
    if disk_dcel.outerFace is None:
        raise ValueError("DCEL must have an outerFace (triangulated disk).")

    mesh = _extract_mesh(disk_dcel)

    # Fix boundary radii.
    mesh.u[mesh.n_interior:] = math.log(boundary_radius)

    _newton_solve(mesh, tol=tol, max_iter=max_iter, quiet=quiet)

    centers = _layout_euclidean(mesh)
    r = np.exp(mesh.u)

    # Build a DCEL → mesh-index map keyed by original vertex index.
    dcel_idx_to_mesh_idx = {}
    for orig_vert, mesh_idx in mesh.vert_to_idx.items():
        dcel_idx_to_mesh_idx[orig_vert.idx] = mesh_idx

    # Duplicate the input combinatorics with DiskS2 vertex data.
    result = disk_dcel.duplicate(vdata_transform=lambda d: None)
    result.markIndices()

    for v in result.verts:
        idx = dcel_idx_to_mesh_idx.get(v.idx)
        if idx is not None and not np.isnan(centers[idx, 0]):
            circle = CircleE2(
                PointE2(float(centers[idx, 0]), float(centers[idx, 1])),
                float(r[idx]),
            )
            v.data = circle.toDiskS2()
        else:
            # Fallback for any unplaced vertex (should not happen for
            # a valid triangulated disk).
            from koebe.geometries.spherical2 import DiskS2
            v.data = DiskS2(0, 0, 1, -1)

    return result
