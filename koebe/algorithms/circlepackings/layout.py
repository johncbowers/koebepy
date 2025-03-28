import math
from koebe.geometries.euclidean3 import VectorE3
from koebe.geometries.orientedProjective2 import DiskOP2
from koebe.geometries.spherical2 import DiskS2

def tangency_point(D1, D2):
    return D1.tangentPointWith(D2)

def compute_tangencies(packingS2):
    """
    Computes the set of tangent points for a circle packing and stores them as the e.data for each edge in packingS2

    Args:
        packingS2: A DCEL where every vertex v has a DiskS2 object as its v.data and every edge ij represents a tangency
    """
    for e in packingS2.edges:
        e.data = tangency_point(*[v.data for v in e.endPoints()])

def canonical_spherical_projection(hyp_packing, n_iterations=50):
    """
    Computes the canonical projection of hyp_packing onto the sphere S^2 where the center of mass
    of all points of tangency is the origin. The algorithm is numerical and in testing converges
    extremely quickly. n_iterations = 50 is the default, but is almost certainly overkill for most
    applications, but because it is far less expensive to do this 50 times than it is to compute
    the original packing, I'm leaving it as the default. 

    Args:
        hyp_packing: A maximal packing of the hyperoblic plane stored in a DCEL as computed by hypPacker.py
        n_iterations: 
        n_iterations: (Default 50) the number of layout iterations to perform

    """
    packing = hyp_packing.duplicate(
        vdata_transform=lambda d: DiskOP2.fromCircleE2(d.toPoincareCircleE2()).toDiskS2()
    )
    return canonical_spherical_layout(packing, n_iterations)

def canonical_spherical_layout(packingS2, n_iterations=50):
    """
    Computes the canonical packing (via Moebius transformations) taking the packing (whose vertex data is 
    assumed to be a collection of DiskS2 objects mutually tangent at each edge) to a packing where
    the center of mass of all tangency points is the origin. 

    Args:
        packingS2: a DCEL where every vertex v has a DiskS2 object as its v.data and every edge ij represents a tangency
        n_iterations: (Default 50) the number of layout iterations to perform
    """
    I1 = DiskS2(1, 0, 0, 0)

    for _ in range(50):
        packingS2 = packingS2.duplicate(
            vdata_transform=lambda d: d.invertThrough(I1)
        )

        # Compute the current center of mass of the tangency points
        compute_tangencies(packingS2)
        points_to_center = [e.data.toVectorE3() for e in packingS2.edges]
        center_of_mass = (1/len(points_to_center)) * sum(points_to_center, start=VectorE3(0,0,0))
        
        # Create a DiskS2 object representing the center of mass (note it will have imaginary radius, since this is a timelike ray
        # in the Minkowski spacetime). 
        center_of_mass_disk = DiskS2(center_of_mass.x, center_of_mass.y, center_of_mass.z, -1)

        # Compute the vector pointed at the origin of Euclidean 3-space that has the same Lorentz-length as center_of_mass_disk
        new_center = DiskS2(0, 0, 0, math.sqrt(abs(center_of_mass_disk.lorentzTo(center_of_mass_disk))))

        # Get the Lorentz-bisector plane between center_of_mass_disk and new_center, a circle inversion through this bisector
        # will move center_of_mass_disk onto new_center
        I2 = new_center.bisectorWith(center_of_mass_disk).dualDiskS2

        # Apply the inversion to every disk in the packing
        packingS2 = packingS2.duplicate(
            vdata_transform=lambda d: d.invertThrough(I2)
        )
    
    return packingS2