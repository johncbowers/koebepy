from koebe.datastructures.dcel import *

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
        tiling.faces[-1].tileType = tileType
        return tiling
    
    def generateTiling(self, initialTileType, depth = 1):
        tiling = self.createInitialTile(initialTileType)
        for _ in range(depth): tilingPass(tiling, self)
        return tiling

    
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
        self.tileVerts    = tileVerts
        self.splitRules   = dict()
        self.childDartsOf = dict()
        self.parentDartOf = dict()
        self.newVertRules = list()
        self.subtiles     = list()
    
    def addSplitEdgeRule(self, edge, newverts):
        """
        Adds a rule to split an edge by introducing a series of new verts. For example
        if edge is "AB" and newverts is "a" this command will split the edge AB into
        Aa and aB. If newverts is "abc" then AB is split into Aa ab bc and cB. 
        Args:
            self
            edge: The name of the edge to split, like "AB"
            newverts: The new vertices to introduce, like "a". 
        """
        self.splitRules[edge[0]] = (edge, newverts)
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
                For example, ("AB", "a") would split the edge AB into two edges Aa and 
                aB. 
        """
        for edge, newverts in splitCommands: 
            self.addSplitEdgeRule(edge, newverts)
    
    def addNewVertexRule(self, vertName):
        self.newVertRules.append(vertName)
    
    def addNewVertexRules(self, vertNames):
        for vertName in vertNames:
            self.addNewVertexRule(vertName)
    
    def addSubtile(self, subtileType, subtileVerts):
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

def tilingPass(tilingRules, tiling):
    
    # tiles that need to be subdivided
    tiles = [tile for tile in tiling.faces if tile != tiling.outerFace]
    
    tiling.addLevel()
    
    dartsByNameForTile = [originNameToDartDict(tilingRules, tile) for tile in tiles]

def _old_setTileAnnotations(tilingRules, tiles):
    """
    For each tile adds a .vertexByName dictionary for mapping 
    """
    for tile in tiles: 
        prototile = tilingRules.getPrototile(tile.tileType)
        theDarts  = tile.darts()
        
        if len(theDarts) != len(prototile.tileVerts):
            raise PrototileFormationError(
                    f"Prototile vertex count ({len(theDarts)}) does not match tile"
                    + f" vertex count for tile type {tile.tileType}."
            )
        
        tile.vertexByName = {}
        # Build a mapping from vertex names to darts originating at the vertex
        # and vice versa. 
#         tile.vertexToDart   = {}
        for i in range(len(theDarts)):
            vertexName = prototile.tileVerts[i]
#             tile.vertexToDart[vertexName] = theDarts[i]
            theDarts[i].originName = vertexName
        
        tile.edgeNameToDart = {}
        for dart in theDarts:
            name = (dart.originName, dart.next.originName)
            tile.edgeNameToDart[name] = dart
            dart.edgeName = name
        
        tile.splitEdgeNameToDart = {}
    
def _old_tilingPass(tilingRules, tiling):
    
    # tiles that need to be subdivided
    tiles = [tile for tile in tiling.faces if tile != tiling.outerFace]
    
    # Annotate each tile with dictionaries to switch between 
    # vertex names and darts within the tile and edge names and darts. 
    setTileAnnotations(tilingRules, tiles)
            
    # For each tile, annotate any edge that needs to be split with its split rules. 
    for tile in tiles:
        prototile = tilingRules.getPrototile(tile.tileType)
        theDarts  = tile.darts()
        for dart in theDarts:
            if dart.edgeName in prototile.splitRules:
                dart.splitRule = prototile.splitRules[dart.edgeName]
            else:
                dart.splitRule = ""
    for dart in tiling.outerFace.darts():
        dart.splitRule = ""
    
    def annotateAndCheckEdge(edge):
        """
        Annotates the edge with .newVertexCount, the number of new vertices to subdivide it into. 
        Return:
            True iff. the split count is consistent on both sides of the edge. 
        """
        dart1, dart2 = edge.darts()
        if dart1.face == edge.dcel.outerFace:
            edge.newVertexCount = len(dart2.splitRule)
        elif dart2.face == edge.dcel.outerFace:
            edge.newVertexCount = len(dart1.splitRule)
        elif len(dart1.splitRule) == len(dart2.splitRule):
            edge.newVertexCount = len(dart2.splitRule)
        else:
            edge.newVertexCount = None
        return edge.newVertexCount != None
    
    def raiseEdgeError(edge):
        dart1, dart2 = edge.darts()
        tileName1 = dart1.face.tileType
        tileName2 = dart2.face.tileType
        splitCount1 = len(dart1.splitRule) + 1
        splitCount2 = len(dart2.splitRule) + 1
        
        raise PrototileFormationError(
                "Edge subdivision cannot be performed because "
                + f"edge {dart1.edgeName} of tile {tileName1}"
                + f" has to split into {splitCount1} edges"
                + " but is matched with "
                + f"edge {dart2.edgeName} of tile {tileName2}," 
                + f" which has to split into {splitCount2} edges"
        )
    
    # Check that each edge compiles:
    for edge in tiling.edges:
        if not annotateAndCheckEdge(edge):
            raiseEdgeError(edge)
    
    # Now we need to actually split each edge introducing new vertices
    # then add the new edges and stitch the tiles up. 

    def getSplitVertexNames(dart):
        """ For each dart get the vertex names for the split. For example
            if we're splitting a dart representing AB in a tiling by introducing
            a single vertex named a, then getSplitVertexNames will return ("A", "a", "B")
            as a tuple.
            
            Args: 
            dart: The dart that needs to be split. 
            
            Returns:
            A tuple containing the vertex names for the split version of the dart.
        """
        if dart.face != dart.dcel.outerFace:
            split_vertex_names = (dart.edgeName[0]) + dart.splitRule + (dart.edgeName[-1])
#             print(f"dart splitRule: {dart.edgeName} to {dart.splitRule} to form {split_vertex_names}")
        else:
            split_vertex_names = None
        return split_vertex_names
    
    def setVertexAndEdgeNames(dartList, vertexNames, parentTile, lastVertex):
        if vertexNames != None:
            for i in range(len(dartList)):
                d = dartList[i]
                d.edgeName = (vertexNames[i], vertexNames[i+1])
                if parentTile != d.dcel.outerFace:
                    parentTile.vertexByName[vertexNames[i]] = d.origin 
                    parentTile.splitEdgeNameToDart[d.edgeName] = d
            if parentTile != d.dcel.outerFace:
                parentTile.vertexByName[vertexNames[-1]] = lastVertex
    
    old_darts, old_edges, old_faces = tiling.addLevel() # Push all the current level info onto the various stacks and reset for new one. 
    
    # Split all edges/darts according to their split rules and store a mapping from new split dart names
    # to Dart objects in the corresponding tile. 
    for e in old_edges:
        
        # For each dart get the vertex names for the split. For example
        # if we're splitting a dart representing AB in a tiling by introducing
        # a single vertex named a, then getSplitVertexNames will return ("A", "a", "B")
        # as a tuple. 
        vertNames1 = getSplitVertexNames(e.aDart)
        vertNames2 = getSplitVertexNames(e.aDart.twin)
        
        # Create the new vertices along the edge and the new darts. 
        newVerts = [Vertex(e.dcel) for _ in range(e.newVertexCount)]  
        
        nDarts1 = ([Dart(e.dcel, origin = e.aDart.origin)] 
                   + [Dart(e.dcel, origin = v) for v in newVerts])
        
        nDarts2 = ([Dart(e.dcel, origin = e.aDart.dest)] 
                   + [Dart(e.dcel, origin = v) for v in reversed(newVerts)])
        
        setVertexAndEdgeNames(nDarts1, vertNames1, e.aDart.face, e.aDart.dest)
        setVertexAndEdgeNames(nDarts2, vertNames2, e.aDart.twin.face, e.aDart.origin)
        
        e.aDart.childDarts = nDarts1
        e.aDart.twin.childDarts = nDarts2
        
        e.childEdges = []
        for i in range(len(nDarts1)):
            nDarts1[i].makeTwin(nDarts2[len(nDarts2) - 1 - i])
            newEdge = Edge(e.dcel, aDart = nDarts1[i])
            e.childEdges.append(newEdge)
            nDarts1[i].edge = newEdge
            nDarts2[i].edge = newEdge
    
    # Split all tiles
    for tile in tiles:
        # Create any new vertices not obtained via splitting
        # and add them to the vertexByName map. 
        
        # Create a new face for each subtile getting either a dart
        # created in the edge split pass or creating a brand new dart
        
        # Loop over all the darts and find any that do not have a twin
        # for any that do not have a twin, set their twin correctly and
        # create an Edge between them
        
        pass
    print(tile.vertexByName)


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
                dart.twin.splitVertices = list(reversed(dart.splitVertices))
            else:
                for vIdx in range(len(splitRule[1])):
                    vert = dart.splitVertices[vIdx]
                    vName = splitRule[1][vIdx]
                    vertNamed[vName] = vert

        # Create the other new vertices
        for vName in prototile.newVertRules:
            vertNamed[vName] = TilingVertex(tiling)

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


def generateCirclePackingLayout(tiling, num_passes = 1000, centerDartIdx = -1):
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
        num_passes=num_passes,
        centerDartIdx=centerDartIdx
    )

    # Annotate each vertex with whether it is an original tile vertex
    # (i.e. .is_tile_vertex == True) or is one of the vertices added
    # to triangulate each face. 
    for vIdx in range(len(packing.verts)):
        packing.verts[vIdx].is_tile_vertex = vIdx < tile_vertex_count
    
    return packing, duplicate_tiling
