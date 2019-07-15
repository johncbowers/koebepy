import unittest

import math
from euclidean3 import *
from orientedProjective3 import *

class TestPointE3(unittest.TestCase):
    def test_fromPointE3(self):
        self.assertEqual(
            PointE3.fromPointE3(PointE3(1,2,3)),
            PointE3(1,2,3)
        )
    def test_add(self):
        self.assertEqual(
            PointE3(1,2,3)+VectorE3(2,2,2),
            PointE3(3,4,5)
        )
    def test_sub(self):
        self.assertEqual(
            PointE3(1,2,3)-PointE3(1,1,1),
            VectorE3(0,1,2)
        )
    def test_distSqTo(self):
        self.assertEqual(
            PointE3(1,2,3).distSqTo(PointE3(0,0,0)),
            14
        )
    def test_distTo(self):
        self.assertEqual(
            PointE3(1,2,3).distTo(PointE3(0,0,0)),
            math.sqrt(14)
        )
    def test_toVectorE3(self):
        v = PointE3(1,2,3).toVectorE3()
        self.assertIsInstance(v, VectorE3)
        self.assertTrue(v.x == 1
                        and v.y == 2
                        and v.z == 3)
    def test_eq(self):
        self.assertTrue(PointE3(1,2,3) == PointE3(1,2,3))
    def test_ne(self):
        self.assertTrue(PointE3(1,2,3) != PointE3(3,2,1))

class TestVectorE3(unittest.TestCase):
    def test_fromVectorE3(self):
        self.assertEqual(VectorE3.fromVectorE3(VectorE3(1,2,3)),
                         VectorE3(1,2,3))
    def test_add(self):
        self.assertEqual(
            VectorE3(1,2,3)+VectorE3(2,2,2),
            VectorE3(3,4,5)
        )
    def test_sub(self):
        self.assertEqual(
            VectorE3(1,2,3)-VectorE3(1,1,1),
            VectorE3(0,1,2)
        )
    def test_mul(self):
        self.assertEqual(VectorE3(1,2,3)*3,
                         VectorE3(3,6,9))
    def test_rmul(self):
        self.assertEqual(3*VectorE3(1,2,3),
                         VectorE3(3,6,9))
    def test_truediv(self):
        self.assertEqual(VectorE3(3,6,9)/3,
                         VectorE3(1,2,3))
    def test_neg(self):
        self.assertEqual(-VectorE3(1,2,3),
                         VectorE3(-1, -2, -3))
    def test_dot(self):
        self.assertEqual(VectorE3(1,2,3).dot(VectorE3(4,1,5)),
                    21)
    def test_normSq(self):
        self.assertEqual(VectorE3(1,2,3).normSq(),
                         14)
    def test_norm(self):
        self.assertEqual(VectorE3(1,2,3).norm(),
                         math.sqrt(14))
    def test_normalize(self):
        inv = 1.0 / math.sqrt(3)
        self.assertEqual(VectorE3(1,1,1).normalize(), 
                         VectorE3(inv, inv, inv))
    def test_cross(self):
        self.assertEqual(VectorE3(3, -3, 1).cross(VectorE3(4, 9, 2)), 
                         VectorE3(-15, -2, 39))
    def test_toPointE3(self):
        p = VectorE3(3,4,5).toPointE3()
        self.assertIsInstance(p, PointE3)
        self.assertEqual(p, PointE3(3, 4, 5))
    def test_eq(self):
        self.assertEqual(VectorE3(1,2,3), VectorE3(1,2,3))
    def test_ne(self):
        self.assertNotEqual(VectorE3(1,2,3),VectorE3(1,1,1))

class TestDirectionE3(unittest.TestCase):
    def test_v(self):
        self.assertEqual(DirectionE3(VectorE3(1,1,1)).v,
                         VectorE3(1,1,1).normalize())     
    def test_endPoint(self):
        self.assertEqual(DirectionE3(VectorE3(1,1,1)).endPoint,
                         PointE3(1/math.sqrt(3),1/math.sqrt(3),1/math.sqrt(3)))
    def test_add(self):
        self.assertEqual(
            (DirectionE3(VectorE3(2,0,0)) + DirectionE3(VectorE3(3,0,0))).v,
            VectorE3(1,0,0))
    def test_sub(self):
        self.assertEqual((DirectionE3(VectorE3(2,0,0)) - DirectionE3(VectorE3(3,0,0))).v,
                         VectorE3(0,0,0))
    def test_neg(self):
        self.assertEqual(-DirectionE3(VectorE3(1,0,0)),
                          DirectionE3(VectorE3(-1, 0, 0)))
    def test_dot(self):
        self.assertEqual(DirectionE3(VectorE3(3,0,0)).dot(
                            DirectionE3(VectorE3(0,4,0))), 
                         0.0)
    def test_cross(self):
        self.assertEqual(DirectionE3(VectorE3(1,0,0)).cross(
                            DirectionE3(VectorE3(0,2,0))),
                         DirectionE3(VectorE3(0,0,1)))
    def test_eq(self):
        self.assertEqual(DirectionE3(VectorE3(1,0,0)), 
                         DirectionE3(VectorE3(2,0,0)))
    def test_ne(self):
        self.assertNotEqual(DirectionE3(VectorE3(1,0,0)),
                            DirectionE3(VectorE3(0,1,0)))
        
class TestPlaneE3(unittest.TestCase):
    def test_fromThreePointE3(self):
        self.assertEqual(
            PlaneE3.fromThreePointE3(
                PointE3(1,0,0),
                PointE3(0,1,0),
                PointE3(1,1,0)
            ), 
            PlaneE3(VectorE3(0,0,-1))
        )
    def test_pointE3ClosestOrigin(self):
        self.assertEqual(
            PlaneE3.fromThreePointE3(
                PointE3(1,0,1),
                PointE3(0,1,1),
                PointE3(1,1,1)
            ).pointE3ClosestOrigin(),
            PointE3(0,0,1)
        )
    def test_pointOP3ClosestOrigin(self):
        self.assertEqual(
            PlaneE3.fromThreePointE3(
                PointE3(1,0,1),
                PointE3(0,1,1),
                PointE3(1,1,1)
            ).pointOP3ClosestOrigin(),
            PointOP3(0,0,1,1)
        )

if __name__ == '__main__':
    unittest.main()