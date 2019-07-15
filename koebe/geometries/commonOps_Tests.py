
import unittest 
from commonOps import *

class TestCommonOps(unittest.TestCase):
    def test_isZero(self):
        self.assertTrue(isZero(0))
        self.assertFalse(isZero(1.0))
        self.assertFalse(isZero(-1.0))
    def test_determinant2(self):
        self.assertEqual(determinant2(1, 2, 3, 4), -2)
    def test_determinant3(self):
        self.assertEqual(determinant3(1, 2, 3,
                                      4, 5, 6, 
                                      7, 8, 10), 
                         -3
                        )
    def test_determinant4(self):
        self.assertEqual(determinant4(1, 3, 5, 9, 
                                      1, 3, 1, 7, 
                                      4, 3, 9, 7, 
                                      5, 2, 0, 9), 
                         -376
                        )
    def test_inner_product2(self):
        self.assertEqual(inner_product2(1, 2, 3, 4), 
                         11
                        )
    def test_inner_product3(self):
        self.assertEqual(inner_product3(1, 2, 3, 4, 5, 6), 
                         32
                        )
    def test_inner_product4(self):
        self.assertEqual(inner_product4(1, 2, 3, 4,
                                        5, 6, 7, 8), 
                         70
                        )
    def test_inner_product31(self):
        self.assertEqual(inner_product31(1, 2, 3, 4,
                                         5, 6, 7, 8), 
                         6
                        )
    def test_norm31(self):
        self.assertEqual(norm31(1, 2, 3, 4), 
                         -2
                        )
    def test_are_dependent3(self):
        self.assertTrue(are_dependent3(1, 2, 3, 2, 4, 6))
        self.assertFalse(are_dependent3(1, 2, 3, 2, 4, 7))
    def test_are_dependent4(self):
        self.assertTrue(are_dependent4(1, 2, 3, 4, 
                                       2, 4, 6, 8))
        self.assertFalse(are_dependent4(1, 2, 3, 4, 
                                        2, 4, 6, 9))

if __name__ == '__main__':
    unittest.main()