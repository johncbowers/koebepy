"""Euclidean 2D Qt view backed by VisPy."""

from __future__ import absolute_import

from koebe.geometries.euclidean2 import CircleE2, LineE2, PointE2, PolygonE2, SegmentE2

from ..renderers import VispyEuclidean2Renderer
from .base import BaseView


class Euclidean2View(BaseView):
    """Interactive Euclidean 2D view with panning and zooming."""

    SUPPORTED_GEOMETRY_TYPES = (PointE2, SegmentE2, CircleE2, PolygonE2, LineE2)

    def __init__(self, scene=None, title="Euclidean 2", background_color="#f8f9fa"):
        BaseView.__init__(self, scene=scene, title=title)
        self.attach_renderer(
            VispyEuclidean2Renderer(scene=scene, background_color=background_color)
        )
        self.request_redraw()

    def supports(self, geometry):
        return isinstance(geometry, self.SUPPORTED_GEOMETRY_TYPES)
