"""VisPy-backed renderer for ``Spherical2View``."""

from __future__ import absolute_import

import math

import numpy as np

from koebe.geometries.euclidean3 import PointE3, SegmentE3
from koebe.geometries.spherical2 import CPlaneS2, CircleArcS2, DiskS2, PointS2

from ..style import Fill, Marker, Stroke, Style
from .vispy_base import VispyRendererBase


class VispySpherical2Renderer(VispyRendererBase):
    """GPU-backed renderer for ``Spherical2View`` using VisPy."""

    DEFAULT_SPHERE_STYLE = Style(
        stroke=None,
        fill=Fill(color="#8ab4f8", alpha=0.16),
    )

    def __init__(self, scene=None, background_color="#f8f9fa", sphere_style=None):
        VispyRendererBase.__init__(self, scene=scene)

        self.require_vispy()
        from vispy import color, scene as vispy_scene

        self._color = color
        self._scene_module = vispy_scene
        self._canvas = vispy_scene.SceneCanvas(
            keys="interactive",
            show=False,
            bgcolor=background_color,
        )
        self._viewbox = self._canvas.central_widget.add_view()
        self._camera = vispy_scene.cameras.ArcballCamera(fov=45.0)
        self._viewbox.camera = self._camera
        self._sphere_style = sphere_style.copy() if sphere_style is not None else self.DEFAULT_SPHERE_STYLE.copy()
        self._visuals = []
        self._sphere_visual = None
        self._auto_fit_pending = True

        if hasattr(self._canvas.events, "mouse_double_click"):
            self._canvas.events.mouse_double_click.connect(self._on_mouse_double_click)

    @property
    def native_widget(self):
        return self._canvas.native

    def set_sphere_style(self, style):
        self._sphere_style = style.copy() if style is not None else self.DEFAULT_SPHERE_STYLE.copy()
        return self

    def sync(self, scene=None):
        VispyRendererBase.sync(self, scene=scene)
        self._clear_visuals()

        draw_order = 0
        if self._view is not None and getattr(self._view, "sphere_visible", False):
            self._add_reference_sphere(draw_order)
            draw_order += 1

        if self._scene is not None:
            for geometry, style in self._scene.items():
                if isinstance(geometry, PointS2):
                    self._add_point(geometry, style, draw_order)
                    draw_order += 1
                elif isinstance(geometry, PointE3):
                    self._add_point_e3(geometry, style, draw_order)
                    draw_order += 1
                elif isinstance(geometry, SegmentE3):
                    self._add_segment_e3(geometry, style, draw_order)
                    draw_order += 1
                elif isinstance(geometry, DiskS2):
                    self._add_disk(geometry, style, draw_order)
                    draw_order += 2
                elif isinstance(geometry, CPlaneS2):
                    self._add_disk(geometry.dualDiskS2, style, draw_order)
                    draw_order += 2
                elif isinstance(geometry, CircleArcS2):
                    self._add_arc(geometry, style, draw_order)
                    draw_order += 1

        if self._auto_fit_pending:
            self.fit()
            self._auto_fit_pending = False
        self.request_draw()
        return self

    def request_draw(self):
        self._canvas.update()

    def fit(self):
        self._camera.reset()
        self._camera.center = (0.0, 0.0, 0.0)
        self._camera.set_range(x=(-1.2, 1.2), y=(-1.2, 1.2), z=(-1.2, 1.2), margin=0.0)
        if hasattr(self._camera, "scale_factor"):
            self._camera.scale_factor = 2.6
        return self

    def _on_mouse_double_click(self, _event):
        self.fit()
        self.request_draw()

    def _clear_visuals(self):
        if self._sphere_visual is not None:
            self._sphere_visual.parent = None
            self._sphere_visual = None
        for visual in self._visuals:
            visual.parent = None
        self._visuals = []

    def _add_reference_sphere(self, draw_order):
        fill = self._sphere_style.fill if self._sphere_style.fill is not None else Fill(
            color="#8ab4f8",
            alpha=0.16,
        )
        visual = self._scene_module.visuals.Sphere(
            radius=1.0,
            rows=48,
            cols=96,
            method="latitude",
            color=self._rgba(fill.color, fill.alpha),
            edge_color=None,
            shading="smooth",
            parent=self._viewbox.scene,
        )
        visual.order = draw_order
        visual.set_gl_state(
            depth_test=True,
            cull_face=False,
            blend=True,
            blend_func=("src_alpha", "one_minus_src_alpha"),
        )
        self._sphere_visual = visual

    def _add_point(self, geometry, style, draw_order):
        marker = style.marker if style is not None and style.marker is not None else Marker()
        edge = style.stroke if style is not None and style.stroke is not None else Stroke(
            color=marker.color,
            width=0.0,
            alpha=marker.alpha,
        )
        visual = self._scene_module.visuals.Markers(parent=self._viewbox.scene)
        visual.set_data(
            pos=np.array([self._point_xyz(geometry)], dtype=np.float32),
            face_color=self._rgba(marker.color, marker.alpha),
            edge_color=self._rgba(edge.color, edge.alpha),
            edge_width=float(edge.width),
            size=float(marker.size),
            symbol=self._marker_symbol(marker.shape),
        )
        self._configure_overlay_visual(visual, draw_order)
        self._visuals.append(visual)

    def _add_point_e3(self, geometry, style, draw_order):
        marker = style.marker if style is not None and style.marker is not None else Marker()
        edge = style.stroke if style is not None and style.stroke is not None else Stroke(
            color=marker.color,
            width=0.0,
            alpha=marker.alpha,
        )
        visual = self._scene_module.visuals.Markers(parent=self._viewbox.scene)
        visual.set_data(
            pos=np.array([self._point_e3_xyz(geometry)], dtype=np.float32),
            face_color=self._rgba(marker.color, marker.alpha),
            edge_color=self._rgba(edge.color, edge.alpha),
            edge_width=float(edge.width),
            size=float(marker.size),
            symbol=self._marker_symbol(marker.shape),
        )
        self._configure_overlay_visual(visual, draw_order)
        self._visuals.append(visual)

    def _add_segment_e3(self, geometry, style, draw_order):
        stroke = style.stroke if style is not None and style.stroke is not None else Stroke()
        positions = np.array(
            [
                self._point_e3_xyz(geometry.source),
                self._point_e3_xyz(geometry.target),
            ],
            dtype=np.float32,
        )
        visual = self._scene_module.visuals.Line(
            pos=positions,
            color=self._rgba(stroke.color, stroke.alpha),
            width=float(stroke.width),
            method="gl",
            parent=self._viewbox.scene,
        )
        self._configure_overlay_visual(visual, draw_order)
        self._visuals.append(visual)

    def _add_disk(self, geometry, style, draw_order):
        stroke = style.stroke if style is not None and style.stroke is not None else Stroke()
        fill = style.fill if style is not None and style.fill is not None else Fill(
            color=stroke.color,
            alpha=0.0,
        )
        boundary = self._sample_disk_boundary(geometry)

        if fill.alpha > 0.0:
            mesh = self._scene_module.visuals.Mesh(
                vertices=self._disk_fill_vertices(geometry, boundary),
                faces=self._disk_fill_faces(boundary.shape[0] - 1),
                color=self._rgba(fill.color, fill.alpha),
                parent=self._viewbox.scene,
            )
            self._configure_surface_visual(mesh, draw_order)
            self._visuals.append(mesh)

        line = self._scene_module.visuals.Line(
            pos=boundary,
            color=self._rgba(stroke.color, stroke.alpha),
            width=float(stroke.width),
            method="gl",
            parent=self._viewbox.scene,
        )
        self._configure_overlay_visual(line, draw_order + 1)
        self._visuals.append(line)

    def _add_arc(self, geometry, style, draw_order):
        stroke = style.stroke if style is not None and style.stroke is not None else Stroke()
        line = self._scene_module.visuals.Line(
            pos=self._sample_arc(geometry),
            color=self._rgba(stroke.color, stroke.alpha),
            width=float(stroke.width),
            method="gl",
            parent=self._viewbox.scene,
        )
        self._configure_overlay_visual(line, draw_order)
        self._visuals.append(line)

    def _sample_disk_boundary(self, disk, samples=192):
        center = self._vector_xyz(disk.centerE3.toVectorE3())
        radius = float(disk.radiusE3)
        basis1 = self._vector_xyz(disk.normedBasis1.v)
        basis2 = self._vector_xyz(disk.normedBasis2.v)
        thetas = np.linspace(0.0, 2.0 * math.pi, samples, endpoint=True)
        boundary = []
        for theta in thetas:
            point = center + radius * (math.cos(theta) * basis1 + math.sin(theta) * basis2)
            boundary.append(self._normalize(point))
        return np.asarray(boundary, dtype=np.float32)

    def _sample_arc(self, arc, samples=96):
        center = self._vector_xyz(arc.centerE3.toVectorE3())
        radius = float(arc.radiusE3)
        basis1 = self._vector_xyz(arc.normedBasis1.v)
        basis2 = self._vector_xyz(arc.normedBasis2.v)
        source_angle = self._disk_angle(arc.source, center, basis1, basis2)
        target_angle = self._disk_angle(arc.target, center, basis1, basis2)
        delta = target_angle - source_angle
        while delta <= -math.pi:
            delta += 2.0 * math.pi
        while delta > math.pi:
            delta -= 2.0 * math.pi

        thetas = np.linspace(source_angle, source_angle + delta, samples, endpoint=True)
        points = []
        for theta in thetas:
            point = center + radius * (math.cos(theta) * basis1 + math.sin(theta) * basis2)
            points.append(self._normalize(point))
        return np.asarray(points, dtype=np.float32)

    def _disk_fill_vertices(self, disk, boundary):
        anchor = self._normalize(self._vector_xyz(disk.directionE3.v))
        return np.vstack([anchor, boundary[:-1]]).astype(np.float32)

    @staticmethod
    def _disk_fill_faces(segment_count):
        faces = []
        for index in range(segment_count):
            next_index = 1 if index == segment_count - 1 else index + 2
            faces.append([0, index + 1, next_index])
        return np.asarray(faces, dtype=np.uint32)

    @staticmethod
    def _configure_overlay_visual(visual, draw_order):
        visual.order = draw_order
        visual.set_gl_state(
            depth_test=False,
            cull_face=False,
            blend=True,
            blend_func=("src_alpha", "one_minus_src_alpha"),
        )

    @staticmethod
    def _configure_surface_visual(visual, draw_order):
        visual.order = draw_order
        visual.set_gl_state(
            depth_test=True,
            cull_face=False,
            blend=True,
            blend_func=("src_alpha", "one_minus_src_alpha"),
        )

    def _rgba(self, color_value, alpha):
        rgba = list(self._color.Color(color_value).rgba)
        rgba[3] = float(alpha)
        return tuple(rgba)

    @staticmethod
    def _point_xyz(point):
        return np.array([float(point.x), float(point.y), float(point.z)], dtype=np.float32)

    @staticmethod
    def _point_e3_xyz(point):
        return np.array([float(point.x), float(point.y), float(point.z)], dtype=np.float32)

    @staticmethod
    def _vector_xyz(vector):
        return np.array([float(vector.x), float(vector.y), float(vector.z)], dtype=np.float64)

    @staticmethod
    def _normalize(vector):
        norm = np.linalg.norm(vector)
        if math.isclose(norm, 0.0):
            return np.array([0.0, 0.0, 1.0], dtype=np.float64)
        return vector / norm

    @classmethod
    def _disk_angle(cls, point, center, basis1, basis2):
        delta = cls._point_xyz(point).astype(np.float64) - center
        x = float(np.dot(delta, basis1))
        y = float(np.dot(delta, basis2))
        return math.atan2(y, x)

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

