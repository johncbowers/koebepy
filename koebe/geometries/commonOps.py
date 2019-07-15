# Test if x is zero?
def isZero(x):
    return abs(x) < 1e-8

# Compute the 2x2 determinant
def determinant2(a, b, 
                 c, d):
    return a * d - b * c

# Compute the 3x3 determinant
def determinant3(a, b, c,
                 d, e, f,
                 g, h, i):
    return (
        + a * determinant2(e, f, h, i)
        - b * determinant2(d, f, g, i)
        + c * determinant2(d, e, g, h)
    )

# Compute the 4x4 determinant
def determinant4(a, b, c, d,
                 e, f, g, h,
                 i, j, k, l,
                 m, n, o, p):
    return (
        + a * determinant3(f, g, h, j, k, l, n, o, p)
        - b * determinant3(e, g, h, i, k, l, m, o, p)
        + c * determinant3(e, f, h, i, j, l, m, n, p)
        - d * determinant3(e, f, g, i, j, k, m, n, o)
    )

# Euclidean 2D inner product
def inner_product2(x1, y1, 
                   x2, y2): 
    return x1*x2 + y1*y2

# Euclidean 3D inner product
def inner_product3(x1, y1, z1,
                   x2, y2, z2): 
    return x1*x2 + y1*y2 + z1*z2

# Euclidean 4D inner product
def inner_product4(x1, y1, z1, w1,
                   x2, y2, z2, w2): 
    return x1*x2 + y1*y2 + z1*z2 + w1*w2

# Minkowski-(3,1) inner product
def inner_product31(x1, y1, z1, w1,
                    x2, y2, z2, w2): 
    return x1*x2 + y1*y2 + z1*z2 - w1*w2

# Minkowski-(3,1) norm
def norm31(x1, y1, z1, w1): 
    return x1*x1 + y1*y1 + z1*z1 - (w1*w1)

# Are the vectors (a1, b1, c1), (a2, b2, c2) dependent?
def are_dependent3(a1, b1, c1,
                   a2, b2, c2):
    return (
        isZero(determinant2(a1, b1, a2, b2))
        and isZero(determinant2(a1, c1, a2, c2))
        and isZero(determinant2(b1, c1, b2, c2))
    )

# Are the vectors (a1, b1, c1, d1), (a2, b2, c2, d2) dependent?
def are_dependent4(a1, b1, c1, d1,
                   a2, b2, c2, d2):
    return (
            isZero(determinant2(a1, b1, a2, b2))
        and isZero(determinant2(a1, c1, a2, c2))
        and isZero(determinant2(a1, d1, a2, d2))
        and isZero(determinant2(b1, c1, b2, c2))
        and isZero(determinant2(b1, d1, b2, d2))
        and isZero(determinant2(c1, d1, c2, d2))
    )