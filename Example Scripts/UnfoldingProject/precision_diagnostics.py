"""Where does packing_residual come from? A read-only precision diagnostic.

Rebuilds one sweep trial's packing from its seed, running the same steps as
generate_coin_polygon_orick one at a time, and checks the packing's accuracy
between every step. Nothing in the existing pipeline is modified: library
functions are called as-is, and the stable half-angle formula lives only in
this file as a helper.

Every packing edge is a pair of circles that must be exactly tangent, i.e.
inversive distance exactly 1. Inversive distance is preserved by every
geometric step after the layout (stereographic projection, Möbius moves), so
in exact arithmetic it would stay 1 throughout; any growth is numerical.
At each step it is reported two ways:
  float  -- what the pipeline itself computes (float64)
  exact  -- the same quantity evaluated in 60-digit Decimal from the numbers
            that step actually stored. If exact is large too, the stored
            numbers themselves already lost the information.

Steps (as in generate_coin_polygon_orick / newton_packing):
  1. randomConvexHullE3                     random polyhedron (combinatorics)
  2. newton_packing -> _newton_solve        radii, as log-radii
  3. newton_packing -> _layout_euclidean    circle centers in the plane
  4a. DiskOP2.fromCircleE2                  plane circle -> (a,b,c,d) coefficients
  4b. DiskOP2.toDiskS2                      -> sphere cap coefficients
  5. canonical_spherical_layout             Möbius normalization (checked at
                                            several iteration counts)
  6. compute_tangencies                     tangency points on the sphere

Usage:
  python precision_diagnostics.py --n 2000 --seed 8247816612784319471
"""

import argparse
import contextlib
import io
import math
import sys
import time
from decimal import Decimal, getcontext
from pathlib import Path
from random import seed as rseed

import numpy as np

koebepy_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(koebepy_root))

from koebe.algorithms.incrementalConvexHull import randomConvexHullE3
from koebe.algorithms.circlepackings.layout import canonical_spherical_layout, compute_tangencies
from koebe.algorithms.circlepackings import newton_packing as npk
from koebe.geometries.euclidean2 import PointE2, CircleE2
from koebe.geometries.orientedProjective2 import DiskOP2

getcontext().prec = 60
D_PI = Decimal("3.14159265358979323846264338327950288419716939937510582097494")


# ---------------------------------------------------------------------------
# Angle formulas
# ---------------------------------------------------------------------------

def stable_tangent_triangle_angles(ri, rj, rk):
    """Angles of the triangle of centers of three mutually tangent circles.

    Half-angle formula: tan(alpha_i / 2) = sqrt(rj*rk / (ri*(ri+rj+rk))).
    Uses only additions of positives, products, quotients, sqrt and atan, so
    no step subtracts nearly equal numbers. Works elementwise on arrays.
    """
    s = ri + rj + rk
    ai = 2.0 * np.arctan(np.sqrt(rj * rk / (ri * s)))
    aj = 2.0 * np.arctan(np.sqrt(ri * rk / (rj * s)))
    ak = 2.0 * np.arctan(np.sqrt(ri * rj / (rk * s)))
    return np.column_stack([ai, aj, ak])


def _datan(x):
    """60-digit arctan for x >= 0 (argument halving, then Taylor series)."""
    halvings = 0
    while x > Decimal("0.01"):
        x = x / (1 + (1 + x * x).sqrt())
        halvings += 1
    total, term, k, x2 = Decimal(0), x, 0, x * x
    while abs(term) > Decimal(10) ** -58:
        total += term / (2 * k + 1) if k % 2 == 0 else -term / (2 * k + 1)
        term *= x2
        k += 1
    return total * (2 ** halvings)


def reference_angle(ri, rj, rk):
    """60-digit angle at i, from the float64 radii taken as exact inputs."""
    ri, rj, rk = Decimal(ri), Decimal(rj), Decimal(rk)
    return 2 * _datan((rj * rk / (ri * (ri + rj + rk))).sqrt())


# ---------------------------------------------------------------------------
# Exact inversive distances, one per representation
# ---------------------------------------------------------------------------

def _D(x):
    return Decimal(float(x))


def _inv_dist_center_radius(x1, y1, r1, x2, y2, r2):
    """(d^2 - r1^2 - r2^2) / (2 r1 r2) for planar circles, Decimal inputs."""
    d2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
    return (d2 - r1 * r1 - r2 * r2) / (2 * r1 * r2)


def _op2_center_radius(disk):
    """Recover (x, y, r) exactly from DiskOP2 coefficients a|z|^2 + bx + cy + d."""
    a, b, c, d = (_D(t) for t in (disk.a, disk.b, disk.c, disk.d))
    x, y = -b / (2 * a), -c / (2 * a)
    r2 = x * x + y * y - d / a
    return x, y, r2.sqrt() if r2 > 0 else Decimal(0)


def _s2_inv_dist(p, q):
    """Inversive distance of two DiskS2s in 60 digits, from their stored floats."""
    a1, b1, c1, d1 = (_D(t) for t in (p.a, p.b, p.c, p.d))
    a2, b2, c2, d2 = (_D(t) for t in (q.a, q.b, q.c, q.d))
    ip12 = a1 * a2 + b1 * b2 + c1 * c2 - d1 * d2
    ip11 = a1 * a1 + b1 * b1 + c1 * c1 - d1 * d1
    ip22 = a2 * a2 + b2 * b2 + c2 * c2 - d2 * d2
    return -ip12 / (ip11.sqrt() * ip22.sqrt())


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _summ(label, arr):
    arr = np.asarray(arr, dtype=float)
    print(f"    {label:<40} max={arr.max():.2e}  median={np.median(arr):.2e}  "
          f"p99={np.percentile(arr, 99):.2e}")


def _report_edges(label, edges, float_errs=None, exact_errs=None):
    print(f"\n{label}")
    if float_errs is not None:
        _summ("float (as the pipeline computes it)", float_errs)
    if exact_errs is not None:
        _summ("exact (60 digits, from stored numbers)", exact_errs)
        w = int(np.argmax(exact_errs))
        print(f"    worst edge (exact): verts {edges[w]}")


def _sphere_edge_errors(packing, edges):
    verts = packing.verts
    fl, ex = [], []
    for i, j in edges:
        p, q = verts[i].data, verts[j].data
        fl.append(abs(p.inversiveDistTo(q) - 1.0))
        ex.append(float(abs(_s2_inv_dist(p, q) - 1)))
    return fl, ex


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=8247816612784319471)
    ap.add_argument("--tol", type=float, default=1e-13)
    ap.add_argument("--canonical", type=int, default=1000,
                    help="canonical_spherical_layout iterations (sweep uses 1000)")
    args = ap.parse_args()

    # ---- 1. random convex polyhedron -------------------------------------
    t0 = time.time()
    rseed(args.seed)
    hull = randomConvexHullE3(args.n)
    hull.outerFace = hull.faces[0]
    hull.markIndices()
    V, E, F = len(hull.verts), len(hull.edges), len(hull.faces)
    all_tri = all(len(f.vertices()) == 3 for f in hull.faces)
    print(f"[1] randomConvexHullE3 ({time.time() - t0:.1f}s): V={V} E={E} F={F}  "
          f"V-E+F={V - E + F} (should be 2)  all triangles={all_tri}")
    edges = [tuple(sorted((u.idx, v.idx))) for u, v in (e.endPoints() for e in hull.edges)]

    # ---- 2. Newton solve (same calls newton_packing makes) ---------------
    mesh = npk._extract_mesh(hull)
    mesh.u[mesh.n_interior:] = math.log(1.0)
    npk._newton_solve(mesh, tol=args.tol, max_iter=50, quiet=True)
    r = np.exp(mesh.u)
    m = {v.idx: k for v, k in mesh.vert_to_idx.items()}   # hull idx -> mesh idx

    old_angles, _, _, _ = npk._compute_face_data(mesh)
    f = mesh.faces
    new_angles = stable_tangent_triangle_angles(r[f[:, 0]], r[f[:, 1]], r[f[:, 2]])
    ref = np.empty(f.shape, dtype=object)
    for fi in range(len(f)):
        a, b, c = (float(r[x]) for x in f[fi])
        ref[fi] = [reference_angle(a, b, c), reference_angle(b, c, a), reference_angle(c, a, b)]

    def rel_err(approx):
        return [float(abs(_D(approx[i, p]) - ref[i, p]) / ref[i, p])
                for i in range(len(f)) for p in range(3)]

    theta_ref = [Decimal(0)] * mesh.n_verts
    for fi in range(len(f)):
        for p in range(3):
            theta_ref[f[fi, p]] += ref[fi, p]
    solver_res = np.abs(npk._compute_angle_sums(mesh, old_angles)[:mesh.n_interior] - 2 * math.pi)
    true_res = [float(abs(theta_ref[v] - 2 * D_PI)) for v in range(mesh.n_interior)]

    print(f"\n[2] _newton_solve: radii {r.min():.2e} .. {r.max():.2e}, "
          f"smallest angle {new_angles.min():.2e} rad")
    print("  angle-sum residual |theta - 2pi| per interior vertex")
    _summ("as the solver sees it", solver_res)
    _summ("true (60 digits)", true_res)
    print("  per-angle relative error")
    _summ("current formula (law of cosines)", rel_err(old_angles))
    _summ("half-angle helper", rel_err(new_angles))

    # ---- 3. planar layout -------------------------------------------------
    centers = npk._layout_euclidean(mesh)
    rel_center, inv3 = [], []
    for i, j in edges:
        a, b = m[i], m[j]
        x1, y1, x2, y2 = (_D(t) for t in (centers[a, 0], centers[a, 1], centers[b, 0], centers[b, 1]))
        r1, r2 = _D(r[a]), _D(r[b])
        d = ((x1 - x2) ** 2 + (y1 - y2) ** 2).sqrt()
        rel_center.append(float(abs(d - (r1 + r2)) / (r1 + r2)))
        inv3.append(float(abs(_inv_dist_center_radius(x1, y1, r1, x2, y2, r2) - 1)))
    _report_edges("[3] _layout_euclidean: |inversive distance - 1| per edge", edges, exact_errs=inv3)
    _summ("(center distance vs r1+r2, relative)", rel_center)

    # ---- 4a. plane circle -> DiskOP2 coefficients --------------------------
    op2 = {}
    for v in hull.verts:
        k = m[v.idx]
        op2[v.idx] = DiskOP2.fromCircleE2(
            CircleE2(PointE2(float(centers[k, 0]), float(centers[k, 1])), float(r[k])))
    inv4a, rad4a = [], []
    for i, j in edges:
        x1, y1, r1 = _op2_center_radius(op2[i])
        x2, y2, r2 = _op2_center_radius(op2[j])
        inv4a.append(float(abs(_inv_dist_center_radius(x1, y1, r1, x2, y2, r2) - 1)))
    for v in hull.verts:
        _, _, rr = _op2_center_radius(op2[v.idx])
        rad4a.append(float(abs(rr - _D(r[m[v.idx]])) / _D(r[m[v.idx]])))
    _report_edges("[4a] DiskOP2.fromCircleE2 (d = x^2 + y^2 - r^2): |inversive distance - 1|",
                  edges, exact_errs=inv4a)
    _summ("(radius recoverable from coeffs, rel. err)", rad4a)

    # ---- 4b. DiskOP2 -> DiskS2 (completes the lift) -------------------------
    packing = hull.duplicate(vdata_transform=lambda _: None)
    packing.markIndices()
    for v in packing.verts:
        v.data = op2[v.idx].toDiskS2()
    fl, ex = _sphere_edge_errors(packing, edges)
    _report_edges("[4b] DiskOP2.toDiskS2: |inversive distance - 1| on the sphere", edges, fl, ex)

    # Sanity: this hand-run lift must match the real newton_packing exactly.
    rseed(args.seed)
    hull2 = randomConvexHullE3(args.n)
    hull2.outerFace = hull2.faces[0]
    real = npk.newton_packing(hull2, tol=args.tol, quiet=True)
    same = all(tuple(a.data) == tuple(b.data) for a, b in zip(real.verts, packing.verts))
    print(f"    (identical to real newton_packing output: {same})")

    # ---- 5. canonical layout, checked as it runs ---------------------------
    # canonical_spherical_layout keeps no state between iterations that
    # affects the result, so running it in chunks equals one long run.
    checkpoints = sorted({c for c in (1, 10, 100, args.canonical) if c <= args.canonical})
    done = 0
    t0 = time.time()
    for cp in checkpoints:
        with contextlib.redirect_stdout(io.StringIO()):
            packing = canonical_spherical_layout(packing, n_iterations=cp - done)
        done = cp
        fl, ex = _sphere_edge_errors(packing, edges)
        _report_edges(f"[5] canonical_spherical_layout after {cp} iterations", edges, fl, ex)
    print(f"    (canonical layout took {time.time() - t0:.1f}s; float max above at "
          f"{args.canonical} iterations is the pipeline's packing_residual)")

    # ---- 6. tangency points ------------------------------------------------
    with contextlib.redirect_stdout(io.StringIO()):
        compute_tangencies(packing)
    off_circle, off_sphere = [], []
    verts = packing.verts
    for e in packing.edges:
        u, v = e.endPoints()
        p = e.data
        px, py, pz = _D(p.x), _D(p.y), _D(p.z)
        off_sphere.append(float(abs((px * px + py * py + pz * pz).sqrt() - 1)))
        for D in (u.data, v.data):
            a, b, c, d = (_D(t) for t in D)
            # distance from the cap's plane, relative to its boundary circle's size
            off_circle.append(float(abs(a * px + b * py + c * pz + d)
                                    / (a * a + b * b + c * c - d * d).sqrt()))
    fl, ex = _sphere_edge_errors(packing, edges)
    _report_edges("[6] compute_tangencies: |inversive distance - 1| (disks unchanged)", edges, fl, ex)
    _summ("tangency point off its circles (rel.)", off_circle)
    _summ("tangency point off the unit sphere", off_sphere)


if __name__ == "__main__":
    main()
