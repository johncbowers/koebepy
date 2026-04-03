"""Top-level window and layout helpers for the Qt graphics backend."""

from __future__ import absolute_import

from ._qt import ensure_qapplication, require_qt
from .app import App
from .controls import ControlPanel


class Window(object):
    """Qt window containing views and optional control panels."""

    VALID_PANEL_SIDES = ("left", "right", "top", "bottom")

    def __init__(self, title="KoebePy", layout="grid", size=(1024, 768)):
        ensure_qapplication()
        _QtCore, _QtGui, QtWidgets = require_qt()
        self._QtWidgets = QtWidgets
        self._layout_mode = layout
        self._app = None
        self._views = []
        self._panels = []

        self._widget = QtWidgets.QWidget()
        self._widget.setWindowTitle(title)
        if size is not None:
            self._widget.resize(*size)

        self._root_layout = QtWidgets.QVBoxLayout(self._widget)
        self._root_layout.setContentsMargins(6, 6, 6, 6)
        self._root_layout.setSpacing(6)

        self._top_widget, self._top_layout = self._make_container(QtWidgets.QHBoxLayout)
        self._center_widget = QtWidgets.QWidget(self._widget)
        self._center_layout = QtWidgets.QHBoxLayout(self._center_widget)
        self._center_layout.setContentsMargins(0, 0, 0, 0)
        self._center_layout.setSpacing(6)

        self._left_widget, self._left_layout = self._make_container(QtWidgets.QVBoxLayout)
        self._view_widget, self._view_layout = self._make_container(QtWidgets.QGridLayout)
        self._right_widget, self._right_layout = self._make_container(QtWidgets.QVBoxLayout)
        self._bottom_widget, self._bottom_layout = self._make_container(QtWidgets.QHBoxLayout)

        self._center_layout.addWidget(self._left_widget)
        self._center_layout.addWidget(self._view_widget, 1)
        self._center_layout.addWidget(self._right_widget)

        self._root_layout.addWidget(self._top_widget)
        self._root_layout.addWidget(self._center_widget, 1)
        self._root_layout.addWidget(self._bottom_widget)

        current_app = App.current()
        if current_app is not None:
            current_app.add_window(self)

    @property
    def widget(self):
        return self._widget

    def add_view(self, view, row=0, col=0, row_span=1, col_span=1):
        widget = self._coerce_widget(view)
        self._view_layout.addWidget(widget, row, col, row_span, col_span)
        self._views.append(view)
        if hasattr(view, "attach_window"):
            view.attach_window(self)
        return view

    def add_panel(self, title="", side="right", width=None):
        if side not in self.VALID_PANEL_SIDES:
            raise ValueError("Panel side must be one of {}".format(", ".join(self.VALID_PANEL_SIDES)))

        panel = ControlPanel(title=title, parent=self._widget, width=width)
        container_layout = {
            "left": self._left_layout,
            "right": self._right_layout,
            "top": self._top_layout,
            "bottom": self._bottom_layout,
        }[side]
        container_layout.addWidget(panel.widget)
        self._panels.append(panel)
        return panel

    def show(self):
        self._widget.show()
        return self

    def _attach_app(self, app):
        self._app = app

    def _make_container(self, layout_type):
        widget = self._QtWidgets.QWidget(self._widget)
        layout = layout_type(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        return widget, layout

    def _coerce_widget(self, view):
        widget = getattr(view, "widget", None)
        if callable(widget):
            return widget()
        if widget is not None:
            return widget
        return view
