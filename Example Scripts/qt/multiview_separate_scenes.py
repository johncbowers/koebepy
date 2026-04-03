"""Two-view Qt sketch with a separate Scene for each view."""

from __future__ import absolute_import

import math

from koebe.geometries.euclidean2 import CircleE2, PointE2, PolygonE2, SegmentE2
from koebe.geometries.spherical2 import CircleArcS2, DiskS2, PointS2
from koebe.graphics.qt import App, Scene, Window
from koebe.graphics.qt.style import Fill, Marker, Stroke, Style
from koebe.graphics.qt.views import Euclidean2View, Spherical2View


EUCLIDEAN_POINT_STYLE = Style(marker=Marker(color="#202124", size=9), stroke=Stroke(color="#ffffff", width=1.0))
EUCLIDEAN_SEGMENT_STYLE = Style(stroke=Stroke(color="#8ab4f8", width=2.4))
EUCLIDEAN_POLYGON_STYLE = Style(stroke=Stroke(color="#81c995", width=2.0), fill=Fill(color="#81c995", alpha=0.16))
EUCLIDEAN_CIRCLE_STYLE = Style(stroke=Stroke(color="#f28b82", width=2.3), fill=Fill(color="#f28b82", alpha=0.10))
SPHERICAL_POINT_STYLE = Style(marker=Marker(color="#202124", size=11), stroke=Stroke(color="#ffffff", width=1.0))
SPHERICAL_DISK_STYLE = Style(stroke=Stroke(color="#c58af9", width=2.2), fill=Fill(color="#c58af9", alpha=0.12))
SPHERICAL_ARC_STYLE = Style(stroke=Stroke(color="#ffcc00", width=2.4))


def normalize_point(x, y, z):
    norm = math.sqrt(x * x + y * y + z * z)
    return PointS2(x / norm, y / norm, z / norm)


def build_euclidean_scene(radius=1.0):
    scene = Scene()
    a = PointE2(-1.4, -1.0)
    b = PointE2(1.65, -0.55)
    c = PointE2(0.15, 1.45)
    polygon = PolygonE2([a, b, c])
    circle = CircleE2(PointE2(0.1, 0.05), radius)

    scene.add(polygon, EUCLIDEAN_POLYGON_STYLE)
    scene.add(circle, EUCLIDEAN_CIRCLE_STYLE)
    scene.addAll([SegmentE2(a, b), SegmentE2(b, c), SegmentE2(c, a)], style=EUCLIDEAN_SEGMENT_STYLE)
    scene.addAll([a, b, c], style=EUCLIDEAN_POINT_STYLE)
    return {
        "scene": scene,
        "polygon": polygon,
        "circle": circle,
    }


def build_spherical_scene(include_arc=True):
    scene = Scene()
    p = normalize_point(1.0, 0.0, 0.15)
    q = normalize_point(0.0, 1.0, 0.20)
    r = normalize_point(0.2, 0.15, 1.0)
    disk = DiskS2.throughThreePointS2(p, q, r)

    scene.add(disk, SPHERICAL_DISK_STYLE)
    scene.addAll([p, q, r], style=SPHERICAL_POINT_STYLE)
    arc = None
    if include_arc:
        arc = CircleArcS2(p, q, disk)
        scene.add(arc, SPHERICAL_ARC_STYLE)
    return {
        "scene": scene,
        "disk": disk,
        "arc": arc,
    }


def main():
    app = App()
    euclidean_data = build_euclidean_scene()
    spherical_data = build_spherical_scene(include_arc=True)

    window = Window("Qt Multiview - Separate Scenes", layout="grid", size=(1440, 860))
    euclidean_view = Euclidean2View(euclidean_data["scene"], title="Euclidean scene")
    spherical_view = Spherical2View(spherical_data["scene"], title="Spherical scene")
    window.add_view(euclidean_view, row=0, col=0)
    window.add_view(spherical_view, row=0, col=1)

    panel = window.add_panel("Independent controls", side="right", width=320)
    status = panel.add_text("status", "Each view owns its own Scene")

    state = {
        "circle": euclidean_data["circle"],
        "show_polygon_fill": True,
        "show_arc": True,
        "show_sphere": True,
    }

    def set_status(message):
        status.set_text(message)

    def update_circle(radius):
        scene = euclidean_data["scene"]
        old_circle = state["circle"]
        scene.remove(old_circle)
        new_circle = CircleE2(PointE2(0.1, 0.05), radius)
        state["circle"] = new_circle
        scene.add(new_circle, EUCLIDEAN_CIRCLE_STYLE)
        euclidean_view.fit()
        set_status("euclidean scene: circle radius = {:.2f}".format(radius))

    def toggle_polygon_fill(checked):
        state["show_polygon_fill"] = checked
        euclidean_data["scene"].set_style(
            euclidean_data["polygon"],
            EUCLIDEAN_POLYGON_STYLE.copy(fill=Fill(color="#81c995", alpha=0.16 if checked else 0.0)),
        )
        set_status("euclidean polygon fill {}".format("on" if checked else "off"))

    def toggle_arc(checked):
        state["show_arc"] = checked
        scene = spherical_data["scene"]
        arc = spherical_data["arc"]
        if checked and arc is not None and arc not in scene:
            scene.add(arc, SPHERICAL_ARC_STYLE)
        elif (not checked) and arc is not None:
            scene.remove(arc)
        set_status("spherical arc {}".format("shown" if checked else "hidden"))

    def toggle_sphere(checked):
        state["show_sphere"] = checked
        spherical_view.show_sphere() if checked else spherical_view.hide_sphere()
        set_status("reference sphere {}".format("shown" if checked else "hidden"))

    panel.add_slider("circle radius", min=0.35, max=2.5, value=1.0, step=0.05, on_change=update_circle)
    panel.add_checkbox("Show polygon fill", checked=True, on_change=toggle_polygon_fill)
    panel.add_checkbox("Show spherical arc", checked=True, on_change=toggle_arc)
    panel.add_checkbox("Show sphere", checked=True, on_change=toggle_sphere)
    panel.add_button("Fit Euclidean view", on_click=euclidean_view.fit)
    panel.add_button("Fit Spherical view", on_click=spherical_view.fit)
    panel.add_button("Fit both views", on_click=lambda: (euclidean_view.fit(), spherical_view.fit()))

    euclidean_view.fit()
    spherical_view.fit()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
