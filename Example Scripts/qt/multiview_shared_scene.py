"""Shared-scene Qt sketch with Euclidean and spherical views side by side."""

from __future__ import absolute_import

import math

from koebe.geometries.euclidean2 import CircleE2, PointE2, PolygonE2, SegmentE2
from koebe.geometries.spherical2 import CircleArcS2, DiskS2, PointS2
from koebe.graphics.qt import App, Scene, Window
from koebe.graphics.qt.style import Fill, Marker, Stroke, Style
from koebe.graphics.qt.views import Euclidean2View, Spherical2View


EUCLIDEAN_POINT_STYLE = Style(marker=Marker(color="#202124", size=9), stroke=Stroke(color="#ffffff", width=1.0))
EUCLIDEAN_SEGMENT_STYLE = Style(stroke=Stroke(color="#8ab4f8", width=2.5))
EUCLIDEAN_POLYGON_STYLE = Style(stroke=Stroke(color="#81c995", width=2.0), fill=Fill(color="#81c995", alpha=0.16))
SPHERICAL_POINT_STYLE = Style(marker=Marker(color="#202124", size=11), stroke=Stroke(color="#ffffff", width=1.0))
SPHERICAL_DISK_STYLE = Style(stroke=Stroke(color="#f28b82", width=2.2), fill=Fill(color="#f28b82", alpha=0.12))
SPHERICAL_ARC_STYLE = Style(stroke=Stroke(color="#ffcc00", width=2.4))


def normalize_point(x, y, z):
    norm = math.sqrt(x * x + y * y + z * z)
    return PointS2(x / norm, y / norm, z / norm)


def build_shared_scene():
    scene = Scene()

    # Euclidean geometry.
    a = PointE2(-1.6, -1.1)
    b = PointE2(1.7, -0.5)
    c = PointE2(0.25, 1.55)
    polygon = PolygonE2([a, b, c])
    circle = CircleE2(PointE2(0.0, 0.1), 1.0)
    edges = [SegmentE2(a, b), SegmentE2(b, c), SegmentE2(c, a)]

    scene.add(polygon, EUCLIDEAN_POLYGON_STYLE)
    scene.add(circle, Style(stroke=Stroke(color="#c58af9", width=2.0), fill=Fill(color="#c58af9", alpha=0.10)))
    scene.addAll(edges, style=EUCLIDEAN_SEGMENT_STYLE)
    scene.addAll([a, b, c], style=EUCLIDEAN_POINT_STYLE)

    # Spherical geometry.
    p = normalize_point(1.0, 0.0, 0.20)
    q = normalize_point(0.10, 1.0, 0.05)
    r = normalize_point(0.0, 0.30, 1.0)
    disk = DiskS2.throughThreePointS2(p, q, r)
    arc = CircleArcS2(p, q, disk)

    scene.add(disk, SPHERICAL_DISK_STYLE)
    scene.add(arc, SPHERICAL_ARC_STYLE)
    scene.addAll([p, q, r], style=SPHERICAL_POINT_STYLE)

    return {
        "scene": scene,
        "euclidean_circle": circle,
        "euclidean_polygon": polygon,
    }


def main():
    app = App()
    data = build_shared_scene()
    scene = data["scene"]

    window = Window("Qt Multiview - Shared Scene", layout="grid", size=(1440, 860))
    euclidean_view = Euclidean2View(scene, title="Euclidean 2")
    spherical_view = Spherical2View(scene, title="Spherical 2")
    window.add_view(euclidean_view, row=0, col=0)
    window.add_view(spherical_view, row=0, col=1)

    panel = window.add_panel("Shared controls", side="right", width=320)
    status = panel.add_text("status", "Both views share one Scene")

    state = {
        "circle": data["euclidean_circle"],
        "show_polygon_fill": True,
        "show_sphere": True,
    }

    def set_status(message):
        status.set_text(message)

    def update_circle(radius):
        old_circle = state["circle"]
        scene.remove(old_circle)
        new_circle = CircleE2(PointE2(0.0, 0.1), radius)
        state["circle"] = new_circle
        scene.add(new_circle, Style(stroke=Stroke(color="#c58af9", width=2.0), fill=Fill(color="#c58af9", alpha=0.10)))
        euclidean_view.fit()
        set_status("shared scene updated: circle radius = {:.2f}".format(radius))

    def toggle_polygon_fill(checked):
        state["show_polygon_fill"] = checked
        fill_alpha = 0.16 if checked else 0.0
        scene.set_style(
            data["euclidean_polygon"],
            EUCLIDEAN_POLYGON_STYLE.copy(fill=Fill(color="#81c995", alpha=fill_alpha)),
        )
        set_status("polygon fill {}".format("on" if checked else "off"))

    def toggle_sphere(checked):
        state["show_sphere"] = checked
        spherical_view.show_sphere() if checked else spherical_view.hide_sphere()
        set_status("sphere {}".format("shown" if checked else "hidden"))

    panel.add_slider("circle radius", min=0.35, max=2.4, value=1.0, step=0.05, on_change=update_circle)
    panel.add_checkbox("Show polygon fill", checked=True, on_change=toggle_polygon_fill)
    panel.add_checkbox("Show sphere", checked=True, on_change=toggle_sphere)
    panel.add_button("Fit both views", on_click=lambda: (euclidean_view.fit(), spherical_view.fit()))

    euclidean_view.fit()
    spherical_view.fit()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
