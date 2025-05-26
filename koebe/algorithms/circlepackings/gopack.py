#
# This is a port of Ken Stephenson's matlab implemention of GoPack 
# from https://github.com/kensmath/GOPack.git
#

import math
from koebe.datastructures.dcel import DCEL

_TOLER = 1e-12

def gopack(dcel: DCEL):
   
   packing = dcel.duplicate()
   packing.markIndices()

   for v in packing.verts: 
       v.localradius = 0.5

   layoutBoundary(packing)
   layoutCenters(packing)
   setEffective(packing)

   return packing


def layoutBoundary(dcel: DCEL):
    bdry = dcel.outerFace.vertices()
   
    if len(bdry) <= 3:
        s3 = math.sqrt(3)
        brad = s3 / (2 + s3)
        for v in bdry: 
            v.localradius = brad
            v.aim = 0
        bdry[0].localcenter = (1-brad)*(1J)
        bdry[1].localcenter = (1-brad)*0.5*(-s3-1J)
        bdry[2].localcenter = (1-brad)*0.5*( s3-1J)
    
    # Initial guess for R, (sum of boundary radii)/pi
    bdryR = [v.localradius for v in bdry]
    minrad = max(bdryR)
    R = sum(bdryR) / math.pi
    if R < 2 * minrad:
        R = 3 * minrad
    
    # Newton iteration to find R
    tries = 0
    keepon = True

    while keepon and tries < 100:
        tries += 1
        
        Rrrs = [R - bdry[i].localradius - bdry[(i+1)%len(bdry)].localradius for i in range(len(bdry))]
        RRrrs = [R * Rrr for Rrr in Rrrs]
        abs = [bdry[i].localradius * bdry[(i+1)%len(bdry)].localradius for i in range(len(bdry))]
        fvalue = -2 * math.pi - sum([math.acos((RRrrs[i]-abs[i])/ (RRrrs[i]+abs[i])) for i in range(len(RRrrs))])
        fprime = -1.0 * sum([(R + Rrrs[i])*math.sqrt(abs[i]/RRrrs[i])/(RRrrs[i]+abs[i]) for i in range(len(RRrrs))])

        newR = R - fvalue / fprime
        if newR < R / 2.0:
            newR = R / 2.0
        elif newR > R * 2.0:
            newR = R * 2.0
        if abs(newR - R) < 0.00001:
            keepon = False
        R = newR
    
    # scale all radii by 1/R
    invR = 1.0 / R
    for v in bdry:
        v.localradius *= invR
    
    r2 = bdry[0].localradius
    bdry[0].localcenter = (1 - r2) * 1J
    arg = math.pi / 2.0
    for k in range(1, len(bdry)):
        r1 = r2
        r2 = bdry[k].localradius
        RRrr = 1 - r1 - r2
        ab = r1 * r2
        delta = math.acos((RRrr-ab)/(RRrr+ab))
        arg += delta
        d = 1 - r2
        bdry[k].localcenter = d * math.cos(arg) + 1J * math.sin(arg)

def layoutCenters(dcel: DCEL):
   pass

def setEffective(dcel: DCEL):
   pass