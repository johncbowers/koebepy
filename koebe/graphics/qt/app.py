"""Application wrapper for the Qt graphics backend."""

from __future__ import absolute_import

import sys

from ._qt import ensure_qapplication, require_qt


class App(object):
    """Small wrapper around ``QApplication`` for KoebePy sketches."""

    _current = None

    def __init__(self):
        QtCore, _QtGui, QtWidgets = require_qt()
        self._qt_app = ensure_qapplication(sys.argv or ["koebepy"])
        self._windows = []
        self._frame_callbacks = []
        self._frame_timer = None
        self._QtCore = QtCore
        App._current = self

    @classmethod
    def current(cls):
        return cls._current

    @property
    def qt_app(self):
        return self._qt_app

    def add_window(self, window):
        if window not in self._windows:
            self._windows.append(window)
            window._attach_app(self)
        return window

    def create_window(self, title="KoebePy", layout="grid", size=(1024, 768)):
        from .window import Window

        window = Window(title=title, layout=layout, size=size)
        return self.add_window(window)

    def add_frame_callback(self, callback, interval_ms=16):
        if callback not in self._frame_callbacks:
            self._frame_callbacks.append(callback)
        self._ensure_frame_timer(interval_ms)
        return callback

    def on_frame(self, func=None, interval_ms=16):
        if func is None:
            def decorator(callback):
                self.add_frame_callback(callback, interval_ms=interval_ms)
                return callback
            return decorator

        self.add_frame_callback(func, interval_ms=interval_ms)
        return func

    def run(self):
        for window in self._windows:
            window.show()
        return self._qt_app.exec()

    def _ensure_frame_timer(self, interval_ms):
        if self._frame_timer is None:
            self._frame_timer = self._QtCore.QTimer()
            self._frame_timer.timeout.connect(self._emit_frame)
        if not self._frame_timer.isActive():
            self._frame_timer.start(interval_ms)

    def _emit_frame(self):
        for callback in list(self._frame_callbacks):
            callback()
