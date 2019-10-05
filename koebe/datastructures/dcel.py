# Doubly-connected edge list data structure

class DCEL:
    
    def __init__(self, outerFaceData = None):
        self.verts = []
        self.darts = []
        self.edges = []
        self.faces = []
        
        self.outerFace = (None if outerFaceData == None 
                               else Face(self, data = outerFaceData))
    
    def eulerCharacteristic(self):
        return len(self.verts) - (len(self.darts) / 2.0) + len(self.faces)

    def reorderVerticesByBoundaryFirst(self):
        bdryVerts = list(reversed(self.outerFace.vertices()))
        bdryVertSet = set(bdryVerts)
        otherVerts = [v for v in self.verts if v not in bdryVertSet]
        self.verts = bdryVerts + otherVerts
    
    def laplacian(self):
        vertToIdx = dict((v, k) for k, v in enumerate(self.verts))
        vertToDeg = [len(v.outDarts()) for v in self.verts]
        mat = [[0 for _ in range(len(self.verts))] for _ in range(len(self.verts))]
        for i in range(len(self.verts)):
            u = self.verts[i]
            neighbors = u.neighbors()
            mat[i][i] = len(neighbors)
            for v in neighbors:
                mat[i][vertToIdx[v]] = -1
        return mat
    
    def weightedLaplacian(self, weight):
        vertToIdx = dict((v, k) for k, v in enumerate(self.verts))
        vertToDeg = [len(v.outDarts()) for v in self.verts]
        mat = [[0 for _ in range(len(self.verts))] for _ in range(len(self.verts))]
        for i in range(len(self.verts)):
            u = self.verts[i]
            neighbors = u.neighbors()
            theSum = 0
            for v in neighbors:
                w = weight(u, v)
                theSum += w
                mat[i][vertToIdx[v]] = -w
            mat[i][i] = theSum
        return mat
    
    def boundaryVerts(self):
        if self.outerFace == None:
            return []
        return list(reversed(self.outerFace.vertices()))
        
    # WARNING: NOT THOROUGHLY TESTED, MAY CONTAIN BUGS
    # Duplicates this DCEL
    # optional parameters: 
    #
    #   * vdata_transform transform the vertex data on duplication
    #   * ddata_transform transform the edge data on duplication
    #   * fdata_transform transform the face data on duplication
    #
    def duplicate(self, vdata_transform = (lambda v : v), 
                        edata_transform = (lambda e : e), 
                        fdata_transform = (lambda f : f)):
        
        new_dcel = DCEL()        
        
        # create new versions for each object
        new_verts = [Vertex(new_dcel, data = vdata_transform(v.data)) for v in self.verts]
        new_darts = [Dart(new_dcel)                                   for _ in self.darts]
        new_edges = [Edge(new_dcel, data = edata_transform(e.data))   for e in self.edges]
        new_faces = [Face(new_dcel, data = fdata_transform(f.data))   for f in self.faces]
        
        o2n = dict() # old to new object map
        
        # Create the old to new map
        for i in range(len(self.verts)):
            o2n[self.verts[i]] = new_verts[i]
        
        for i in range(len(self.darts)):
            o2n[self.darts[i]] = new_darts[i]
        
        for i in range(len(self.edges)):
            o2n[self.edges[i]] = new_edges[i]
            
        for i in range(len(self.faces)):
            o2n[self.faces[i]] = new_faces[i]
        
        # Set all the dcel pointers
        for vert in self.verts:
            o2n[vert].aDart = o2n[vert.aDart]
        
        for dart in self.darts:
            o2n[dart].edge = o2n[dart.edge]
            o2n[dart].origin = o2n[dart.origin]
            o2n[dart].face = o2n[dart.face]
            o2n[dart].prev = o2n[dart.prev]
            o2n[dart].next = o2n[dart.next]
            o2n[dart].twin = o2n[dart.twin]
        
        for edge in self.edges:
            o2n[edge].aDart = o2n[edge.aDart]
        
        for face in self.faces:
            o2n[face].aDart = o2n[face.aDart]
        
        if self.outerFace != None:
            new_dcel.outerFace = o2n[self.outerFace]
        
        return new_dcel
    
# END DCEL

class Vertex:
    
    def __init__(self, dcel, aDart = None, data = None):
        self.dcel = dcel
        self.dcel.verts.append(self)
        self.aDart = aDart
        self.data  = data
        if data == None:
            raise Exception("Just set a None data vertex")
    
    def edges(self):
        return [dart.edge for dart in self.outDarts()]
    
    def degree(self):
        return len(self.outDarts())
    
    def outDarts(self):
        # ERMERGERD Why do I have to eliminate tail recursion myself!!!
        # The only reason python is not the worst language is because
        # PHP exists. My kotlin code is beautiful.
        darts = []
        curr = self.aDart
        if self.aDart == None:
            raise MalformedDCELException("Vertex.aDart is None")
        # Even worse there is no do-while loop. _sigh_
        i = 0
        while True:
            darts.append(curr)
            curr = curr.prev.twin
            if i > len(self.dcel.darts):
                raise MalformedDCELException("outDarts() collected more darts than should exist")
            i += 1
            if curr == self.aDart:
                break # That's a do-while folks...
        return darts
                
    def inDarts(self):
        # ERMERGERD Why do I have to eliminate tail recursion myself!!!
        # The only reason python is not the worst language is because
        # PHP exists. My kotlin code is beautiful.
        darts = []
        curr = self.aDart.twin
        # Even worse there is no do-while loop. _sigh_
        i = 0
        while True:
            darts.append(curr)
            curr = curr.twin.prev
            if i > len(self.dcel.darts):
                raise MalformedDCELException("inDarts() collected more darts than should exist")
            i += 1
            if curr == self.aDart.twin:
                break # That's a do-while folks...
        return darts

    def neighbors(self):
        return [dart.origin for dart in self.inDarts()]
    
    def faces(self):
        return [dart.face for dart in self.outDarts()]
    
    # Removes a vertex
    # WARNING: NOT THOROUGHLY TESTED, MAY CONTAIN BUGS
    # Almost certainly doesn't work with degree 2 vertices
    # I think it will work if all faces incident to the vertex have
    # degree 3. 
    def remove(self, newFaceData = None):
        indarts = self.inDarts()
        outdarts = [dart.next for dart in indarts]
        curr_edges = self.edges()
        curr_faces = self.faces()
        deg = len(indarts)
        
        if deg <= 2:
            print(f"WARNING: degree is ${deg} <= 2. This is almost certainly going to result in errors.")
        
        chains = [outdarts[i].dartsAlongFaceBetween(indarts[i])
                  for i in range(len(indarts))]
        
        # Create a new face to replace the old one
        newFace = Face(self.dcel, chains[0][0], newFaceData)
        
        # Connect up all the chains and set their face to the new face
        for cIdx in range(len(chains)):
            chains[cIdx][-1].makeNext(chains[(cIdx + 1) % len(chains)][0])
            for dart in chains[cIdx]:
                dart.face = newFace
        
        # Now remove everything
        self.dcel.verts.remove(self)
        for dart in indarts:
            if dart == dart.origin.aDart:
                dart.origin.aDart = dart.prev.twin
            self.dcel.darts.remove(dart)
        for dart in outdarts:
            self.dcel.darts.remove(dart)
        for edge in curr_edges:
            self.dcel.edges.remove(edge)
        for face in curr_faces:
            self.dcel.faces.remove(face)
        
        return newFace
    
# END Vertex

class Dart:
    
    def __init__(self, 
                 dcel, 
                 edge   = None, 
                 origin = None, 
                 face   = None,
                 prev   = None,
                 next   = None,
                 twin   = None, 
                 data   = None):
        
        self.dcel = dcel
        self.dcel.darts.append(self)
        
        self.edge   = edge
        self.origin = origin
        self.face   = face
        self.prev   = prev
        self.next   = next
        self.twin   = twin
        self.data   = data
        
        if self.edge != None:
            self.edge.aDart = self
        if self.origin != None:
            self.origin.aDart = self
        if self.face != None:
            self.face.aDart = self
        if self.prev != None:
            self.prev.next = self
        if self.next != None:
            self.next.prev = self
        if self.twin != None:
            self.twin.twin = self
      
    @property
    def dest(self):
        if self.twin == None:
            raise MalformedDCELException("Dart.twin is None")
        return self.twin.origin
    
    @property
    def pred(self): # predecessor vertex
        if self.prev == None:
            raise MalformedDCELException("Dart.prev is None")
        return self.prev.origin
    
    def makeNext(self, newNext):
        self.next = newNext
        newNext.prev = self
    
    def makeTwin(self, newTwin):
        self.twin = newTwin
        if not newTwin == None:
            newTwin.twin = self
    
    def makePrev(self, prev):
        self.prev = newPrev
        newPrev.next = self
        
    # Get the cycle of darts starting from self (follows .next)
    def cycle(self):
        cycle = []
        curr = self
        while True: # stupid do-while
            cycle.append(curr)
            curr = curr.next
            if self == curr: 
                break
        return cycle
    
    # Gets the darts starting with self up to stopDart (following
    # .next)
    def dartsAlongFaceTo(self, stopDart):
        cycle = []
        curr = self
        while True:
            cycle.append(curr)
            if curr == stopDart:
                break
            curr = curr.next
        return cycle
    
    def dartsAlongFaceBetween(self, stopDart):
        return self.dartsAlongFaceTo(stopDart)[1:-1]
    
    def reverse_cycle(self):
        return reversed(self.cycle())
    
    # Introduces a zero area face between this dart and its twin.
    # The new edge data is given by eData and the new face's data
    # is given by fData.
    # The new edge data is used for the twin's new edge.
    def cut(self, eData, fData):
        # TODO
        raise NotImplementedError("cut not yet implemented, sorry.")
    
    # Splits this dart (and twin) by the introduction of a vertex. The new vertex
    # data is given by vData, and the new edge data is given by eData.
    # The old dart is recycled to be the dart ccw before the new one.
    def split(vData, eData):
        # TODO
        raise NotImplementedError("split not yet implemented, sorry.")

# END Dart
        
class Edge:
    
    def __init__(self, dcel, aDart = None, data = None):
        
        self.dcel = dcel
        self.dcel.edges.append(self)
        
        self.aDart = aDart
        self.data  = data
        
    # Cuts this edge into two by introducing a zero-area face. 
    # The new edge's data is set to the eData parameter and 
    # the new face is set to the fData parameter. 
    #
    # Note that this is just a convenience wrapper for the same function
    # defined on the edge's dart. 
    def cut(self, eData, fData):
        self.aDart.cut(eData, fData)
    
    #Splits this edge by the introduction of a vertex. The new vertex
    # data is given by vData, and the new edge data is given by eData.
    #
    # Note that this is just a convenience wrapper for the same function
    # defined on this edge's dart.
    def split(self, vData, eData):
        self.aDart.split(vData, eData)

# END Edge

class Face:
    
    def __init__(self, dcel, aDart = None, data = None):
        
        self.dcel = dcel
        self.dcel.faces.append(self)
        
        self.aDart = aDart
        self.data  = data
    
    def darts(self):
        if (self.aDart == None):
            raise MalformedDCELException("Face.aDart is None")
        return self.aDart.cycle()
    
    def vertices(self):
        return [dart.origin for dart in self.darts()]

# END Face

class MalformedDCELException(Exception):
    pass

# END MalformedDCELException
