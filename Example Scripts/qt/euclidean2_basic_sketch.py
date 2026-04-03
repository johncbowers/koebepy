"""Basic Qt sketch demonstrating the new Euclidean2View backend."""

from __future__ import absolute_import

from koebe.geometries.euclidean2 import CircleE2, PointE2, PolygonE2, SegmentE2
from koebe.graphics.qt import App, Scene, Window
from koebe.graphics.qt.style import Fill, Marker, Stroke, Style
from koebe.graphics.qt.views import Euclidean2View


BACKGROUND_COLOR = "#f8f9fa"
POINT_STYLE = Style(marker=Marker(color="#202124", size=10), stroke=Stroke(color="#ffffff", width=1))
HIGHLIGHT_STYLE = Style(marker=Marker(color="#f29900", size=12), stroke=Stroke(color="#ffffff", width=1.5))
SEGMENT_STYLE = Style(stroke=Stroke(color="#8ab4f8", width=2.5))
POLYGON_STYLE = Style(
    stroke=Stroke(color="#81c995", width=2),
    fill=Fill(color="#81c995", alpha=0.18),
)
POLYGON_OUTLINE_STYLE = Style(
    stroke=Stroke(color="#81c995", width=2),
    fill=Fill(color="#81c995", alpha=0.0),
)


def make_circle_style(radius):
    alpha = max(0.08, min(0.35, 0.10 + 0.08 * float(radius)))
    return Style(
        stroke=Stroke(color="#f28b82", width=2.5),
        fill=Fill(color="#f28b82", alpha=alpha),
    )


def build_polygon(a, b, c):
    return PolygonE2([a, b, c])


def build_segments(a, b, c):
    return [
        SegmentE2(a, b),
        SegmentE2(b, c),
        SegmentE2(c, a),
    ]


def main():
    app = App()
    scene = Scene()

    a = PointE2(-1.5, -1.0)
    b = PointE2(1.75, -0.6)
    c = PointE2(0.2, 1.6)
    center = PointE2(0.0, 0.1)

    polygon = build_polygon(a, b, c)
    segments = build_segments(a, b, c)
    circle = CircleE2(center, 1.0)

    scene.add(polygon, POLYGON_STYLE)
    scene.addAll(segments, style=SEGMENT_STYLE)
    scene.add(circle, make_circle_style(circle.radius))
    scene.addAll([a, b, c], style=POINT_STYLE)
    scene.set_style(a, HIGHLIGHT_STYLE)

    window = Window("Euclidean2View Test Sketch", layout="grid", size=(1280, 840))
    view = Euclidean2View(scene, background_color=BACKGROUND_COLOR)
    window.add_view(view, row=0, col=0)

    panel = window.add_panel(title="Controls", side="right", width=320)
    status = panel.add_text("status", "Ready")

    state = {
        "circle": circle,
        "circle_radius": circle.radius,
        "polygon_visible": True,
        "highlight_on": True,
    }

    def update_status(message):
        status.set_text(message)

    def update_circle(radius):
        old_circle = state["circle"]
        scene.remove(old_circle)
        new_circle = CircleE2(center, radius)
        state["circle"] = new_circle
        state["circle_radius"] = radius
        scene.add(new_circle, make_circle_style(radius))
        update_status("circle radius = {:.2f}".format(radius))
        view.fit()

    def toggle_polygon(checked):
        state["polygon_visible"] = checked
        scene.set_style(polygon, POLYGON_STYLE if checked else POLYGON_OUTLINE_STYLE)
        update_status("polygon fill {}".format("on" if checked else "off"))

    def toggle_highlight(checked):
        state["highlight_on"] = checked
        scene.set_style(a, HIGHLIGHT_STYLE if checked else POINT_STYLE)
        update_status("highlight {}".format("on" if checked else "off"))

    def reset_scene():
        update_circle(1.0)
        toggle_polygon(True)
        toggle_highlight(True)
        update_status("reset")

    panel.add_slider(
        "radius",
        min=0.25,
        max=2.75,
        value=state["circle_radius"],
        step=0.05,
        on_change=update_circle,
    )
    panel.add_checkbox("Show polygon fill", checked=True, on_change=toggle_polygon)
    panel.add_checkbox("Highlight point A", checked=True, on_change=toggle_highlight)
    panel.add_button("Fit view", on_click=view.fit)
    panel.add_button("Reset", on_click=reset_scene)

    view.fit()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
