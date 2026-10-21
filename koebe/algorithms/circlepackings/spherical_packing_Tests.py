import random
import unittest

import numpy as np

from koebe.algorithms.incrementalConvexHull import randomConvexHullE3
from koebe.algorithms.circlepackings.newton_packing import newton_packing
from koebe.algorithms.circlepackings.spherical_packing import (
    spherical_packing, refine_spherical_packing, refine_caps, canonical_center,
    tangency_point_centroid, tangency_errors, inversive_distances,
    disks_to_caps, caps_to_disks, _combinatorics, _face_orientations,
)


def _triangulation(n, seed):
    random.seed(seed)
    poly = randomConvexHullE3(n)
    poly.outerFace = poly.faces[0]
    return poly


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.T = _triangulation(300, 1)
        cls.packing, cls.info = spherical_packing(cls.T, return_info=True)

    def test_two_stage_low_error(self):
        err = tangency_errors(self.packing)
        self.assertTrue(self.info.converged)
        self.assertTrue(self.info.orientation_preserved)
        self.assertLess(err.max(), 1e-12)
        self.assertLess(self.info.final_error, self.info.initial_error)

    def test_vertex_data_are_disks_matching_caps(self):
        X = np.array([[v.data.a, v.data.b, v.data.c, v.data.d] for v in self.packing.verts])
        N, r = disks_to_caps(X)
        self.assertLess(np.max(np.abs(N - self.packing.sphere_centers)), 1e-12)
        self.assertLess(np.max(np.abs(r / self.packing.sphere_radii - 1)), 1e-8)

    def test_canonical_normalization(self):
        edges, _ = _combinatorics(self.packing)
        X = np.array([[v.data.a, v.data.b, v.data.c, v.data.d] for v in self.packing.verts])
        self.assertLess(np.linalg.norm(tangency_point_centroid(X, edges)), 1e-9)

    def test_caps_roundtrip(self):
        rng = np.random.default_rng(0)
        N = rng.standard_normal((50, 3)); N /= np.linalg.norm(N, axis=1)[:, None]
        r = rng.uniform(1e-4, 3.0, 50)
        X = np.array([list(d) for d in caps_to_disks(N, r)])
        N2, r2 = disks_to_caps(X)
        self.assertLess(np.max(np.abs(N2 - N)), 1e-14)
        self.assertLess(np.max(np.abs(r2 - r)), 1e-10)

    def test_inversive_distance(self):
        # Tangent edges have inversive distance 1; agrees with DiskS2 for
        # well-conditioned (non-adjacent) pairs.
        self.packing.markIndices()
        edges = [(e.endPoints()[0].idx, e.endPoints()[1].idx) for e in self.packing.edges]
        self.assertLess(np.max(np.abs(inversive_distances(self.packing, edges) - 1)), 1e-12)
        V = self.packing.verts
        pairs = [(0, 5), (3, 17), (10, 200)]
        ours = inversive_distances(self.packing, pairs)
        theirs = [V[i].data.inversiveDistTo(V[j].data) for i, j in pairs]
        self.assertLess(np.max(np.abs(ours - np.array(theirs)) / np.abs(ours)), 1e-8)

    def test_refine_recovers_from_large_perturbation(self):
        p = newton_packing(_triangulation(200, 2))
        edges, faces = _combinatorics(p)
        X = canonical_center(np.array([[v.data.a, v.data.b, v.data.c, v.data.d] for v in p.verts]), edges)
        N0, r0 = disks_to_caps(X)
        rng = np.random.default_rng(1)
        r = r0 * (1 + 0.05 * rng.standard_normal(len(r0)))
        N = N0 + 0.05 * r0[:, None] * rng.standard_normal(N0.shape)
        Nf, rf, info = refine_caps(N, r, edges)
        self.assertTrue(info.converged)
        self.assertLess(info.final_error, 1e-12)
        self.assertTrue(np.all(_face_orientations(Nf, faces) == _face_orientations(N0, faces)))

    def test_rejects_non_triangulation(self):
        from koebe.datastructures.dcel import DCEL
        square = DCEL.generateCycle(4)   # two quadrilateral faces
        with self.assertRaises(ValueError):
            _combinatorics(square)


if __name__ == '__main__':
    unittest.main()
