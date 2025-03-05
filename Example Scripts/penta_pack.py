from koebe.algorithms.tiling import *
from koebe.geometries.euclidean2 import PointE2
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2


########################################
# Set up the finite subdivision rules
########################################

# # The chair tiling only has one prototile
# pent_rules = TilingRules()

# pent = pent_rules.createPrototile("pent", tuple("ABCDE"))

# # Edges that need to be split
# pent.addSplitEdgeRules(((("A","B"), ("a", "b")), 
#                         (("B","C"), ("c", "d")), 
#                         (("C","D"), ("e", "f")),
#                         (("D","E"), ("g", "h")), 
#                         (("E","A"), ("i", "j"))))

# # New vertices to create
# pent.addNewVertexRules(("k"))

# # The subdivision subtiles: 
# pent.addSubtile("pent", tuple("Aabkj"))
# pent.addSubtile("pent", tuple("Bcdkb"))
# pent.addSubtile("pent", tuple("Cefkd"))
# pent.addSubtile("pent", tuple("Dghkf"))
# pent.addSubtile("pent", tuple("Eijkh"))

# pent_tiling = pent_rules.generateTiling("pent", depth = 1)

# pent_packing, _ = generateCirclePackingLayout(pent_tiling)

# circles = [v.data.toPoincareCircleE2() for v in pent_packing.verts]


design1_rules = TilingRules()

hex = design1_rules.createPrototile("hex", tuple("ABCDEF"))
hex = design1_rules.createPrototile("tri", tuple("ABC"))

hex.addNewVertexRules(tuple("abc"))

hex.addSubtile("tri", tuple("ABa"))
hex.addSubtile("tri", tuple("aBb"))
hex.addSubtile("tri", tuple("bBC"))
hex.addSubtile("tri", tuple("bCD"))
hex.addSubtile("tri", tuple("bDc"))
hex.addSubtile("tri", tuple("cDE"))
hex.addSubtile("tri", tuple("cEF"))
hex.addSubtile("tri", tuple("cFa"))
hex.addSubtile("tri", tuple("aFA"))
hex.addSubtile("tri", tuple("abc"))

########################################
# Apply the rules
########################################

design1_tiling = design1_rules.generateTiling("hex", depth = 1)

design1_packing, _ = generateCirclePackingLayout(design1_tiling)

circles = [v.data.toPoincareCircleE2() for v in design1_packing.verts]


def svg_string(circles):
    out_str = '<?xml version="1.0" standalone="no"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" version="1.1" baseProfile="full">\n'
    for c in circles: 
        out_str += f'\t\n<circle cx="{c.center.x*600+600}" cy="{c.center.y*600+600}" r="{c.radius*600}" stroke="black" stroke-width="1" fill="none"/>\n'
    out_str += "</svg>"
    return out_str

with open('out_penta.svg', 'w') as f:
    f.write(svg_string(circles))