"""Qt version of the coin unfolding example."""

from __future__ import absolute_import

import heapq
import math
import random

from koebe.algorithms.circlepackings.layout import canonical_spherical_projection, compute_tangencies
from koebe.algorithms.hypPacker import maximalPacking
from koebe.algorithms.incrementalConvexHull import randomConvexHullE3
from koebe.geometries.euclidean2 import CircleE2, PointE2, SegmentE2
from koebe.geometries.euclidean3 import PointE3, SegmentE3
from koebe.graphics.qt import App, Scene, Window
from koebe.graphics.qt.style import Fill, Marker, Stroke, Style
from koebe.graphics.qt.views import Euclidean2View, Spherical2View


DEFAULT_POINT_COUNT = 100
DEFAULT_ITERATIONS = 10000
DEFAULT_SCALE = 100.0

BLACK_STYLE = Style(stroke=Stroke(color="#202124", width=1.2))
RED_STYLE = Style(stroke=Stroke(color="#d93025", width=2.0), fill=Fill(color="#d93025", alpha=0.0))
GREEN_STYLE = Style(stroke=Stroke(color="#188038", width=2.0), fill=Fill(color="#188038", alpha=0.0))
BLUE_STYLE = Style(stroke=Stroke(color="#1a73e8", width=2.0), fill=Fill(color="#1a73e8", alpha=0.0))
GRAY_STYLE = Style(stroke=Stroke(color="#9aa0a6", width=1.0), fill=Fill(color="#9aa0a6", alpha=0.0))


def _highlight_style(index, first_neighbor_index, second_neighbor_index):
    if index == 0:
        return RED_STYLE
    if index == first_neighbor_index:
        return GREEN_STYLE
    if index == second_neighbor_index:
        return BLUE_STYLE
    return BLACK_STYLE


def compute_coin_unfolding(n_points=DEFAULT_POINT_COUNT, n_iterations=DEFAULT_ITERATIONS):
    print("Generating random convex hull of {} points and computing a Tutte embedding...".format(n_points))
    poly = randomConvexHullE3(n_points)
    poly.outerFace = poly.faces[0]
    print("\tdone.")

    print("Computing a circle packing...")
    hyp_packing, _ = maximalPacking(poly, num_passes=n_iterations)
    packing = canonical_spherical_projection(hyp_packing)
    packing.markIndices()
    print("\tdone.")

    compute_tangencies(packing)

    unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
    unfolding.markIndices()

    print("Placing vertex 0")
    unfolding.verts[0].data = CircleE2(PointE2(0, 0), packing.verts[0].data.radiusE3)
    nbs_s2 = packing.verts[0].neighbors()
    edges_s2 = packing.verts[0].edges()
    nbs_e2 = unfolding.verts[0].neighbors()

    for vertex in unfolding.verts:
        vertex.parent = None

    nbs_e2[0].data = CircleE2(
        PointE2(unfolding.verts[0].data.radius + nbs_s2[0].data.radiusE3, 0),
        nbs_s2[0].data.radiusE3,
    )
    nbs_e2[0].parent = unfolding.verts[0]

    normal = packing.verts[0].data.basis3.normalize()
    for index in range(1, len(nbs_e2)):
        v0 = edges_s2[0].data.toVectorE3() - packing.verts[0].data.centerE3
        vi = edges_s2[index].data.toVectorE3() - packing.verts[0].data.centerE3
        print("Placing vertex {} with parent 0".format(nbs_s2[index].idx))

        theta = math.atan2(v0.cross(vi).dot(normal), v0.dot(vi))
        nbs_e2[index].data = CircleE2(
            PointE2(
                (packing.verts[0].data.radiusE3 + nbs_s2[index].data.radiusE3) * math.cos(theta),
                (packing.verts[0].data.radiusE3 + nbs_s2[index].data.radiusE3) * math.sin(theta),
            ),
            nbs_s2[index].data.radiusE3,
        )
        nbs_e2[index].parent = unfolding.verts[0]

    for edge in packing.edges:
        vector = edge.data - PointE3.O
        edge.key = -vector.dot(normal)

    priority_queue = [(edge.key, random.random(), edge) for edge in packing.edges]
    heapq.heapify(priority_queue)

    while priority_queue:
        _, _, edge = heapq.heappop(priority_queue)
        v0_index, v1_index = [vertex.idx for vertex in edge.endPoints()]

        v0 = unfolding.verts[v0_index]
        v1 = unfolding.verts[v1_index]
        if v0.data is None and v1.data is None:
            print("Can't place edge because neither endpoint is placed. This should never happen.")
            continue
        if v0.data is None:
            v0, v1 = v1, v0
            v0_index, v1_index = v1_index, v0_index

        if v1.data is None:
            print("Placing vertex {} with parent {}".format(v1_index, v0_index))
            if v0.parent is None:
                print("v0 has no parent, this should not happen. v0's index is {}".format(v0_index))
                break

            parent_direction_e2 = (v0.parent.data.center - v0.data.center).normalize()
            parent_direction_s2 = (
                packing.verts[v0_index].data.tangentPointWith(packing.verts[v0.parent.idx].data).toVectorE3()
                - packing.verts[v0_index].data.centerE3
            )
            v1_direction_s2 = (
                packing.verts[v0_index].data.tangentPointWith(packing.verts[v1_index].data).toVectorE3()
                - packing.verts[v0_index].data.centerE3
            )
            normal = packing.verts[v0_index].data.basis3.normalize()

            theta = math.atan2(
                parent_direction_s2.cross(v1_direction_s2).dot(normal),
                parent_direction_s2.dot(v1_direction_s2),
            )

            direction = parent_direction_e2.rotate(theta).normalize()
            v1.data = CircleE2(
                v0.data.center + (packing.verts[v0_index].data.radiusE3 + packing.verts[v1_index].data.radiusE3) * direction,
                packing.verts[v1_index].data.radiusE3,
            )
            v1.parent = v0

    inversive_distances_sphere = []
    inversive_distances_plane = []
    for i in range(len(unfolding.verts) - 1):
        for j in range(i + 1, len(unfolding.verts)):
            if (
                unfolding.verts[j].parent != unfolding.verts[i]
                and unfolding.verts[i].parent != unfolding.verts[j]
                and unfolding.verts[i].data is not None
                and unfolding.verts[j].data is not None
            ):
                inversive_distances_sphere.append(packing.verts[i].data.inversiveDistTo(packing.verts[j].data))
                inversive_distances_plane.append(unfolding.verts[i].data.inversiveDistTo(unfolding.verts[j].data))

    passes_inversive_distance_test = not (
        False in [
            inversive_distances_plane[index] > inversive_distances_sphere[index]
            for index in range(len(inversive_distances_plane))
        ]
    )

    print("Passes inversive distance test: {}".format(passes_inversive_distance_test))
    print("Minimum inversive distance detected in the sphere: {}".format(min(inversive_distances_sphere)))
    print("Minimum inversive distance detected in the plane: {}".format(min(inversive_distances_plane)))

    segments_e2 = []
    for vertex in unfolding.verts:
        if vertex.parent is not None:
            segments_e2.append(SegmentE2(vertex.data.center, vertex.parent.data.center))

    segments_e3 = []
    for vertex in unfolding.verts:
        if vertex.parent is not None:
            segments_e3.append(
                SegmentE3(
                    packing.verts[vertex.idx].data.basis3.normalize().toPointE3(),
                    packing.verts[vertex.parent.idx].data.basis3.normalize().toPointE3(),
                )
            )

    return {
        "packing": packing,
        "unfolding": unfolding,
        "segments_e2": segments_e2,
        "segments_e3": segments_e3,
        "first_neighbor_index": nbs_e2[0].idx,
        "second_neighbor_index": nbs_e2[1].idx,
        "passes_inversive_distance_test": passes_inversive_distance_test,
        "min_sphere": min(inversive_distances_sphere),
        "min_plane": min(inversive_distances_plane),
    }


def build_qt_scenes(n_points=DEFAULT_POINT_COUNT, n_iterations=DEFAULT_ITERATIONS, scale=DEFAULT_SCALE):
    data = compute_coin_unfolding(n_points=n_points, n_iterations=n_iterations)
    scene_s2 = Scene()
    scene_e2 = Scene()

    first_neighbor_index = data["first_neighbor_index"]
    second_neighbor_index = data["second_neighbor_index"]

    for vertex in data["packing"].verts:
        scene_s2.add(
            vertex.data,
            _highlight_style(vertex.idx, first_neighbor_index, second_neighbor_index),
        )

    for segment in data["segments_e3"]:
        scene_s2.add(segment, GRAY_STYLE)

    for vertex in data["unfolding"].verts:
        if vertex.data is not None:
            scene_e2.add(
                scale * vertex.data,
                _highlight_style(vertex.idx, first_neighbor_index, second_neighbor_index),
            )

    for segment in data["segments_e2"]:
        scene_e2.add(scale * segment, GRAY_STYLE)

    return scene_s2, scene_e2, data


def main(n_points=DEFAULT_POINT_COUNT, n_iterations=DEFAULT_ITERATIONS, scale=DEFAULT_SCALE):
    app = App()
    scene_s2, scene_e2, data = build_qt_scenes(
        n_points=n_points,
        n_iterations=n_iterations,
        scale=scale,
    )

    window = Window("Coin Unfolding (Qt)", layout="grid", size=(1600, 900))
    spherical_view = Spherical2View(scene_s2, title="Coin polyhedron", show_sphere=False)
    euclidean_view = Euclidean2View(scene_e2, title="Proposed unfolding")
    window.add_view(spherical_view, row=0, col=0)
    window.add_view(euclidean_view, row=0, col=1)

    panel = window.add_panel("Coin unfolding", side="right", width=340)
    panel.add_text("summary", "Qt version of Example Scripts/coin_unfolding.py")
    panel.add_text("points", "points = {}".format(n_points))
    panel.add_text("iterations", "iterations = {}".format(n_iterations))
    panel.add_text(
        "passes_test",
        "passes inversive distance test = {}".format(data["passes_inversive_distance_test"]),
    )
    panel.add_text("min_sphere", "min sphere distance = {:.6f}".format(data["min_sphere"]))
    panel.add_text("min_plane", "min plane distance = {:.6f}".format(data["min_plane"]))
    panel.add_button("Fit spherical view", on_click=spherical_view.fit)
    panel.add_button("Fit unfolding view", on_click=euclidean_view.fit)
    panel.add_button("Fit both", on_click=lambda: (spherical_view.fit(), euclidean_view.fit()))
    panel.add_checkbox(
        "Show sphere",
        checked=False,
        on_change=lambda checked: spherical_view.show_sphere() if checked else spherical_view.hide_sphere(),
    )

    spherical_view.fit()
    euclidean_view.fit()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
