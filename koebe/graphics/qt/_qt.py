"""Internal helpers for optional Qt and VisPy dependencies."""

from __future__ import absolute_import

import sys


class QtBackendDependencyError(ImportError):
    """Raised when an optional Qt backend dependency is unavailable."""


class VispyDependencyError(ImportError):
    """Raised when an optional VisPy dependency is unavailable."""


QT_IMPORT_ERROR_MESSAGE = (
    "PySide6 is required to use koebe.graphics.qt. "
    "Install it with `pip install PySide6`."
)

VISPY_IMPORT_ERROR_MESSAGE = (
    "VisPy is required to use the GPU-backed koebe.graphics.qt renderers. "
    "Install it with `pip install vispy`."
)


def require_qt():
    """Return the Qt modules needed by the Qt graphics backend."""

    try:
        from PySide6 import QtCore, QtGui, QtWidgets
    except ImportError as exc:
        raise QtBackendDependencyError(QT_IMPORT_ERROR_MESSAGE) from exc

    return QtCore, QtGui, QtWidgets


def ensure_qapplication(argv=None):
    """Return an existing QApplication or create one if needed."""

    _QtCore, _QtGui, QtWidgets = require_qt()
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(argv or sys.argv or ["koebepy"])
    return app


def require_vispy():
    """Import and return the VisPy package used by renderer implementations."""

    try:
        import vispy
        vispy.use(app="pyside6")
    except ImportError as exc:
        raise VispyDependencyError(VISPY_IMPORT_ERROR_MESSAGE) from exc

    return vispy
