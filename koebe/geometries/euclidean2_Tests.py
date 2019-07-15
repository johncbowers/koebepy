import unittest

import math
from euclidean2 import PointE2, VectorE2

class TestPointE2(unittest.TestCase):

    def test_origin(self):
        origin = PointE2()
        self.assertEqual(origin.x, 0)
        self.assertEqual(origin.y, 0)

    def test_from(self):
        point1 = PointE2(4, 5)
        point2 = PointE2.fromPointE2(point1)
        self.assertTrue(point1 == point2 and not point1 is point2)
    
    def test_eq(self):
        point1 = PointE2(4, 5)
        point2 = PointE2(4, 5)
        self.assertEqual(point1, point2)
    
    def test_ne(self):
        point1 = PointE2(4, 5)
        point2 = PointE2(5, 4)
        self.assertNotEqual(point1, point2)
    
    def test_distSqTo(self):
        point1 = PointE2(0, 4)
        point2 = PointE2(3, 0)
        self.assertEqual(point1.distSqTo(point2), 25)
    
    def test_distTo(self):
        point1 = PointE2(0, 4)
        point2 = PointE2(3, 0)
        self.assertEqual(point1.distTo(point2), 5.0)
    
    def test_sub(self):
        point1 = PointE2(3, 4)
        point2 = PointE2(1, 1)
        v = point2 - point1
        self.assertEquals(v, VectorE2(-2, -3))


class TestVectorE2(unittest.TestCase):
    
    def test_add(self):
        v1 = VectorE2(3,4)
        v2 = VectorE2(-2,5)
        self.assertEqual(v1 + v2, VectorE2(1,9))

    def test_sub(self):
        v1 = VectorE2(3,4)
        v2 = VectorE2(-2,5)
        self.assertEqual(v1 - v2, VectorE2(5,-1))
                         
    def test_mul(self):
        v1 = VectorE2(3,4)
        self.assertEqual(v1 * 2, VectorE2(6,8))
                         
    def test_rmul(self):
        v1 = VectorE2(3,4)
        self.assertEqual(2 * v1, VectorE2(6,8))
    
    def testTrueDiv(self):
        v1 = VectorE2(3,4)
        self.assertEqual(v1 / 3, 
                         VectorE2(1, 4 / 3))
    
    def testNeg(self):
        v1 = VectorE2(3,4)
        self.assertEqual(-v1, VectorE2(-3, -4))
    
    def test_eq(self):
        v1 = VectorE2(4, 5)
        v2 = VectorE2(4, 5)
        self.assertEqual(v1, v2)
    
    def test_ne(self):
        v1 = VectorE2(4, 5)
        v2 = VectorE2(5, 4)
        self.assertNotEqual(v1, v2)
        
    def testDot(self):
        v1 = VectorE2(2,3)
        v2 = VectorE2(4,5)
        self.assertEqual(v1.dot(v2), 23)
    
    def testNormSq(self):
        v = VectorE2(3,4)
        self.assertEqual(v.normSq(), 25)
    
    def testNorm(self):
        v = VectorE2(3,4)
        self.assertEqual(v.norm(), 5.0)
    
    def testAngleFromXAxis(self):
        v1 = VectorE2(1,1)
        self.assertTrue(abs(v1.angleFromXAxis() - math.pi / 4.0) < 1e-8)
        v2 = VectorE2(-1, -1)
        self.assertTrue(abs(v2.angleFromXAxis() - math.pi * 5.0 / 4.0) < 1e-8)
        
if __name__ == '__main__':
    unittest.main()