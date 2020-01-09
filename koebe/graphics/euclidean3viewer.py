from .spherical2viewer import makeStyle as _makeStyle
from .spherical2viewer import DefaultStyles as _DefaultStyles
from .spherical2viewer import S2Viewer as _S2Viewer
from .spherical2viewer import S2Sketch as _S2Sketch

class E3Viewer(_S2Viewer):
    """A Viewer for 3D Euclidean space."""
    def __init__(self, width=500, height=500):
        super().__init__(width = width, height = height)
        self.toggleSphere()

