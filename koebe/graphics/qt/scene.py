"""Scene model for the Qt graphics backend."""

from __future__ import absolute_import

from collections import OrderedDict

from .style import Style


class SceneChangeEvent(object):
    """Description of a scene mutation."""

    def __init__(self, kind, geometries):
        self.kind = kind
        self.geometries = tuple(geometries)


class Scene(object):
    """Identity-based mapping from geometry objects to display styles."""

    def __init__(self):
        self._entries = OrderedDict()
        self._listeners = []
        self._dirty = False

    def __len__(self):
        return len(self._entries)

    def __contains__(self, geometry):
        return id(geometry) in self._entries

    @property
    def dirty(self):
        return self._dirty

    def add(self, geometry, style=None):
        """Add one geometry object to the scene or replace its style."""

        event_kind = "updated" if geometry in self else "added"
        self._entries[id(geometry)] = (geometry, style if style is not None else Style())
        self._mark_dirty()
        self._notify(SceneChangeEvent(event_kind, [geometry]))
        return geometry

    def addAll(self, items, style=None):
        """Bulk-add geometry objects or (geometry, style) pairs."""

        items = list(items)
        if not items:
            return []

        inserted = []
        pair_mode = self._is_pair_sequence(items)

        if pair_mode and style is not None:
            raise ValueError("scene.addAll(...) cannot combine tuple pairs with a shared style")

        if pair_mode:
            for geometry, item_style in items:
                inserted.append(self._add_without_notify(geometry, item_style))
        else:
            for geometry in items:
                inserted.append(self._add_without_notify(geometry, style))

        self._mark_dirty()
        self._notify(SceneChangeEvent("bulk-added", inserted))
        return inserted

    def set_style(self, geometry, style):
        """Update the style of an existing geometry object."""

        key = id(geometry)
        if key not in self._entries:
            raise KeyError("Geometry object is not present in this scene")

        self._entries[key] = (geometry, style if style is not None else Style())
        self._mark_dirty()
        self._notify(SceneChangeEvent("style-updated", [geometry]))
        return style

    def remove(self, geometry):
        """Remove a geometry object from the scene if present."""

        key = id(geometry)
        entry = self._entries.pop(key, None)
        if entry is None:
            return False

        self._mark_dirty()
        self._notify(SceneChangeEvent("removed", [geometry]))
        return True

    def clear(self):
        """Remove every geometry object from the scene."""

        if not self._entries:
            return

        removed = [geometry for geometry, _style in self._entries.values()]
        self._entries.clear()
        self._mark_dirty()
        self._notify(SceneChangeEvent("cleared", removed))

    def style_of(self, geometry):
        """Return the style currently attached to a geometry object."""

        entry = self._entries.get(id(geometry))
        return None if entry is None else entry[1]

    def items(self):
        """Iterate over ``(geometry, style)`` pairs in insertion order."""

        for geometry, style in self._entries.values():
            yield geometry, style

    def geometries(self):
        for geometry, _style in self._entries.values():
            yield geometry

    def styles(self):
        for _geometry, style in self._entries.values():
            yield style

    def subscribe(self, callback):
        """Register a listener for scene changes."""

        if callback not in self._listeners:
            self._listeners.append(callback)
        return callback

    def unsubscribe(self, callback):
        """Remove a previously registered scene listener."""

        if callback in self._listeners:
            self._listeners.remove(callback)

    def clear_dirty(self):
        self._dirty = False

    def _add_without_notify(self, geometry, style=None):
        self._entries[id(geometry)] = (geometry, style if style is not None else Style())
        return geometry

    @staticmethod
    def _is_pair_sequence(items):
        first = items[0]
        return isinstance(first, tuple) and len(first) == 2

    def _mark_dirty(self):
        self._dirty = True

    def _notify(self, event):
        listeners = list(self._listeners)
        for callback in listeners:
            callback(event)
