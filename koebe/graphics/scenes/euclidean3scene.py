from .spherical2scene import makeStyle as _makeStyle
from .spherical2scene import DefaultStyles as _DefaultStyles
from .spherical2scene import S2Scene as _S2Scene

makeStyle = _makeStyle
DefaultStyles = _DefaultStyles

class E3Scene(_S2Scene):
    """A Scene for 3D Euclidean space."""
    def __init__(self, width=500, height=500, title=None, show_sphere=False, show_light_cone=False):
        super().__init__(width=width, height=height, title=title, show_sphere=show_sphere, show_light_cone=show_light_cone)