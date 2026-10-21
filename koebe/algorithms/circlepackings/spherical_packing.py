"""Low-error tangency circle packings of the sphere.

Two-stage algorithm
-------------------
**Stage 1 (approximate).**  Remove one face, compute a Euclidean packing of
the resulting disk with :func:`newton_packing`, stereographically project to
S^2, and Moebius-normalize with :func:`canonical_spherical_layout`.  This is
fast and robust but carries the round-off of the planar solve, the
combinatorial layout, and the projection (max relative tangency errors of
roughly 1e-7 at a few thousand circles).

**Stage 2 (refinement on the sphere).**  Gauss-Newton directly on the
sphere, using intrinsic cap coordinates: a unit center ``n_i`` and spherical
radius ``rho_i`` for every circle.  For every edge ``ij`` the residual is::

    F_ij = theta(n_i, n_j) - rho_i - rho_j,

where ``theta`` is the geodesic distance, computed with ``atan2`` so that it
is accurate to relative machine precision even for tiny circles.  A sphere
triangulation has ``3V - 6`` edges and the unknowns have ``3V`` degrees of
freedom, so the Jacobian has a 6-dimensional kernel: the Moebius group.
Each step is the minimum-norm solution of the linearized system (computed
from a sparse KKT system), which never moves along the Moebius directions,
so the Stage 1 normalization is preserved.  The problem has zero residual
at the solution, so Gauss-Newton converges quadratically, typically in 2-4
iterations from the Stage 1 output.

No stereographic projection, planar layout, or inversion is performed in
Stage 2, so the final accuracy is limited only by how accurately the
residuals can be evaluated: max relative tangency error near 1e-15.

Precision note
--------------
The returned :class:`DiskS2` objects store ``(n, -cos rho)``.  Any quantity
computed from these Lorentz coordinates (``inversiveDistTo``,
``radiusE3``, ...) suffers a cancellation error of about ``eps / rho^2``
for small circles, which is inherent in the representation and unrelated
to the solver.  For maximal accuracy, use the intrinsic arrays attached to
the returned DCEL (``sphere_centers``, ``sphere_radii``) together with
:func:`tangency_errors` and :func:`inversive_distances` in this module.
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
from scipy.sparse import coo_matrix, bmat, identity
from scipy.sparse.linalg import splu

from koebe.datastructures.dcel import DCEL
from koebe.geometries.spherical2 import DiskS2


# ---------------------------------------------------------------------------
# Results / diagnostics
# ---------------------------------------------------------------------------

@dataclass
class RefinementInfo:
    """Convergence report for :func:`refine_spherical_packing`."""
    initial_error: float            # max relative tangency error before refinement
    final_error: float              # max relative tangency error after refinement
    iterations: int
    history: List[float] = field(default_factory=list)  # max rel. error per iteration
    converged: bool = False
    orientation_preserved: bool = True


# ---------------------------------------------------------------------------
# Conversions between DiskS2 and intrinsic cap coordinates
# ---------------------------------------------------------------------------

def disks_to_caps(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Convert DiskS2 coordinates (rows ``(a, b, c, d)``) to caps.

    Uses the koebepy convention in which ``DiskS2(n, -cos rho)`` is the cap
    with unit center ``n`` and spherical radius ``rho``, and in which
    externally tangent disks have normalized Lorentz product ``-1``.

    Returns:
        centers: (V, 3) unit vectors.
        radii:   (V,) spherical radii in (0, pi).
    """
    X = np.asarray(X, dtype=float)
    s = np.linalg.norm(X[:, :3], axis=1)
    centers = X[:, :3] / s[:, None]
    cos_r = -X[:, 3] / s
    lor = np.sum(X[:, :3] ** 2, axis=1) - X[:, 3] ** 2
    if np.any(lor <= 0):
        raise ValueError("Some DiskS2 vectors are not spacelike (not real circles).")
    sin_r = np.sqrt(lor) / s
    radii = np.arctan2(sin_r, cos_r)
    return centers, radii


def caps_to_disks(centers: np.ndarray, radii: np.ndarray) -> List[DiskS2]:
    """Inverse of :func:`disks_to_caps` (same convention as
    ``DiskS2.withCenterAndRadiusS2``)."""
    cos_r = np.cos(radii)
    return [DiskS2(float(c[0]), float(c[1]), float(c[2]), float(-cr))
            for c, cr in zip(centers, cos_r)]


def _geodesic_dist(Ni: np.ndarray, Nj: np.ndarray) -> np.ndarray:
    """Angle between unit vectors, accurate for small and large angles."""
    cross = np.cross(Ni, Nj)
    return np.arctan2(np.linalg.norm(cross, axis=1), np.sum(Ni * Nj, axis=1))


def _relative_tangency_errors(centers, radii, edges) -> np.ndarray:
    i, j = edges[:, 0], edges[:, 1]
    theta = _geodesic_dist(centers[i], centers[j])
    return np.abs(theta - radii[i] - radii[j]) / np.minimum(radii[i], radii[j])


def inversive_distance_caps(ni, ri, nj, rj) -> np.ndarray:
    """Accurate inversive distance between caps (vectorized).

    Uses the koebepy sign convention: 1 for externally tangent caps, >1 for
    disjoint caps.  Computed as::

        I = 1 + 2 sin((theta + s)/2) sin((theta - s)/2) / (sin ri sin rj),

    with ``s = ri + rj``, which avoids the ``eps / r^2`` cancellation of the
    Lorentz-coordinate formula.
    """
    ni = np.atleast_2d(ni); nj = np.atleast_2d(nj)
    ri = np.atleast_1d(ri); rj = np.atleast_1d(rj)
    theta = _geodesic_dist(ni, nj)
    s = ri + rj
    return 1.0 + 2.0 * np.sin(0.5 * (theta + s)) * np.sin(0.5 * (theta - s)) / (np.sin(ri) * np.sin(rj))


# ---------------------------------------------------------------------------
# Combinatorics
# ---------------------------------------------------------------------------

def _combinatorics(dcel: DCEL) -> Tuple[np.ndarray, np.ndarray]:
    """Edge (E, 2) and face (F, 3) index arrays.  Calls ``markIndices``."""
    dcel.markIndices()
    edges = np.array([[u.idx, v.idx] for u, v in (e.endPoints() for e in dcel.edges)],
                     dtype=np.int64)
    faces = []
    for f in dcel.faces:
        vs = f.vertices()
        if len(vs) != 3:
            raise ValueError(f"Face with {len(vs)} vertices; input must be a triangulation.")
        faces.append([v.idx for v in vs])
    faces = np.array(faces, dtype=np.int64)
    V, E, F = len(dcel.verts), len(edges), len(faces)
    if V - E + F != 2 or E != 3 * V - 6:
        raise ValueError(f"Not a triangulated sphere (V={V}, E={E}, F={F}).")
    return edges, faces


def _face_orientations(centers, faces) -> np.ndarray:
    a, b, c = centers[faces[:, 0]], centers[faces[:, 1]], centers[faces[:, 2]]
    return np.sign(np.einsum('ij,ij->i', a, np.cross(b, c)))


# ---------------------------------------------------------------------------
# Moebius normalization (vectorized)
# ---------------------------------------------------------------------------

def _lorentz_normalize(X: np.ndarray) -> np.ndarray:
    lor = np.sum(X[:, :3] ** 2, axis=1) - X[:, 3] ** 2
    return X / np.sqrt(lor)[:, None]


def tangency_point_centroid(X: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """Euclidean centroid of the edge tangency points of DiskS2 vectors X.

    For normalized, externally tangent disks the Lorentz midpoint
    ``(x_i + x_j) / 2`` is lightlike and represents the tangency point
    ``-(a, b, c) / d`` (the ``DiskS2.tangentPointWith`` convention).
    """
    Xn = _lorentz_normalize(X)
    M = Xn[edges[:, 0]] + Xn[edges[:, 1]]
    P = -M[:, :3] / M[:, 3:4]
    P /= np.linalg.norm(P, axis=1)[:, None]
    return P.mean(axis=0)


def _boost(X: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Apply the Lorentz boost (a Moebius transformation of S^2) that maps
    the point of the open unit ball ``c`` to the origin, to rows of X."""
    c2 = float(c @ c)
    if c2 == 0.0:
        return X.copy()
    u = -c   # ball point c corresponds to the timelike vector (-c, 1)
    gamma = 1.0 / math.sqrt(1.0 - c2)
    x, t = X[:, :3], X[:, 3]
    ux = x @ u
    xn = x + (((gamma - 1.0) * ux / c2) - gamma * t)[:, None] * u[None, :]
    tn = gamma * (t - ux)
    return np.column_stack([xn, tn])


def canonical_center(X: np.ndarray, edges: np.ndarray, max_iter: int = 50,
                     tol: float = 1e-13) -> np.ndarray:
    """Moebius-normalize DiskS2 vectors so the tangency points have center of
    mass at the origin.

    Vectorized equivalent of :func:`canonical_spherical_layout` (the results
    agree up to an isometry of S^2).  Each iteration boosts the current
    centroid to the origin; this converges quickly in practice.
    """
    X = _lorentz_normalize(np.asarray(X, dtype=float))
    for _ in range(max_iter):
        c = tangency_point_centroid(X, edges)
        if np.linalg.norm(c) < tol:
            break
        X = _lorentz_normalize(_boost(X, c))
    return X


# ---------------------------------------------------------------------------
# Stage 2: Gauss-Newton refinement on the sphere
# ---------------------------------------------------------------------------

def _tangent_frames(N: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Orthonormal tangent frame (e1, e2) at each unit vector in N."""
    helper = np.zeros_like(N)
    use_x = np.abs(N[:, 0]) < 0.9
    helper[use_x, 0] = 1.0
    helper[~use_x, 1] = 1.0
    e1 = helper - np.sum(helper * N, axis=1)[:, None] * N
    e1 /= np.linalg.norm(e1, axis=1)[:, None]
    e2 = np.cross(N, e1)
    return e1, e2


def _residual(N, rho, edges):
    i, j = edges[:, 0], edges[:, 1]
    return _geodesic_dist(N[i], N[j]) - rho[i] - rho[j]


def _jacobian(N, rho, edges, e1, e2):
    """Sparse Jacobian of the edge residuals w.r.t. the local unknowns.

    Unknowns for vertex v are ``(a_v, b_v, drho_v)`` at columns
    ``3v, 3v+1, 3v+2``; the center moves to ``normalize(n + a e1 + b e2)``.
    """
    E = len(edges)
    i, j = edges[:, 0], edges[:, 1]
    Ni, Nj = N[i], N[j]
    m = np.cross(Ni, Nj)
    s = np.linalg.norm(m, axis=1)[:, None]
    t_ij = np.cross(m, Ni) / s      # unit tangent at n_i pointing to n_j
    t_ji = np.cross(Nj, m) / s      # unit tangent at n_j pointing to n_i
    rows = np.repeat(np.arange(E), 6)
    cols = np.stack([3 * i, 3 * i + 1, 3 * i + 2, 3 * j, 3 * j + 1, 3 * j + 2], axis=1).ravel()
    vals = np.stack([
        -np.sum(t_ij * e1[i], axis=1), -np.sum(t_ij * e2[i], axis=1), -np.ones(E),
        -np.sum(t_ji * e1[j], axis=1), -np.sum(t_ji * e2[j], axis=1), -np.ones(E),
    ], axis=1).ravel()
    return coo_matrix((vals, (rows, cols)), shape=(E, 3 * len(N))).tocsr()


def _apply_step(N, rho, delta, e1, e2):
    d = delta.reshape(-1, 3)
    Nn = N + d[:, 0:1] * e1 + d[:, 1:2] * e2
    Nn /= np.linalg.norm(Nn, axis=1)[:, None]
    return Nn, rho + d[:, 2]


def refine_caps(centers: np.ndarray, radii: np.ndarray, edges: np.ndarray,
                tol: float = 1e-14, max_iter: int = 20,
                quiet: bool = True) -> Tuple[np.ndarray, np.ndarray, RefinementInfo]:
    """Gauss-Newton refinement of an approximate sphere packing (array API).

    Args:
        centers: (V, 3) approximate unit centers.
        radii:   (V,) approximate spherical radii.
        edges:   (3V-6, 2) tangency edges of a sphere triangulation.
        tol:     Stop once the max relative tangency error is below ``tol``,
                 or once every absolute residual is within a few machine
                 epsilons (the floor for unit vectors in double precision,
                 which bounds the relative error by about ``eps / r_min``).
        max_iter: Maximum number of Gauss-Newton steps.
        quiet:   Suppress per-iteration output.

    Returns:
        (centers, radii, info)
    """
    N = np.array(centers, dtype=float)
    N /= np.linalg.norm(N, axis=1)[:, None]
    rho = np.array(radii, dtype=float)
    V = len(N)

    def max_rel(Nc, rc):
        return float(np.max(_relative_tangency_errors(Nc, rc, edges)))

    # Unit vectors stored in double precision carry an absolute error of
    # about eps, so no residual |F_ij| can be reliably pushed below a small
    # multiple of eps.  Reaching that floor counts as convergence.
    abs_floor = 8.0 * np.finfo(float).eps

    def at_floor(Nc, rc):
        return float(np.max(np.abs(_residual(Nc, rc, edges)))) <= abs_floor

    err = max_rel(N, rho)
    info = RefinementInfo(initial_error=err, final_error=err, iterations=0, history=[err])
    if not quiet:
        print(f"  refine iter 0: max rel tangency error = {err:.3e}")

    for it in range(1, max_iter + 1):
        if err < tol or at_floor(N, rho):
            info.converged = True
            break

        # Scaled system: rows by 1/min(rho_i, rho_j) (relative error),
        # columns by rho_v (natural length scale of each circle).
        i, j = edges[:, 0], edges[:, 1]
        w = 1.0 / np.minimum(rho[i], rho[j])
        D = np.repeat(rho, 3)
        e1, e2 = _tangent_frames(N)
        J = _jacobian(N, rho, edges, e1, e2)
        Js = (J.multiply(w[:, None])).multiply(D[None, :]).tocsr()
        Fs = w * _residual(N, rho, edges)

        # Minimum-norm step from the KKT system [[I, Js^T], [Js, 0]].
        K = bmat([[identity(3 * V, format='csc'), Js.T], [Js, None]], format='csc')
        rhs = np.concatenate([np.zeros(3 * V), -Fs])
        try:
            sol = splu(K).solve(rhs)
        except RuntimeError as exc:
            raise RuntimeError(
                f"Singular linearized system at refinement iteration {it}; the input "
                "is probably not close enough to a packing.") from exc
        delta = D * sol[:3 * V]

        # Backtracking on the max relative error.
        t = 1.0
        accepted = False
        for _ in range(30):
            Nn, rn = _apply_step(N, rho, t * delta, e1, e2)
            if np.all(rn > 0) and np.all(rn < math.pi):
                new_err = max_rel(Nn, rn)
                if new_err < err:
                    accepted = True
                    break
            t *= 0.5
        if not accepted:
            # No step improves the residual: we are at (or near) the
            # floating-point floor.
            info.converged = err < tol or float(np.max(np.abs(_residual(N, rho, edges)))) <= 8 * abs_floor
            break

        N, rho, err = Nn, rn, new_err
        info.iterations = it
        info.history.append(err)
        if not quiet:
            print(f"  refine iter {it}: max rel tangency error = {err:.3e} (step {t:g})")
    else:
        info.converged = err < tol or at_floor(N, rho)

    info.converged = info.converged or err < tol or at_floor(N, rho)
    info.final_error = err
    return N, rho, info


def refine_spherical_packing(packingS2: DCEL, tol: float = 1e-14,
                             max_iter: int = 20, quiet: bool = True,
                             return_info: bool = False,
                             canonical: bool = False,
                             canonical_iterations: int = 50):
    """Refine an approximate tangency packing of the sphere (Stage 2).

    Args:
        packingS2: DCEL of a triangulated sphere whose vertex data are
            :class:`DiskS2` objects that are approximately tangent along
            every edge (e.g. the output of :func:`newton_packing`).
        tol: Target max relative tangency error
            ``|d(c_i, c_j) - (r_i + r_j)| / min(r_i, r_j)``.
        max_iter: Maximum Gauss-Newton iterations.
        quiet: Suppress per-iteration output.
        return_info: If True, also return a :class:`RefinementInfo`.
        canonical: If True, first Moebius-normalize with
            :func:`canonical_center` (tangency points centered at the
            origin).  The refinement preserves this normalization up to the
            size of the Stage 1 error.
        canonical_iterations: Maximum centering iterations.

    Returns:
        A new DCEL with refined :class:`DiskS2` vertex data.  The intrinsic
        caps are attached as ``result.sphere_centers`` ((V, 3) array) and
        ``result.sphere_radii`` ((V,) array), indexed by ``v.idx``.
    """
    result = packingS2.duplicate()
    edges, faces = _combinatorics(result)
    X = np.array([[v.data.a, v.data.b, v.data.c, v.data.d] for v in result.verts], dtype=float)
    lor = np.sum(X[:, :3] ** 2, axis=1) - X[:, 3] ** 2
    if np.any(lor <= 0):
        raise ValueError("Some DiskS2 vectors are not spacelike (not real circles).")

    # Every edge should be (approximately) an external tangency.
    i, j = edges[:, 0], edges[:, 1]
    Xn = X / np.sqrt(lor)[:, None]
    ip = np.sum(Xn[i, :3] * Xn[j, :3], axis=1) - Xn[i, 3] * Xn[j, 3]
    if np.any(ip > 0):
        raise ValueError("Some edges are not external tangencies (inconsistent disk "
                         "orientations); the input is not an approximate packing.")

    if canonical:
        X = canonical_center(Xn, edges, max_iter=canonical_iterations)
    centers, radii = disks_to_caps(X)

    orient0 = _face_orientations(centers, faces)
    centers, radii, info = refine_caps(centers, radii, edges, tol=tol,
                                       max_iter=max_iter, quiet=quiet)
    orient1 = _face_orientations(centers, faces)
    info.orientation_preserved = bool(np.all(orient0 == orient1))
    if not info.orientation_preserved and not quiet:
        print("  warning: some face orientations changed during refinement.")

    for v, disk in zip(result.verts, caps_to_disks(centers, radii)):
        v.data = disk
    result.sphere_centers = centers
    result.sphere_radii = radii
    return (result, info) if return_info else result


# ---------------------------------------------------------------------------
# Two-stage public interface
# ---------------------------------------------------------------------------

def spherical_packing(triangulation: DCEL, tol: float = 1e-14, max_iter: int = 20,
                      canonical: bool = True, canonical_iterations: int = 50,
                      outer_face_index: Optional[int] = None,
                      quiet: bool = True, return_info: bool = False):
    """Compute a low-error tangency circle packing of the sphere.

    Args:
        triangulation: DCEL of a triangulated sphere (e.g. from
            ``randomConvexHullE3``).  It is not modified, apart from
            ``markIndices`` being called on it.
        tol: Target max relative tangency error for Stage 2.
        max_iter: Maximum Gauss-Newton iterations in Stage 2.
        canonical: Moebius-normalize the Stage 1 packing so that the
            tangency points have center of mass at the origin (vectorized
            :func:`canonical_center`, equivalent to
            :func:`canonical_spherical_layout` up to an isometry).  The
            normalization is done before refinement and is preserved by it
            up to the size of the Stage 1 error.
        canonical_iterations: Maximum centering iterations.
        outer_face_index: Face removed in Stage 1 (defaults to the DCEL's
            ``outerFace``, or face 0 if none is set).  Only affects the
            result up to a Moebius transformation.
        quiet: Suppress progress output.
        return_info: If True, also return the Stage 2 :class:`RefinementInfo`.

    Returns:
        A DCEL with :class:`DiskS2` vertex data; see
        :func:`refine_spherical_packing` for the attached intrinsic arrays.
    """
    from koebe.algorithms.circlepackings.newton_packing import newton_packing

    work = triangulation.duplicate()
    if outer_face_index is not None:
        work.outerFace = work.faces[outer_face_index]
    elif work.outerFace is None:
        work.outerFace = work.faces[0]

    if not quiet:
        print("Stage 1: planar Newton packing + stereographic projection")
    packing = newton_packing(work, quiet=quiet)

    if not quiet:
        print("Stage 2: Gauss-Newton refinement on the sphere")
    return refine_spherical_packing(packing, tol=tol, max_iter=max_iter,
                                    quiet=quiet, return_info=return_info,
                                    canonical=canonical,
                                    canonical_iterations=canonical_iterations)


# ---------------------------------------------------------------------------
# Diagnostics on returned packings
# ---------------------------------------------------------------------------

def _caps_of(packing: DCEL) -> Tuple[np.ndarray, np.ndarray]:
    if hasattr(packing, 'sphere_centers') and hasattr(packing, 'sphere_radii'):
        return packing.sphere_centers, packing.sphere_radii
    X = np.array([[v.data.a, v.data.b, v.data.c, v.data.d] for v in packing.verts], dtype=float)
    return disks_to_caps(X)


def tangency_errors(packing: DCEL) -> np.ndarray:
    """Relative tangency error of every edge, indexed like ``packing.edges``.

    Uses the attached intrinsic caps when present, otherwise converts the
    DiskS2 vertex data (which limits accuracy to about ``eps / r^2``).
    """
    packing.markIndices()
    edges = np.array([[u.idx, v.idx] for u, v in (e.endPoints() for e in packing.edges)],
                     dtype=np.int64)
    centers, radii = _caps_of(packing)
    return _relative_tangency_errors(centers, radii, edges)


def inversive_distances(packing: DCEL, pairs) -> np.ndarray:
    """Accurate inversive distances for vertex-index pairs ``[(i, j), ...]``."""
    pairs = np.asarray(pairs, dtype=np.int64).reshape(-1, 2)
    centers, radii = _caps_of(packing)
    i, j = pairs[:, 0], pairs[:, 1]
    return inversive_distance_caps(centers[i], radii[i], centers[j], radii[j])
