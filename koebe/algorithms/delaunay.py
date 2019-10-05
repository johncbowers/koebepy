def delaunay(points):
    from koebe.datastructures.dcel import DCEL, Vertex, Dart, Edge, Face
    from scipy.spatial import Delaunay

    tri = Delaunay([[p.x, p.y] for p in points])
    triDcel = DCEL()
    triDcel.delaunay = tri

    for p in points:
        Vertex(dcel = triDcel, data = p)

    dartMap = dict()

    for simplex in tri.simplices:
        i, j, k = simplex

        face = Face(dcel = triDcel)

        dartij = Dart(
            dcel   = triDcel, 
            origin = triDcel.verts[i], 
            face   = face, 
            data   = (i, j)
        )
        dartjk = Dart(
            dcel   = triDcel, 
            origin = triDcel.verts[j],
            face   = face, 
            data   = (j, k)
        )
        dartki = Dart(
            dcel   = triDcel, 
            origin = triDcel.verts[k],
            face   = face, 
            data   = (k, i)
        )

        dartij.makeNext(dartjk)
        dartjk.makeNext(dartki)
        dartki.makeNext(dartij)

        dartMap[(i,j)] = dartij
        dartMap[(j,k)] = dartjk
        dartMap[(k,i)] = dartki

    for dart in triDcel.darts:
        if dart.edge == None:
            i, j = dart.data
            if (j, i) in dartMap:
                twin = dartMap[(j, i)]
                edge = Edge(dcel = triDcel, aDart = dart)
                twin.edge = edge
                dart.makeTwin(twin)
    
    triDcel.outerFace = Face(dcel = triDcel)
    
    boundaryDarts = [dart for dart in triDcel.darts
                     if dart.twin == None]
    
    bdryOriginToDart = dict()
    
    for dart in boundaryDarts:
        twin = Dart(
            dcel = triDcel, 
            origin = triDcel.verts[dart.data[1]],
            face = triDcel.outerFace, 
            data = (dart.data[1], dart.data[0])
        )
        edge = Edge(dcel = triDcel, aDart = dart)
        twin.edge = edge
        dart.makeTwin(twin)
        bdryOriginToDart[twin.origin] = twin
    
    for dart in boundaryDarts:
        dart.twin.makeNext(bdryOriginToDart[dart.origin])
    
    return triDcel