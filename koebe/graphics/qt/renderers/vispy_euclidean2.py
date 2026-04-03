"""VisPy-backed renderer for ``Euclidean2View``."""

from __future__ import absolute_import

import math

import numpy as np

from koebe.geometries.euclidean2 import CircleE2, LineE2, PointE2, PolygonE2, SegmentE2

from ..style import Fill, Marker, Stroke
from .vispy_base import VispyRendererBase


class VispyEuclidean2Renderer(VispyRendererBase):
    """GPU-backed renderer for ``Euclidean2View`` using VisPy."""

    def __init__(self, scene=None, background_color="#f8f9fa"):
        VispyRendererBase.__init__(self, scene=scene)

        vispy = self.require_vispy()
        from vispy import color, scene as vispy_scene

        self._color = color
        self._scene_module = vispy_scene
        self._canvas = vispy_scene.SceneCanvas(
            keys="interactive",
            show=False,
            bgcolor=background_color,
        )
        self._viewbox = self._canvas.central_widget.add_view()
        self._camera = vispy_scene.PanZoomCamera(aspect=1)
        self._camera.zoom_factor = 0.003
        self._viewbox.camera = self._camera
        self._visuals = []
        self._bounds = None
        self._auto_fit_pending = True

    @property
    def native_widget(self):
        return self._canvas.native

    def sync(self, scene=None):
        VispyRendererBase.sync(self, scene=scene)
        self._clear_visuals()
        self._bounds = None

        if self._scene is None:
            self.request_draw()
            return self

        bounds = _Bounds2D()
        draw_order = 0

        for geometry, style in self._scene.items():
            if isinstance(geometry, PointE2):
                self._add_point(geometry, style, draw_order)
                bounds.include_point(geometry)
            elif isinstance(geometry, SegmentE2):
                self._add_segment(geometry, style, draw_order)
                bounds.include_point(geometry.source)
                bounds.include_point(geometry.target)
            elif isinstance(geometry, CircleE2):
                self._add_circle(geometry, style, draw_order)
                bounds.include_circle(geometry)
            elif isinstance(geometry, PolygonE2):
                self._add_polygon(geometry, style, draw_order)
                bounds.include_polygon(geometry)
            elif isinstance(geometry, LineE2):
                self._add_line_segment(geometry, style, draw_order)
                bounds.include_point(geometry.p1)
                bounds.include_point(geometry.p2)
            draw_order += 1

        self._bounds = bounds.as_tuple()
        if self._auto_fit_pending:
            self.fit()
            self._auto_fit_pending = False
        self.request_draw()
        return self

    def request_draw(self):
        self._canvas.update()

    def fit(self):
        if self._bounds is None:
            self._camera.set_range(x=(-1.0, 1.0), y=(-1.0, 1.0), margin=0.05)
            return

        xmin, xmax, ymin, ymax = self._bounds
        width = xmax - xmin
        height = ymax - ymin

        if math.isclose(width, 0.0):
            xmin -= 0.5
            xmax += 0.5
        if math.isclose(height, 0.0):
            ymin -= 0.5
            ymax += 0.5

        self._camera.set_range(x=(xmin, xmax), y=(ymin, ymax), margin=0.05)

    def _clear_visuals(self):
        for visual in self._visuals:
            visual.parent = None
        self._visuals = []

    def _add_point(self, geometry, style, draw_order):
        marker = style.marker if style is not None and style.marker is not None else Marker()
        edge = style.stroke if style is not None and style.stroke is not None else Stroke(
            color=marker.color,
            width=0.0,
            alpha=marker.alpha,
        )
        visual = self._scene_module.visuals.Markers(parent=self._viewbox.scene)
        visual.set_data(
            pos=np.array([[float(geometry.x), float(geometry.y)]], dtype=np.float32),
            face_color=self._rgba(marker.color, marker.alpha),
            edge_color=self._rgba(edge.color, edge.alpha),
            edge_width=float(edge.width),
            size=float(marker.size),
            symbol=self._marker_symbol(marker.shape),
        )
        self._configure_visual(visual, draw_order)
        self._visuals.append(visual)

    def _add_segment(self, geometry, style, draw_order):
        stroke = style.stroke if style is not None and style.stroke is not None else Stroke()
        positions = np.array(
            [
                [float(geometry.source.x), float(geometry.source.y)],
                [float(geometry.target.x), float(geometry.target.y)],
            ],
            dtype=np.float32,
        )
        visual = self._scene_module.visuals.Line(
            pos=positions,
            color=self._rgba(stroke.color, stroke.alpha),
            width=float(stroke.width),
            method="agg",
            parent=self._viewbox.scene,
        )
        self._configure_visual(visual, draw_order)
        self._visuals.append(visual)

    def _add_line_segment(self, geometry, style, draw_order):
        self._add_segment(SegmentE2(geometry.p1, geometry.p2), style, draw_order)

    def _add_circle(self, geometry, style, draw_order):
        stroke = style.stroke if style is not None and style.stroke is not None else Stroke()
        fill = style.fill if style is not None and style.fill is not None else Fill(
            color=stroke.color,
            alpha=0.0,
        )
        visual = self._scene_module.visuals.Ellipse(
            center=(float(geometry.center.x), float(geometry.center.y)),
            radius=(float(geometry.radius), float(geometry.radius)),
            color=self._rgba(fill.color, fill.alpha),
            border_color=self._rgba(stroke.color, stroke.alpha),
            border_width=float(stroke.width),
            parent=self._viewbox.scene,
        )
        self._configure_visual(visual, draw_order)
        self._visuals.append(visual)

    def _add_polygon(self, geometry, style, draw_order):
        stroke = style.stroke if style is not None and style.stroke is not None else Stroke()
        fill = style.fill if style is not None and style.fill is not None else Fill(
            color=stroke.color,
            alpha=0.0,
        )
        positions = np.array(
            [[float(vertex.x), float(vertex.y)] for vertex in geometry.vertices],
            dtype=np.float32,
        )
        visual = self._scene_module.visuals.Polygon(
            pos=positions,
            color=self._rgba(fill.color, fill.alpha),
            border_color=self._rgba(stroke.color, stroke.alpha),
            border_width=float(stroke.width),
            parent=self._viewbox.scene,
        )
        self._configure_visual(visual, draw_order)
        self._visuals.append(visual)

    @staticmethod
    def _configure_visual(visual, draw_order):
        visual.order = draw_order
        visual.set_gl_state(
            depth_test=False,
            cull_face=False,
            blend=True,
            blend_func=("src_alpha", "one_minus_src_alpha"),
        )

    def _rgba(self, color_value, alpha):
        rgba = list(self._color.Color(color_value).rgba)
        rgba[3] = float(alpha)
        return tuple(rgba)

    @staticmethod
    def _marker_symbol(shape):
        symbol_map = {
            "disk": "disc",
            "circle": "o",
            "plus": "+",
            "disc": "disc",
            "square": "square",
            "triangle_up": "triangle_up",
            "triangle_down": "triangle_down",
            "diamond": "diamond",
            "cross": "cross",
            "star": "star",
        }
        return symbol_map.get(shape, shape)


class _Bounds2D(object):
    """Mutable 2D bounds accumulator."""

    def __init__(self):
        self._xmin = None
        self._xmax = None
        self._ymin = None
        self._ymax = None

    def include_point(self, point):
        self._include_xy(float(point.x), float(point.y))

    def include_circle(self, circle):
        r = float(circle.radius)
        self._include_xy(float(circle.center.x) - r, float(circle.center.y) - r)
        self._include_xy(float(circle.center.x) + r, float(circle.center.y) + r)

    def include_polygon(self, polygon):
        for vertex in polygon.vertices:
            self.include_point(vertex)

    def as_tuple(self):
        if self._xmin is None:
            return None
        return self._xmin, self._xmax, self._ymin, self._ymax

    def _include_xy(self, x, y):
        self._xmin = x if self._xmin is None else min(self._xmin, x)
        self._xmax = x if self._xmax is None else max(self._xmax, x)
        self._ymin = y if self._ymin is None else min(self._ymin, y)
        self._ymax = y if self._ymax is None else max(self._ymax, y)
