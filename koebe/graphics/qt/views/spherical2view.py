"""Spherical Qt view backed by VisPy."""

from __future__ import absolute_import

from koebe.geometries.euclidean3 import PointE3, SegmentE3
from koebe.geometries.spherical2 import CPlaneS2, CircleArcS2, DiskS2, PointS2

from ..renderers import VispySpherical2Renderer
from ..style import Fill, Stroke, Style
from .base import BaseView


class Spherical2View(BaseView):
    """Interactive spherical view with a quaternion-based trackball camera."""

    SUPPORTED_GEOMETRY_TYPES = (PointS2, DiskS2, CPlaneS2, CircleArcS2, PointE3, SegmentE3)

    DEFAULT_SPHERE_STYLE = Style(
        stroke=None,
        fill=Fill(color="#8ab4f8", alpha=0.16),
    )

    def __init__(
        self,
        scene=None,
        title="Spherical 2",
        show_sphere=True,
        background_color="#f8f9fa",
        sphere_style=None,
    ):
        self._sphere_visible = bool(show_sphere)
        self._sphere_style = sphere_style.copy() if sphere_style is not None else self.DEFAULT_SPHERE_STYLE.copy()
        BaseView.__init__(self, scene=scene, title=title)
        self.attach_renderer(
            VispySpherical2Renderer(
                scene=scene,
                background_color=background_color,
                sphere_style=self._sphere_style,
            )
        )
        self.request_redraw()

    @property
    def sphere_visible(self):
        return self._sphere_visible

    @property
    def sphere_style(self):
        return self._sphere_style

    def show_sphere(self):
        self._sphere_visible = True
        self.request_redraw()
        return self

    def hide_sphere(self):
        self._sphere_visible = False
        self.request_redraw()
        return self

    def toggle_sphere(self):
        self._sphere_visible = not self._sphere_visible
        self.request_redraw()
        return self

    def set_sphere_style(self, style):
        self._sphere_style = style.copy() if style is not None else self.DEFAULT_SPHERE_STYLE.copy()
        if self._renderer is not None and hasattr(self._renderer, "set_sphere_style"):
            self._renderer.set_sphere_style(self._sphere_style)
        self.request_redraw()
        return self

    def supports(self, geometry):
        return isinstance(geometry, self.SUPPORTED_GEOMETRY_TYPES)
