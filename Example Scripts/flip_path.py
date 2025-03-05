# Imports

# Algorithms:
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.sampling import surfaceSampling, boundarySampling
from koebe.algorithms.poissonDiskSampling import slowAmbientSurfaceSampling, slowAmbientBoundarySampling
#from koebe.algorithms.cvt import weightedCVT, worldToImgPixelCoords
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

# Graphics:
from koebe.graphics.spherical2viewer import *
from koebe.graphics.euclidean2viewer import PoincareDiskViewer, makeStyle

# Geometries:
from koebe.geometries.euclidean3 import PointE3, VectorE3, SegmentE3
from koebe.geometries.euclidean2 import SegmentE2, PointE2, VectorE2

# Linear Algebra:
import numpy as np

# Image creation:
from PIL import Image, ImageDraw, ImageFilter

# Other:
import random

random.seed(100)

poly = randomConvexHullE3(12)
poly.outerFace = poly.faces[0]

tutteGraph = tutteEmbeddingE2(poly)

xs = [float(v.data.x) for v in tutteGraph.verts]
ys = [float(v.data.y) for v in tutteGraph.verts]

minx, maxx = min(xs), max(xs)
miny, maxy = min(ys), max(ys)

for v in tutteGraph.verts:
    p = PointE2((v.data.x - minx) * 600+10, (v.data.y - miny) * 600+10)
    v.data = p

xs = [float(v.data.x) for v in tutteGraph.verts]
ys = [float(v.data.y) for v in tutteGraph.verts]

segments = [SegmentE2(e.aDart.origin.data, e.aDart.twin.origin.data) for e in tutteGraph.edges]

def svg_string(segments):
    out_str = '<?xml version="1.0" standalone="no"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" version="1.1" baseProfile="full">\n'
    for segment in segments: 
        p1 = segment.source
        p2 = segment.target
        out_str += f'\t\n<line x1="{p1.x}" y1="{p1.y}" x2="{p2.x}" y2="{p2.y}" style="stroke:black;stroke-width:1" />\n'
    out_str += "</svg>"
    return out_str

with open('out.svg', 'w') as f:
    f.write(svg_string(segments))