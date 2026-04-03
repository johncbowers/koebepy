"""Base renderer scaffolding for future VisPy-backed views."""

from __future__ import absolute_import

from .._qt import require_vispy


class VispyRendererBase(object):
    """Minimal renderer base class used during Phase 1 scaffolding."""

    def __init__(self, scene=None):
        self._scene = scene
        self._view = None
        self._vispy = None

    @property
    def scene(self):
        return self._scene

    def attach_to_view(self, view):
        self._view = view
        return self

    @property
    def native_widget(self):
        return None

    def sync(self, scene=None):
        if scene is not None:
            self._scene = scene
        return self

    def request_draw(self):
        return None

    def fit(self):
        return None

    def require_vispy(self):
        if self._vispy is None:
            self._vispy = require_vispy()
        return self._vispy
