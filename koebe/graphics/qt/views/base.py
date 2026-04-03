"""Base view scaffolding for Qt graphics views."""

from __future__ import absolute_import

from .._qt import ensure_qapplication, require_qt


class BaseView(object):
    """Minimal view wrapper shared by future concrete view implementations."""

    def __init__(self, scene=None, title=None):
        ensure_qapplication()
        QtCore, _QtGui, QtWidgets = require_qt()
        self._QtWidgets = QtWidgets
        self._scene = None
        self._title = title or self.__class__.__name__
        self._renderer = None
        self._window = None
        self._dirty = False

        self._widget = QtWidgets.QFrame()
        self._widget.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._widget.setFrameShadow(QtWidgets.QFrame.Sunken)
        self._layout = QtWidgets.QVBoxLayout(self._widget)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._placeholder = QtWidgets.QLabel(self._title, self._widget)
        self._placeholder.setAlignment(QtCore.Qt.AlignCenter)
        self._layout.addWidget(self._placeholder, 1)

        if scene is not None:
            self.set_scene(scene)

    @property
    def widget(self):
        return self._widget

    @property
    def scene(self):
        return self._scene

    @property
    def title(self):
        return self._title

    def set_scene(self, scene):
        if scene is self._scene:
            return self
        if self._scene is not None:
            self._scene.unsubscribe(self._handle_scene_change)
        self._scene = scene
        if self._scene is not None:
            self._scene.subscribe(self._handle_scene_change)
        self.request_redraw()
        return self

    def attach_window(self, window):
        self._window = window
        return self

    def attach_renderer(self, renderer):
        self._renderer = renderer
        renderer.attach_to_view(self)
        if renderer.native_widget is not None:
            self.set_content_widget(renderer.native_widget)
        renderer.sync(self._scene)
        self.request_redraw()
        return renderer

    def set_content_widget(self, widget):
        while self._layout.count():
            item = self._layout.takeAt(0)
            child = item.widget()
            if child is not None:
                child.setParent(None)
        self._layout.addWidget(widget, 1)
        return widget

    def supports(self, geometry):
        return False

    def fit(self):
        if self._renderer is not None:
            return self._renderer.fit()
        return None

    def request_redraw(self):
        self._dirty = True
        if self._renderer is not None:
            self._renderer.sync(self._scene)
            self._renderer.request_draw()
        else:
            self._update_placeholder_text()
        return self

    def _handle_scene_change(self, _event):
        self.request_redraw()

    def _update_placeholder_text(self):
        if self._scene is None:
            text = self._title
        else:
            text = "{}\n{} object(s) in scene".format(self._title, len(self._scene))
        self._placeholder.setText(text)
