"""Basic Qt sketch demonstrating the new Spherical2View backend."""

from __future__ import absolute_import

import math

from koebe.geometries.spherical2 import CPlaneS2, CircleArcS2, DiskS2, PointS2
from koebe.graphics.qt import App, Scene, Window
from koebe.graphics.qt.style import Fill, Marker, Stroke, Style
from koebe.graphics.qt.views import Spherical2View


BACKGROUND_COLOR = "#f8f9fa"
POINT_STYLE = Style(marker=Marker(color="#202124", size=10), stroke=Stroke(color="#ffffff", width=1.0))
HIGHLIGHT_STYLE = Style(marker=Marker(color="#f29900", size=13), stroke=Stroke(color="#ffffff", width=1.2))
DISK_STYLE = Style(
    stroke=Stroke(color="#f28b82", width=2.5),
    fill=Fill(color="#f28b82", alpha=0.12),
)
DISK_OUTLINE_STYLE = DISK_STYLE.copy(fill=Fill(color="#f28b82", alpha=0.0))
ARC_STYLE = Style(stroke=Stroke(color="#81c995", width=2.5))
PLANE_STYLE = Style(stroke=Stroke(color="#8ab4f8", width=1.8))


def normalize_point(x, y, z):
    length = math.sqrt(x * x + y * y + z * z)
    return PointS2(x / length, y / length, z / length)


def build_geometry():
    a = normalize_point(1.0, 0.0, 0.25)
    b = normalize_point(0.15, 1.0, 0.10)
    c = normalize_point(0.0, 0.25, 1.0)
    d = normalize_point(-0.85, 0.30, 0.45)

    disk = DiskS2.throughThreePointS2(a, b, c)
    arc = CircleArcS2(a, b, disk)
    aux1 = DiskS2(1.0, 0.0, 0.0, 0.25)
    aux2 = DiskS2(0.0, 1.0, 0.0, 0.25)
    cplane = CPlaneS2.throughThreeDiskS2(disk, aux1, aux2)

    return {
        "points": [a, b, c, d],
        "disk": disk,
        "arc": arc,
        "cplane": cplane,
        "highlight": d,
    }


def populate_scene(scene, geometry, disk_style):
    scene.clear()
    scene.add(geometry["disk"], disk_style)
    scene.add(geometry["arc"], ARC_STYLE)
    scene.add(geometry["cplane"], PLANE_STYLE)
    scene.addAll(geometry["points"], style=POINT_STYLE)
    scene.set_style(geometry["highlight"], HIGHLIGHT_STYLE)


def main():
    app = App()
    scene = Scene()
    geometry = build_geometry()
    populate_scene(scene, geometry, DISK_STYLE)

    window = Window("Spherical2View Test Sketch", layout="grid", size=(1280, 840))
    view = Spherical2View(scene, background_color=BACKGROUND_COLOR)
    window.add_view(view, row=0, col=0)

    panel = window.add_panel(title="Controls", side="right", width=320)
    status = panel.add_text("status", "Ready")

    state = {
        "sphere_visible": True,
        "disk_fill_visible": True,
    }

    def update_status(message):
        status.set_text(message)

    def set_sphere_visible(checked):
        state["sphere_visible"] = checked
        if checked:
            view.show_sphere()
        else:
            view.hide_sphere()
        update_status("sphere {}".format("shown" if checked else "hidden"))

    def set_disk_fill_visible(checked):
        state["disk_fill_visible"] = checked
        scene.set_style(geometry["disk"], DISK_STYLE if checked else DISK_OUTLINE_STYLE)
        update_status("disk fill {}".format("on" if checked else "off"))

    def reset_scene():
        set_sphere_visible(True)
        set_disk_fill_visible(True)
        view.fit()
        update_status("reset")

    panel.add_checkbox("Show sphere", checked=True, on_change=set_sphere_visible)
    panel.add_checkbox("Show disk fill", checked=True, on_change=set_disk_fill_visible)
    panel.add_button("Fit view", on_click=view.fit)
    panel.add_button("Reset", on_click=reset_scene)

    view.fit()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
