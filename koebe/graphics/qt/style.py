"""Display-only style primitives for the Qt graphics backend."""

from __future__ import absolute_import


class Stroke(object):
    """Line style for drawable geometry."""

    def __init__(self, color="#202124", width=1.0, alpha=1.0, dash=None):
        self.color = color
        self.width = width
        self.alpha = alpha
        self.dash = dash

    def copy(self, **updates):
        data = {
            "color": self.color,
            "width": self.width,
            "alpha": self.alpha,
            "dash": self.dash,
        }
        data.update(updates)
        return Stroke(**data)


class Fill(object):
    """Fill style for drawable geometry."""

    def __init__(self, color="#5f6368", alpha=1.0):
        self.color = color
        self.alpha = alpha

    def copy(self, **updates):
        data = {
            "color": self.color,
            "alpha": self.alpha,
        }
        data.update(updates)
        return Fill(**data)


class Marker(object):
    """Point/marker style for drawable geometry."""

    def __init__(self, color="#202124", size=6.0, shape="disk", alpha=1.0):
        self.color = color
        self.size = size
        self.shape = shape
        self.alpha = alpha

    def copy(self, **updates):
        data = {
            "color": self.color,
            "size": self.size,
            "shape": self.shape,
            "alpha": self.alpha,
        }
        data.update(updates)
        return Marker(**data)


class Style(object):
    """Aggregated display style attached to one geometry object in a scene."""

    def __init__(self, stroke=None, fill=None, marker=None):
        self.stroke = stroke
        self.fill = fill
        self.marker = marker

    def copy(self, **updates):
        data = {
            "stroke": self.stroke,
            "fill": self.fill,
            "marker": self.marker,
        }
        data.update(updates)
        return Style(**data)

    def __repr__(self):
        return "Style(stroke={!r}, fill={!r}, marker={!r})".format(
            self.stroke,
            self.fill,
            self.marker,
        )
