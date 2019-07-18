# Doubly-connected edge list data structure

class DCEL:
    
    def __init__(self, outerFaceData = None):
        self.verts = []
        self.darts = []
        self.edges = []
        self.faces = []
        
        self.outerFace = None if outerFaceData == None else Face(data = outerFaceData)
        
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
      
    
class Dart:
    
    def __init__(self, 
                 dcel, 
                 edge   = None, 
                 origin = None, 
                 face   = None,
                 prev   = None,
                 next   = None,
                 twin   = None):
        
        self.dcel = dcel
        self.dcel.darts.append(self)
        
        self.edge   = edge
        self.origin = origin
        self.face   = face
        self.prev   = prev
        self.next   = next
        self.twin   = twin
        
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
        
    # Get the cycle of edges starting from self (follows .next)
    def cycle(self):
        cycle = []
        curr = self
        while True: # stupid do-while
            cycle.append(curr)
            curr = curr.next
            if self == curr: 
                break
        return cycle
                
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
    
class MalformedDCELException(Exception):
    pass