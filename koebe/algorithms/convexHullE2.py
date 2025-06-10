from koebe.geometries.euclidean2 import PointE2, PolygonE2


def convex_hull(points):
    """ Find the convex hull of a set of points in E2 and return as 
        polygon.
    """
    points = sorted(points, key=lambda p: (p.x, p.y))  # Sort points lexicographically
    if len(points) <= 1:
        return PolygonE2(points)

    # Function to compute the orientation of the triplet (p, q, r)
    def orientation(p, q, r):
        return (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)

    # Build lower hull
    lower = []
    for p in points:
        while len(lower) >= 2 and orientation(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Build upper hull
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and orientation(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    # Remove the last point of each half because it is repeated at the beginning of the other half
    del lower[-1]
    del upper[-1]

    # Concatenate lower and upper hull to get the full convex hull
    return PolygonE2(lower + upper)