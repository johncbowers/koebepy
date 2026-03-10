from collections import deque, defaultdict
from typing import Callable, Dict, Optional

from koebe.datastructures.dcel import DCEL, Vertex
from koebe.geometries.euclidean2 import CircleE2, PointE2, PolygonE2, SegmentE2
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle


def _default_point_of(data):
    """Extract a PointE2 from common vertex payloads."""
    if data is None:
        return None
    if isinstance(data, PointE2):
        return data
    if hasattr(data, "toPointE2"):
        return data.toPointE2()
    if hasattr(data, "center") and isinstance(data.center, PointE2):
        return data.center
    return None


def _default_vertex_drawable(data):
    """Return a drawable 2D object for a vertex payload, if possible."""
    if data is None:
        return None
    if isinstance(data, CircleE2):
        return data
    if isinstance(data, PointE2):
        return data
    if hasattr(data, "center") and hasattr(data, "radius"):
        center = data.center
        if isinstance(center, PointE2):
            return CircleE2(center, data.radius)
    if hasattr(data, "toPointE2"):
        return data.toPointE2()
    return None


def _scale_obj(obj, scale):
    """Scale a supported geometry object by a scalar."""
    if scale == 1.0:
        return obj
    if isinstance(obj, (PointE2, SegmentE2, CircleE2)):
        return scale * obj
    if isinstance(obj, PolygonE2):
        return PolygonE2([scale * v for v in obj.vertices])
    return obj


def _shift_point(point, shift):
    """Translate a PointE2 by subtracting the shift vector."""
    if shift is None:
        return point
    return PointE2(point.x - shift.x, point.y - shift.y)


def _shift_obj(obj, shift):
    """Translate a supported geometry object by subtracting shift."""
    if shift is None:
        return obj
    if isinstance(obj, PointE2):
        return _shift_point(obj, shift)
    if isinstance(obj, SegmentE2):
        return SegmentE2(_shift_point(obj.source, shift), _shift_point(obj.target, shift))
    if isinstance(obj, CircleE2):
        return CircleE2(_shift_point(obj.center, shift), obj.radius)
    if isinstance(obj, PolygonE2):
        return PolygonE2([_shift_point(v, shift) for v in obj.vertices])
    return obj


def _resolve_root(dcel: DCEL, root: Optional[Vertex], root_idx: Optional[int], parent_map):
    """Pick a root vertex from explicit root, index, parent map, or fallback."""
    if root is not None:
        return root
    if root_idx is not None and 0 <= root_idx < len(dcel.verts):
        return dcel.verts[root_idx]
    if parent_map is not None:
        for v, p in parent_map.items():
            if p is None:
                return v
    return dcel.verts[0] if dcel.verts else None


def _build_parent_map(dcel: DCEL, root: Optional[Vertex], parent_of):
    """Build a parent map from explicit parents or a BFS spanning tree."""
    if parent_of is not None:
        return parent_of

    parent_map = {}
    has_explicit_parent = False
    for v in dcel.verts:
        if hasattr(v, "parent") and v.parent is not None:
            parent_map[v] = v.parent
            has_explicit_parent = True

    if has_explicit_parent:
        return parent_map

    if not dcel.verts:
        return parent_map

    start = root or dcel.verts[0]
    queue = deque([start])
    visited = {start}
    parent_map[start] = None
    while queue:
        v = queue.popleft()
        for nb in v.neighbors():
            if nb in visited:
                continue
            visited.add(nb)
            parent_map[nb] = v
            queue.append(nb)

    return parent_map


def _tree_order(parent_map, root):
    """Return a BFS order list starting at the root using the parent map."""
    if root is None:
        return []
    children = {}
    for v, p in parent_map.items():
        if p is None:
            continue
        children.setdefault(p, []).append(v)
    order = []
    queue = deque([root])
    visited = {root}
    while queue:
        v = queue.popleft()
        order.append(v)
        for child in children.get(v, []):
            if child in visited:
                continue
            visited.add(child)
            queue.append(child)
    return order


def _depths_from_parent_map(parent_map, root):
    """Compute BFS depths for vertices in the parent map."""
    if root is None:
        return {}
    depths = {root: 0}
    queue = deque([root])
    children = {}
    for v, p in parent_map.items():
        if p is None:
            continue
        children.setdefault(p, []).append(v)
    while queue:
        v = queue.popleft()
        for child in children.get(v, []):
            if child in depths:
                continue
            depths[child] = depths[v] + 1
            queue.append(child)
    return depths


def scene_from_dcel_2d(
    dcel: DCEL,
    title: str = "2D View",
    width: int = 800,
    height: int = 800,
    scale: float = 1.0,
    pan_and_zoom: bool = True,
    show_faces: bool = False,
    show_edges: bool = True,
    show_vertices: bool = True,
    show_tree: bool = False,
    root: Optional[Vertex] = None,
    root_idx: Optional[int] = None,
    parent_of: Optional[Dict[Vertex, Optional[Vertex]]] = None,
    point_of: Optional[Callable] = None,
    vertex_style=None,
    edge_style=None,
    tree_style=None,
    face_style=None,
    root_style=None,
    root_at_origin: bool = False,
    order_from_root: bool = False,
):
    """Create an E2Scene from a DCEL with optional tree and root controls."""
    point_of = point_of or _default_point_of
    scene = E2Scene(title=title, width=width, height=height, scale=1.0, pan_and_zoom=pan_and_zoom)

    parent_map = None
    if show_tree or order_from_root:
        parent_map = _build_parent_map(dcel, root, parent_of)
    root = _resolve_root(dcel, root, root_idx, parent_map)
    if parent_map is None and (show_tree or order_from_root):
        parent_map = _build_parent_map(dcel, root, parent_of)

    shift = None
    if root_at_origin and root is not None:
        root_point = point_of(root.data)
        if root_point is not None:
            shift = root_point

    if show_faces:
        faces = [f for f in dcel.faces if f is not dcel.outerFace]
        if face_style is None:
            face_style = makeStyle(stroke="#000", strokeWeight=1, fill="#ccf")
        scene.addAll([(f, face_style) for f in faces])

    if show_edges:
        segments = []
        for e in dcel.edges:
            u, v = e.endPoints()
            pu = point_of(u.data)
            pv = point_of(v.data)
            if pu is None or pv is None:
                continue
            seg = SegmentE2(pu, pv)
            seg = _shift_obj(seg, shift)
            segments.append(_scale_obj(seg, scale))
        if edge_style is not None:
            if callable(edge_style):
                scene.addAll([(s, edge_style(s)) for s in segments])
            else:
                scene.addAll([(s, edge_style) for s in segments])
        else:
            scene.addAll(segments)

    if show_vertices:
        verts = []
        depths = _depths_from_parent_map(parent_map, root) if order_from_root else {}
        order = _tree_order(parent_map, root) if order_from_root else list(dcel.verts)
        seen = set(order)
        order += [v for v in dcel.verts if v not in seen]
        for v in order:
            drawable = _default_vertex_drawable(v.data)
            if drawable is None:
                continue
            drawable = _shift_obj(drawable, shift)
            verts.append((v, _scale_obj(drawable, scale)))
        if vertex_style is not None:
            if callable(vertex_style):
                scene.addAll([(obj, vertex_style(v, depths.get(v, 0))) for v, obj in verts])
            else:
                scene.addAll([(obj, vertex_style) for _, obj in verts])
        else:
            scene.addAll([obj for _, obj in verts])

        if root_style is not None and root is not None:
            for v, obj in verts:
                if v is root:
                    scene.addAll([(obj, root_style)])
                    break

    if show_tree:
        if tree_style is None:
            tree_style = makeStyle(stroke=(128, 128, 128), strokeWeight=1.0, fill=None)
        tree_segments = []
        for v, p in parent_map.items():
            if p is None:
                continue
            pv = point_of(v.data)
            pp = point_of(p.data)
            if pv is None or pp is None:
                continue
            seg = SegmentE2(pv, pp)
            seg = _shift_obj(seg, shift)
            tree_segments.append(_scale_obj(seg, scale))
        if callable(tree_style):
            scene.addAll([(s, tree_style(s)) for s in tree_segments])
        else:
            scene.addAll([(s, tree_style) for s in tree_segments])

    return scene


def display_dcel_2d(dcel: DCEL, viewer=None, run: bool = False, **scene_kwargs):
    """Build a DCEL scene and optionally add/run it in a viewer."""
    scene = scene_from_dcel_2d(dcel, **scene_kwargs)
    if viewer is not None:
        viewer.add_scene(scene)
        if run:
            viewer.run()
    return scene
