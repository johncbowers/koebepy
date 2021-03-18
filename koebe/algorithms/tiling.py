from koebe.datastructures.dcel import *

from koebe.graphics.euclidean2viewer import UnitScaleE2Sketch, PoincareDiskViewer, E2Viewer, makeStyle

class Tiling(DCEL):
    
    def __init__(self, outerFaceData = None):
        super().__init__(outerFaceData)

        self.dartLevels = []
        self.edgeLevels = []
        self.faceLevels = []
        self.subdivisionLevel = 1
        
        self.Vertex = TilingVertex
        self.Dart   = TilingDart
        self.Face   = Tile

    def addLevel(self):
        old_darts, old_edges, old_faces = self.darts, self.edges, self.faces
        
        self.dartLevels.append(self.darts)
        self.edgeLevels.append(self.edges)
        self.faceLevels.append(self.faces)
        
        self.darts = []
        self.edges = []
        self.faces = []
        
        self.subdivisionLevel += 1
        self.outerFace = self.Face(dcel = self)
        
        return old_darts, old_edges, old_faces

class TilingVertex(Vertex):
    def __init__(self, dcel, data = None):
        super().__init__(dcel = dcel, data = data)
        self.level = dcel.subdivisionLevel
    
class TilingDart(Dart):
    def __init__(self, 
                 dcel, 
                 edge   = None, 
                 origin = None, 
                 face   = None,
                 prev   = None,
                 next   = None,
                 twin   = None, 
                 data   = None):
        super().__init__(dcel = dcel, edge = edge, origin = origin, face = face, 
                         prev = prev, next = next, twin = twin, data = data)
        self.subdarts = []

class Tile(Face):
    def __init__(self, dcel, tileType=None, data=None):
        super().__init__(dcel = dcel, data = data)
        self.tileType = tileType
        self.subtiles = []
        
class TilingRules:
    
    def __init__(self):
        self.prototiles = {}
    
    def createPrototile(self, tileType, tileVerts):
        self.prototiles[tileType] = Prototile(self, tileType, tileVerts)
        return self.prototiles[tileType]
    
    def getPrototile(self, tileType):
        return self.prototiles[tileType]
    
    def createInitialTile(self, tileType):
        prototile = self.getPrototile(tileType)
        tiling    = Tiling.generateCycle(vdata = prototile.tileVerts)
        if prototile.tileData != []:
            for i in range(len(tiling.verts)):
                tiling.verts[i].point = prototile.tileData[i]
        tiling.faces[-1].tileType = tileType
        return tiling
    
    def generateTiling(self, initialTileType, depth = 1):
        tiling = self.createInitialTile(initialTileType)
        for _ in range(depth): tilingPass(tiling, self)
        return tiling

def midp(dart):
    from koebe.geometries.euclidean2 import PointE2
    u = dart.origin.point - PointE2.O
    v = dart.dest.point - PointE2.O
    vs = dart.splitVertices
    vs[0].point = PointE2.O + (u + v) / 2
    return vs[0].point
    
    
class Prototile:
    
    def __init__(self, tilingRules: TilingRules, tileType: str, tileVerts: str):
        """
        Args: 
            tilingRules: The TilingRules object that this prototile is a part of. 
            tileVerts: The name of the vertices. For example, "ABCDEF" is a 
                six sided tile with vertex names A, B, C, D, E, and F. 
        """
        self.tilingRules  = tilingRules
        self.tileType     = tileType
        if len(tileVerts) > 0 and isinstance(tileVerts[0], tuple):
            self.tileVerts = [v for v, _ in tileVerts]
            self.tileData = [d for _, d in tileVerts]
        else: 
            self.tileVerts = tileVerts
            self.tileData = []
        self.splitRules   = dict()
        self.splitFn      = dict()
        self.childDartsOf = dict()
        self.parentDartOf = dict()
        self.newVertRules = list()
        self.newVertFnHandler = None
        self.subtiles     = list()
    
    def addSplitEdgeRule(self, edge, newverts, fn = None):
        """
        Adds a rule to split an edge by introducing a series of new verts. For example
        if edge is "AB" and newverts is "a" this command will split the edge AB into
        Aa and aB. If newverts is "abc" then AB is split into Aa ab bc and cB. 
        Args:
            self
            edge: The name of the edge to split, like "AB"
            newverts: The new vertices to introduce, like "a". 
            fn (Optional): (Dart, List[Vertex])->None
        """
        if edge[0] in self.splitRules:
            raise PrototileFormationError("There appear to be two splits beginning with the same vertex. This probably means you either attempted to split the same edge twice, or did not orient your edges consistently.")
        self.splitRules[edge[0]] = (edge, newverts)
        if fn != None:
            self.splitFn[edge[0]] = fn
        splitEdge = [edge[0]] + list(newverts) + [edge[1]]
        self.parentDartOf.update(
            [((splitEdge[i], splitEdge[i+1]), edge) 
             for i in range(len(splitEdge) - 1)]
        )
        self.childDartsOf[edge] = [(splitEdge[i], splitEdge[i+1])
                                   for i in range(len(splitEdge) - 1)]
    
    def addSplitEdgeRules(self, splitCommands):
        """
        Args: 
            self
            splitCommands: A list of tuples of the form (edge, newverts) that directs
                the tiling to split this edge by introducing a series of new vertices. 
                For example, (("A", "B"), ("a")) would split the edge AB into two edges Aa and 
                aB. 
                
                The tuples may optionally contain a third parameter, a function fn of
                type (Face, (Vertex, Vertex), List[Vertex]) -> None that sets any additional
                data when the split occurs.
        """
        for command in splitCommands: 
            self.addSplitEdgeRule(*command)
    
    def addNewVertexRule(self, vertName):
        """
        Args:
            vertName: the name of the new vertex
            fn: (Face) -> None
        """
        self.newVertRules.append(vertName)
#         if fn != None:
#             self.newVertFn[vertName] = fn
    
    def setNewVertexHandlerFn(self, fn):
        self.newVertFnHandler = fn
    
    def addNewVertexRules(self, vertNames):
        for vertName in vertNames:
            self.addNewVertexRule(vertName)
    
    def addSubtile(self, subtileType, subtileVerts):
        if len(subtileVerts) != len(self.tilingRules.getPrototile(subtileType).tileVerts):
            raise PrototileFormationError(
                f"Subtiles of type {subtileType} require {len(self.tilingRules.getPrototile(subtileType).tileVerts)}"
                + f" vertices, but the given vertex set was {subtileVerts} with {len(subtileVerts)} vertices."
            )
        self.subtiles.append((subtileType, subtileVerts))
    
class PrototileFormationError(Exception):
    pass

def originNameToDartDict(tilingRules, tile):
    
    prototile = tilingRules.getPrototile(tile.tileType)
    theDarts  = tile.darts()
    
    if len(theDarts) != len(prototile.tileVerts):
        raise PrototileFormationError(
                f"Prototile vertex count ({len(theDarts)}) does not match tile"
                + f" vertex count for tile type {tile.tileType}."
        )
    
    return dict([(prototile.tileVerts[i], theDarts[i]) for i in range(len(theDarts))])

def subdivideTile(tilingRules, tiling, tile):
    prototile = tilingRules.getPrototile(tile)
    tile.subtiles = [Tile(tiling, prototile.subtiles[i][0]) for i in range(len(prototile.subtiles))]
    dartFrom = originNameToDartDict(tilingRules, tile)

def starTriangulateAllFaces(tiling):
    for face in tuple(tiling.faces):
        if face != tiling.outerFace:
            face.starTriangulate()

def tilingPass(tiling, tilingRules):
    
    #####
    # Subdivide a tile: 
    ##### 

    def subdivideTile(tiling, tile, tilingRules):

        prototile = tilingRules.getPrototile(tile.tileType) # Grab this tile's subdivision rules

        # Keep track of a few of the original items before we start the subdivision procedure
        originalDarts = tile.darts()

        originalDartFrom  = originNameToDartDict(tilingRules, tile) 
        vertNamed = dict([(vName, originalDartFrom[vName].origin) for vName in prototile.tileVerts])

        #####
        # 1. Create the new vertices. 
        #####

        # Create the new vertices required by each dart split:
        for i in range(len(originalDarts)):
            dart = originalDarts[i]
            splitRule = prototile.splitRules[prototile.tileVerts[i]] if prototile.tileVerts[i] in prototile.splitRules else (prototile.tileVerts[i], ())
            
            if dart.splitVertices == []:
                for vName in splitRule[1]:
                    vert = TilingVertex(tiling)
                    vertNamed[vName] = vert
                    dart.splitVertices.append(vert)
                if prototile.tileVerts[i] in prototile.splitFn:
                    fn = prototile.splitFn[prototile.tileVerts[i]]
                    fn(dart)
                dart.twin.splitVertices = list(reversed(dart.splitVertices))
            else:
                for vIdx in range(len(splitRule[1])):
                    vert = dart.splitVertices[vIdx]
                    vName = splitRule[1][vIdx]
                    vertNamed[vName] = vert

        # Create the other new vertices
        for vName in prototile.newVertRules:
            vertNamed[vName] = TilingVertex(tiling)
            
        if prototile.newVertFnHandler:
            fn = prototile.newVertFnHandler
            fn(vertNamed)
        

        #####
        # 2. Create the new darts and tiles.  
        #####

        dartNamed = {}
        nameOfDart = {}
        newDarts = []

        # Each tile is now split into subtiles and darts are created to surround each tile: 
        for subtileType, subtileVertNames in prototile.subtiles:
            subtile = Tile(tiling, subtileType)
            subtile.name = subtileVertNames
            tile.subtiles.append(subtile)
            subtile.parent = tile
            subtileDarts = [tiling.Dart(dcel = tiling, origin = vertNamed[vName], face=subtile) 
                            for vName in subtileVertNames]
            
            for i in range(len(subtileVertNames)):
                subtileDarts[i].name = subtileVertNames[i]
                subtileDarts[i].parent = None

            newDarts += subtileDarts
            subtile.aDart = subtileDarts[0]
            for i in range(len(subtileDarts)):
                subtileDarts[i-1].makeNext(subtileDarts[i]) # Stitches up the darts to be formed correctly.

            namesToDarts = [((subtileVertNames[i-1], subtileVertNames[i]), subtileDarts[i-1])
                             for i in range(len(subtileDarts))]
            
            dartNamed.update(namesToDarts)
            nameOfDart.update([(dart, name) for name, dart in namesToDarts])

        # Set the twin pointers for the internally created darts. 
        for i in range(len(newDarts)):
            origin, dest = nameOfDart[newDarts[i]]
            dart1 = dartNamed[(origin, dest)]
            if (dest, origin) in dartNamed and dart1.edge == None:
                dart2 = dartNamed[(dest, origin)]
                dart1.makeTwin(dart2)
                edge = tiling.Edge(tiling, dart1)
                dart1.edge = dart2.edge = edge

        # For each original dart, set its children list: 
        nameOfOriginalDart = dict([(originalDarts[i-1], (prototile.tileVerts[i-1], prototile.tileVerts[i])) 
                              for i in range(len(originalDarts))])
        
        for originalDart in originalDarts:
            name = nameOfOriginalDart[originalDart]
            originalDart.subdarts = [dartNamed[childName] 
                                     for childName in (prototile.childDartsOf[name] 
                                                       if name in prototile.childDartsOf 
                                                       else [name])]
            for subdart in originalDart.subdarts:
                subdart.parent = originalDart
    #####
    # Stitch the subtiles together. 
    #####
    def stitchSubTilesTogether(tiling):

        oldOuterFace = tiling.faceLevels[-1][0]
        oldFaces = tiling.faceLevels[-1]
        oldEdges = tiling.edgeLevels[-1]
        oldDarts = tiling.dartLevels[-1]

        for e in oldEdges:
            if e.aDart.face is not oldOuterFace and e.aDart.twin.face is not oldOuterFace:
                darts1 = e.aDart.subdarts
                darts2 = list(reversed(e.aDart.twin.subdarts))
                if len(darts1) != len(darts2):
                    raise PrototileFormationError(f"Edge ({e.aDart.name},{e.aDart.next.name}) of a {e.aDart.face.tileType} prototile is matched with edge ({e.aDart.twin.name},{e.aDart.twin.next.name}) of a {e.aDart.twin.face.tileType} prototile at level {e.dcel.subdivisionLevel-1}, but these do not split consistently.")
                for i in range(len(darts1)):
                    dart1, dart2 = darts1[i], darts2[i]
                    dart1.makeTwin(dart2)
                    edge = tiling.Edge(tiling, dart1)
                    dart1.edge = dart2.edge = edge

        # Now we need to deal with the outer face. 
        # First we need to split all of its edges appropriately to create subdarts. 
        # Then stitch them up with their twins. 
        for dart in oldOuterFace.darts():

            twinSubDarts = list(reversed(dart.twin.subdarts))
            dart.subdarts = [tiling.Dart(dcel = tiling, origin = twinSubDart.next.origin, face = tiling.outerFace)
                             for twinSubDart in twinSubDarts]

            for i in range(len(twinSubDarts)):
                twinSubDarts[i].makeTwin(dart.subdarts[i])
                edge = tiling.Edge(tiling, twinSubDarts[i])
                twinSubDarts[i].edge = dart.subdarts[i].edge = edge

            for i in range(len(dart.subdarts) - 1):
                dart.subdarts[i].makeNext(dart.subdarts[i+1])

        for dart in oldOuterFace.darts():
            dart.subdarts[-1].makeNext(dart.next.subdarts[0])

        tiling.outerFace.aDart = oldOuterFace.aDart.subdarts[0]

    for dart in tiling.darts:
        dart.splitVertices = []
        
    tiling.addLevel() # Push the current tiling level. 
    
    for tile in tiling.faceLevels[-1][1:]:
        subdivideTile(tiling, tile, tilingRules)
    
    stitchSubTilesTogether(tiling)
    
    for dart in tiling.darts:
        dart.origin.aDart = dart
        
def TilingViewer(packing, showCirclePacking = True, showTriangulation = True, size=(600,600)):
    import random

    from koebe.graphics.euclidean2viewer import PoincareDiskViewer, makeStyle
    from koebe.geometries.euclidean2 import PointE2, SegmentE2, PolygonE2

    def PointE2For(v):
        return PointE2(v.data.center.coord.real, v.data.center.coord.imag)

    def SegmentE2For(dart):
        return SegmentE2(PointE2For(dart.origin), PointE2For(dart.dest))

    def collectFaces(face):
        if len(face.subtiles) > 0:
            return [subface for subtile in face.subtiles for subface in collectFaces(subtile)]
        else: 
            return [face]
        
    viewer = PoincareDiskViewer(*size)
    
    # Uncomment to show super-tiles
    # level = 1
    # colors = ["#173679", "#0b1e38", "#db901c", "#e8e163", "#c6ca78", "#efe198", "hsl(120,100%,50%)"]
    # for i in range(1,len(original_pent_tiling.faceLevels[level])):
    #     rcolor = int(random.random() * 360)
    #     rsat =int(random.random()*50) + 50
    #     rlight = int(random.random()*40) + 50
    #     for tile in collectFaces(original_pent_tiling.faceLevels[level][i]):
    #         color = f"hsl({rcolor},{rsat}%,{rlight}%)"
    #         viewer.add(PolygonE2([PointE2For(v) for v in tile.vertices()]), 
    #                    makeStyle(fill=color))

    if showCirclePacking:
        circleStyle = makeStyle(stroke="#007849", strokeWeight=0.5)
        viewer.addAll([(v.data, circleStyle) for v in packing.verts])

    if showTriangulation:
        triSegStyle = makeStyle(stroke="#fece00", strokeWeight=1.0)
        triSegs = [(SegmentE2For(e.aDart), triSegStyle)
                   for e in packing.edges if not e.aDart.origin.is_tile_vertex or not e.aDart.dest.is_tile_vertex]
        viewer.addAll(triSegs)

    edgeStyle = makeStyle(stroke="#0375b4", strokeWeight=2.0)
    edgeSegs = [(SegmentE2For(e.aDart), edgeStyle)
               for e in packing.edges if e.aDart.origin.is_tile_vertex and e.aDart.dest.is_tile_vertex]
    viewer.addAll(edgeSegs)
    
    return viewer


def generateCirclePackingLayout(tiling, centerDartIdx = -1):
    # To circle pack we will have to triangulate each face, which adds
    # a new vertex for each face. We store the current vertex count
    # so we can distinguish between these new vertices and the originals
    # by index (index >= tile_vertex_count will be a triangulation
    # vertex)
    tile_vertex_count = len(tiling.verts)
    original_tiling = tiling
    duplicate_tiling = tiling.duplicate()
    starTriangulateAllFaces(duplicate_tiling)

    # Do the hyperbolic maximal circle packing
    from koebe.algorithms.hypPacker import maximalPacking
    packing, _ = maximalPacking(
        duplicate_tiling, 
        num_passes=1000,
        centerDartIdx=centerDartIdx
    )

    # Annotate each vertex with whether it is an original tile vertex
    # (i.e. .is_tile_vertex == True) or is one of the vertices added
    # to triangulate each face. 
    for vIdx in range(len(packing.verts)):
        packing.verts[vIdx].is_tile_vertex = vIdx < tile_vertex_count
    
    return packing, duplicate_tiling


def random_fill(tile):
    import random
    rcolor = int(random.random() * 360)
    rsat   = int(random.random()*70) + 30
    rlight = int(random.random()*50) + 40
    color = f"hsl({rcolor},{rsat}%,{rlight}%)"
    return makeStyle(fill=color)

def tileIdx_fill_fromList(colorList):
    def fn(tile):
        nonlocal colorList
        return makeStyle(fill=colorList[tile.idx % len(colorList)])
    return fn

def tileType_fill_fromDict(colorDict):
    def fn(tile):
        nonlocal colorDict
        return makeStyle(fill=colorDict[tile.tileType])
    return fn

def collectFaces(face):
    if len(face.subtiles) > 0:
        return [subface for subtile in face.subtiles for subface in collectFaces(subtile)]
    else: 
        return [face]

def GeometricTilingViewer(tiling, 
                          size=(600, 600), 
                          edgeStyle=makeStyle(stroke="#0375b4", strokeWeight=1.0), 
                          shadedLevel=-1, 
                          style_fn=random_fill, 
                          BaseViewer=E2Viewer, 
                          scale_factor=1,
                          scale_translation=(0,0)):

    import random

    from koebe.geometries.euclidean2 import PointE2, SegmentE2, PolygonE2
    
    w, h = size

    xs = [v.point.x for v in tiling.verts]
    ys = [v.point.y for v in tiling.verts]

    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    dx = maxx - minx
    dy = maxy - miny

    sc = min(w-6, h-6) / min(dx, dy)

    def mvPt(p):
        nonlocal minx, miny, w, h, scale_factor, scale_translation
        tx, ty = scale_translation
        return PointE2(((p.x - minx) * sc - w*0.5 + 3)*scale_factor+tx, ((p.y - miny) * sc - h*0.5 + 3)*scale_factor+ty)
        
    def pointSegmentE2For(dart):
        return SegmentE2(mvPt(dart.origin.point), mvPt(dart.dest.point))

    viewer = BaseViewer(w, h)

    if shadedLevel != -1 and shadedLevel <= len(tiling.faceLevels):
        faces = (tiling.faceLevels[shadedLevel] 
                 if shadedLevel < len(tiling.faceLevels) 
                 else tiling.faces)
        for i in range(1,len(faces)):
            faces[i].idx = i
            style = style_fn(faces[i])
            for tile in collectFaces(faces[i]):
                viewer.add(PolygonE2([mvPt(v.point) for v in tile.vertices()]), style)

    edgeSegs = [(pointSegmentE2For(e.aDart), edgeStyle)
               for e in tiling.edges]

    viewer.addAll(edgeSegs)
    return viewer

def CirclePackedTilingViewer(tiling, 
                              packing, 
                                size = (600, 600),
                                edgeStyle = makeStyle(stroke="#0375b4", strokeWeight=2.0),
                                showCircles = True,
                                circleStyle = makeStyle(stroke="#007849", strokeWeight=0.5),
                                showTriangulation = False,
                                triangulationStyle = makeStyle(stroke="#fece00", strokeWeight=1.0),
                                showBoundaryEdges = False,
                                shadedLevel = -1,
                                style_fn=random_fill,
                                BaseViewer=PoincareDiskViewer):

    for vIdx in range(len(tiling.verts)):
        tiling.verts[vIdx].idx = vIdx

    from koebe.geometries.euclidean2 import PointE2, SegmentE2, PolygonE2

    def PointE2For(v):
        return PointE2(v.data.center.coord.real, v.data.center.coord.imag)

    def SegmentE2For(dart):
        return SegmentE2(PointE2For(dart.origin), PointE2For(dart.dest))

    viewer = BaseViewer(600, 600)

    if shadedLevel != -1 and shadedLevel < len(tiling.faceLevels):
        faces = (tiling.faceLevels[shadedLevel]
                 if shadedLevel < len(tiling.faceLevels)
                 else tiling.faces)
        for i in range(1,len(faces)):
            faces[i].idx = i
            style = style_fn(faces[i])
            for tile in collectFaces(faces[i]):
                viewer.add(PolygonE2([PointE2For(packing.verts[v.idx]) for v in tile.vertices()]), style)

    if showCircles:
        viewer.addAll([(v.data, circleStyle) for v in packing.verts])

    # Ucomment to view the triangulation vertices
    if showTriangulation:
        if showBoundaryEdges:
            triSegs = [(SegmentE2For(e.aDart), triangulationStyle)
                   for e in packing.edges if not e.aDart.origin.is_tile_vertex or not e.aDart.dest.is_tile_vertex]
        else:
            triSegs = [(SegmentE2For(e.aDart), triangulationStyle)
                   for e in packing.edges if (not e.aDart.origin.is_tile_vertex or not e.aDart.dest.is_tile_vertex)
                      and not packing.outerFace in e.incidentFaces()]
        viewer.addAll(triSegs)

    if showBoundaryEdges:
        edgeSegs = [(SegmentE2For(e.aDart), edgeStyle)
               for e in packing.edges if e.aDart.origin.is_tile_vertex and e.aDart.dest.is_tile_vertex]
    else:
        edgeSegs = [(SegmentE2For(e.aDart), edgeStyle)
               for e in packing.edges 
                    if e.aDart.origin.is_tile_vertex and e.aDart.dest.is_tile_vertex
                       and not packing.outerFace in e.incidentFaces()]
    viewer.addAll(edgeSegs)
    
    return viewer

def TutteEmbeddedTilingViewer(tiling, 
                              tutteGraph, 
                              edgeStyle = makeStyle(stroke="#0375b4", strokeWeight=0.5),
                              shadedLevel = -1,
                              style_fn=random_fill, 
                              showVertices=False):

    from koebe.geometries.euclidean2 import SegmentE2, PolygonE2

    for vIdx in range(len(tiling.verts)):
        tiling.verts[vIdx].idx = vIdx

    viewer = UnitScaleE2Sketch()

    if shadedLevel != -1 and shadedLevel < len(tiling.faceLevels):
        faces = (tiling.faceLevels[shadedLevel]
                 if shadedLevel < len(tiling.faceLevels)
                 else tiling.faces)
        for i in range(1,len(faces)):
            faces[i].idx = i
            style = style_fn(faces[i])
            for tile in collectFaces(faces[i]):
                viewer.add(PolygonE2([tutteGraph.verts[v.idx].data for v in tile.vertices()]), style)

    viewer.addAll(
        [(SegmentE2(e.aDart.origin.data, e.aDart.twin.origin.data), edgeStyle)
        for e in tutteGraph.edges]
    )
    
    if showVertices: viewer.addAll([v.data for v in tutteGraph.verts])
    
    return viewer