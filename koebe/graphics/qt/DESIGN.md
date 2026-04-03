# koebe.graphics.qt Design Specification

## Purpose

`koebe.graphics.qt` is a new native, non-browser graphics backend for KoebePy.

It is intended to:

- coexist with the existing Flask-based viewers,
- leave all existing geometry code in `koebe.geometries` untouched,
- provide fast interactive rendering,
- support multiple simultaneous views,
- support animation and user interaction,
- provide a clean interface suitable for mathematicians.

This package is **additional functionality**, not a replacement for the existing Flask viewers.

---

## Core Design Constraints

### 1. Geometry and graphics are strictly separated

Objects in `koebe.geometries` remain pure mathematical objects.

Examples:

- `PointE2`
- `PointE3`
- `PointS2`

These objects:

- do **not** know how to draw themselves,
- do **not** store color, line width, marker size, labels, or other display data,
- do **not** depend on Qt, VisPy, or any graphics code.

All drawing state belongs to the graphics layer.

---

### 2. Existing geometry code is not modified

No changes should be required in:

- `koebe.geometries.euclidean2`
- `koebe.geometries.spherical2`
- any other geometry module (these are in koebe.geometries)

The new viewer system must adapt to existing geometry types from outside.

---

### 3. Existing Flask viewers remain untouched

Files in `koebe.graphics.flask`, including:

- `spherical2server.py`

remain intact.

`koebe.graphics.qt` is a parallel backend.

---

### 4. Naming should match geometry module structure

The initial views are:

- `Euclidean2View`
- `Spherical2View`

This naming is intentional and should align with geometry module names such as:

- `koebe.geometries.euclidean2`
- `koebe.geometries.spherical2`

---

### 5. Scene styling is external

A `Scene` stores:

- a geometry object,
- one associated style.

A geometry object has at most one style in a given scene.

A scene does **not** allow the same geometry object to appear multiple times with different styles.

---

### 6. Views ignore unsupported geometry

A view renders only geometry types it understands.

Unsupported geometry in the same scene is ignored silently.

Example:

- `Euclidean2View` renders `PointE2`, `SegmentE2`, etc.
- `Spherical2View` renders `PointS2`, spherical circles, spherical arcs, etc.
- each ignores incompatible geometry from the other setting

This allows a single mixed scene to be displayed by multiple views at once.

---

## Recommended Technology Stack

### UI framework

- **PySide6**

Used for:

- application lifecycle,
- windows,
- layouts,
- timers,
- keyboard and mouse events,
- future widget integration.

### Rendering engine

- **VisPy**

Used for:

- GPU-backed rendering,
- performant redraws,
- 2D and 3D drawing,
- camera integration,
- future large-scene support.

### Rationale

This combination gives:

- native desktop rendering,
- no browser dependency,
- no JSON round-trips,
- better scalability than the current Flask viewer pattern,
- enough structure for a clean API.

---

## Package Layout

Proposed initial layout:

```text
koebe/
  graphics/
    flask/
      ...
    qt/
      __init__.py
      DESIGN.md
      app.py
      window.py
      scene.py
      style.py
      controls.py
      views/
        __init__.py
        base.py
        euclidean2view.py
        spherical2view.py
      renderers/
        __init__.py
        vispy_base.py
        vispy_euclidean2.py
        vispy_spherical2.py
```

This can expand later, but the initial structure should stay small.

---

## Architectural Overview

The package should be organized around five main concepts:

1. `App`
2. `Window`
3. `Scene`
4. `Style`
5. `View`
6. `ControlPanel`

### App

Responsible for:

- creating and managing the Qt application,
- running the event loop,
- global animation timer,
- global key/mouse callback registration if needed.

### Window

Responsible for:

- hosting one or more views,
- arranging views in a grid or split layout,
- hosting optional control panels,
- window-level title and size,
- future shared controls.

### Scene

Responsible for:

- storing geometry-to-style associations,
- notifying views when content changes,
- providing iteration over all scene entries.

### Style

Responsible for display-only properties such as:

- stroke color,
- line width,
- fill color,
- marker size,
- marker color,
- transparency.

### View

Responsible for:

- rendering a `Scene`,
- deciding which geometry it understands,
- ignoring the rest,
- handling view-local interactions,
- managing camera/navigation.

### ControlPanel

Responsible for:

- hosting native interactive UI elements for a sketch,
- exposing controls such as sliders, buttons, numeric fields, checkboxes, and text output,
- updating scene content or sketch parameters through callbacks,
- remaining separate from geometry storage and rendering logic.

Control panels belong to the window/UI layer, not the scene layer.

---

## Scene Model

### Concept

A `Scene` is a mapping:

- `geometry object -> style`

Only one style is attached to a given geometry object within a scene.

### Intended API

```python
scene.add(geometry, style=None)
scene.addAll(items, style=None)
scene.set_style(geometry, style)
scene.remove(geometry)
scene.clear()
scene.style_of(geometry)
scene.items()
```

### Semantics

- `add` inserts or replaces the style for the geometry object.
- `addAll` inserts multiple objects at once.
- `set_style` updates the style attached to an existing geometry object.
- `remove` removes the object from the scene.
- `clear` removes all objects.
- `items` yields `(geometry, style)` pairs.

### Bulk add behavior

The API should support bulk insertion for convenience and to reduce scene update overhead.

`scene.addAll(...)` should accept either:

- a list of geometry objects, optionally together with a single shared `style`, or
- a list of pairs of the form `(geometry, style)`.

Examples:

```python
scene.addAll([p, q, r], style=Style(marker=Marker(color="white", size=8)))

scene.addAll([
  (p, Style(marker=Marker(color="white", size=8))),
  (q, Style(marker=Marker(color="orange", size=8))),
  (s, Style(stroke=Stroke(color="gray", width=2))),
])
```

This should update the scene efficiently and trigger redraw only after the bulk operation completes.

### Style update behavior

The API should support changing the style of an existing geometry object without rebuilding the scene externally.

Example:

```python
scene.add(p, Style(marker=Marker(color="white", size=8)))
scene.set_style(p, Style(marker=Marker(color="orange", size=10)))
```

This should mark the scene as dirty and trigger redraws in attached views.

### Internal requirements

The scene should:

- support efficient iteration,
- track dirty state,
- notify subscribed views on modification,
- avoid unnecessary full rebuilds where practical.

---

## Style Model

Style must remain independent of geometry.

### Proposed shape

```python
Style(
    stroke=Stroke(...),
    fill=Fill(...),
    marker=Marker(...),
)
```

### Components

#### Stroke

For line-like drawing:

- color
- width
- alpha
- optional dash pattern later

#### Fill

For filled regions:

- color
- alpha

#### Marker

For point-like drawing:

- color
- size
- shape

### Example

```python
Style(
    stroke=Stroke(color="white", width=2),
    fill=Fill(color="#3366aa", alpha=0.25),
    marker=Marker(color="orange", size=8),
)
```

Not every style component applies to every geometry type.

---

## Window and Multi-View Model

A window can contain multiple simultaneous views.

### Example target usage

```python
win = Window("KoebePy", layout="grid", size=(1400, 900))
win.add_view(Euclidean2View(scene), row=0, col=0)
win.add_view(Spherical2View(scene), row=0, col=1)
```

### Requirements

- one window can host multiple views,
- one window can host optional UI panels in addition to views,
- multiple views can share one scene,
- multiple views may also use separate scenes in the same window,
- each view renders only supported geometry,
- scene changes trigger redraw in all attached views.

### Shared-scene multiview pattern

One important use case is a single mixed `Scene` that contains geometry for more than one view type.

Example:

```python
scene = Scene()

# Euclidean objects
scene.add(PointE2(0, 0), euclidean_point_style)

# Spherical objects
scene.add(PointS2(1, 0, 0), spherical_point_style)

win = Window("Shared Scene", layout="grid")
win.add_view(Euclidean2View(scene), row=0, col=0)
win.add_view(Spherical2View(scene), row=0, col=1)
```

In this pattern:

- the same `Scene` instance is attached to multiple views,
- each view ignores unsupported geometry types,
- a single scene mutation may redraw multiple views,
- control callbacks may update shared state that is visible in more than one view.

This is the right pattern when the views are two renderings of one conceptual model.

### Separate-scene multiview pattern

Another important use case is a window with multiple views where each view owns its own scene.

Example:

```python
euclidean_scene = Scene()
spherical_scene = Scene()

win = Window("Separate Scenes", layout="grid")
win.add_view(Euclidean2View(euclidean_scene), row=0, col=0)
win.add_view(Spherical2View(spherical_scene), row=0, col=1)
```

In this pattern:

- scene mutations are isolated to one view unless the programmer explicitly coordinates them,
- each scene can use its own update cadence and object set,
- controls can target one view independently of the other,
- the window still provides a unified UI layout for both views.

This is the right pattern when the views are related in the interface but not the same renderable model.

### Control panel requirement

The system should support attaching native Qt control panels to a window so that a programmer can build an interactive geometric sketch.

These controls are intended for the programmer creating the sketch, not for modifying the `Scene` abstraction itself.

Examples of useful controls include:

- sliders for continuous parameters,
- buttons for recomputation or reset actions,
- checkboxes for visibility toggles,
- numeric entry fields for integer or floating-point parameters,
- static labels,
- dynamic text output / status text,
- dropdown selection widgets where appropriate.

This should be treated as a first-class part of the window/layout design, because interactive sketches often need both a drawing surface and a small set of controls.

### Separation rule

Controls should **not** be stored in `Scene`.

The responsibilities should remain:

- `Scene`: geometry objects and their styles only
- `View`: rendering and camera/navigation
- `Window`: layout of views and control panels
- `ControlPanel`: interactive widgets and sketch-facing UI

This separation keeps the drawing model clean and avoids mixing graphics state with user interface state.

### Suggested window API

The window layer should support adding one or more panels around the view area.

Example target API:

```python
win = Window("Sketch", layout="grid", size=(1400, 900))
view = Euclidean2View(scene)
win.add_view(view, row=0, col=0)

panel = win.add_panel(title="Controls", side="right", width=320)
panel.add_slider("radius", min=0.1, max=2.0, value=1.0, on_change=update_radius)
panel.add_button("Reset", on_click=reset_scene)
panel.add_number_field("n", value=12, on_change=update_n)
panel.add_checkbox("Show auxiliary circles", checked=True, on_change=toggle_aux)
panel.add_text("status", "Ready")
```

The exact widget API can evolve, but the design should explicitly support this use case.

### Panel width

The panel API should support an optional fixed-width hint so that a sketch author can keep the control area visually stable.

Example:

```python
panel = win.add_panel(title="Controls", side="right", width=320)
```

This is especially useful when status text or control values change frequently, since it avoids distracting panel-width changes while interacting with the sketch.

### Panel placement

At minimum, the initial design should support placing a control panel:

- to the left of the views,
- to the right of the views,
- above the views,
- below the views.

Later versions may support dockable panels or resizable split layouts.

---

## View Base Behavior

Each view should provide:

- a link to a `Scene`,
- a redraw/update method,
- fit-to-scene behavior if meaningful,
- local input handling,
- conversion utilities where appropriate.

### Expected base responsibilities

A common base view should define:

- scene subscription
- invalidation / redraw path
- title handling
- renderer lifecycle
- common event hooks

The base view should not be responsible for creating sliders, buttons, or text fields. Those belong to the window/panel layer.

---

## Control Panels and Sketch UI

### Motivation

Many geometric sketches are not just static renderings. A programmer often wants a small interactive interface for adjusting parameters and inspecting output while the sketch is running.

Typical examples include:

- a slider controlling a circle radius,
- a numeric field controlling iteration count,
- a button that rebuilds the current construction,
- a checkbox that toggles a family of auxiliary objects,
- a text label showing the current value of an invariant or measurement.

Qt is well suited to this because it already provides mature native widgets.

### Design decision

The new backend should explicitly support sketch UI, but that support should live in a dedicated panel/control layer rather than being embedded in `Scene`.

This means:

- scenes remain purely about geometry and styles,
- views remain purely about rendering and navigation,
- windows may host one or more control panels,
- control callbacks may mutate scene content, restyle objects, or update application state.

### Proposed classes

The first implementation does not need a large widget framework, but it should reserve space in the design for the following concepts:

- `ControlPanel`
- `Control`
- simple typed controls such as `SliderControl`, `ButtonControl`, `NumberFieldControl`, `CheckboxControl`, and `TextControl`

These do not need to be exposed as a deep inheritance hierarchy immediately. A pragmatic builder-style API is acceptable.

### Suggested panel API

```python
panel = win.add_panel(title="Parameters", side="right")

panel.add_slider(
  "radius",
  min=0.1,
  max=2.0,
  value=1.0,
  step=0.01,
  on_change=update_radius,
)

panel.add_button("Reset", on_click=reset_scene)
panel.add_number_field("n", value=12, on_change=update_n)
panel.add_checkbox("Show labels", checked=False, on_change=toggle_labels)
panel.add_text("status", "Ready")
```

The goal is a small and easy API for sketch authors, not a complete abstraction over all Qt widgets.

### Callback model

Control callbacks should be able to:

- update application-level parameters,
- update scene contents,
- call `scene.set_style(...)`,
- trigger recomputation of constructions,
- update text displays in the control panel.

Example:

```python
def update_radius(value):
  rebuild_scene(radius=value)

def toggle_aux(checked):
  scene.set_style(aux_circle, visible_style if checked else hidden_style)

panel.add_slider("radius", min=0.1, max=2.0, value=1.0, on_change=update_radius)
panel.add_checkbox("Show auxiliary circles", checked=True, on_change=toggle_aux)
```

### Text output and status displays

The sketch UI should support programmer-facing output text.

This is useful for displaying:

- current parameter values,
- counts of objects,
- convergence diagnostics,
- measurements,
- short status messages.

This should be supported either through a dedicated text output control or through mutable label-like controls.

Example target API:

```python
status = panel.add_text("status", "Ready")

def rebuild_scene(radius):
  # recompute geometry here
  status.set_text(f"radius = {radius:.3f}")
```

### Initial control set

The first implementation should aim to support:

- button
- slider
- checkbox
- integer field
- floating-point field
- text/label output

Dropdowns or radio groups may be added later if needed.

### Layout expectations

The panel system does not need to be highly sophisticated at first, but it should be capable of:

- stacking controls vertically,
- grouping related controls under a titled panel,
- living beside or below one or more views,
- resizing with the window without breaking the view layout.

### Relationship to animation and interaction

Control panels should work naturally with animation and interactive sketches.

Examples:

- a button starts or stops animation,
- a slider changes a parameter used by the per-frame update callback,
- a numeric field adjusts iteration depth,
- a text display reports frame state or measured values.

### Implementation difficulty

This feature should not be especially hard to include because Qt already has mature widget support.

The main design concern is architectural cleanliness, not low-level feasibility.

In particular, adding control panels is substantially easier than embedding browser-style UI or inventing a custom widget toolkit.

### Initial implementation guidance

To keep the first coding pass manageable, the initial implementation should:

- provide `Window.add_panel(...)`,
- provide a small `ControlPanel` wrapper around standard Qt widgets,
- expose a few convenience methods such as `add_slider`, `add_button`, `add_checkbox`, `add_number_field`, and `add_text`,
- keep the control values and callbacks in Python,
- avoid over-generalizing until real sketch examples are built.

This is enough to support interactive mathematical sketches without overcomplicating the first implementation.

---

## Euclidean2View

### Purpose

Displays geometry from `koebe.geometries.euclidean2`.

### Initial supported object types

The exact list depends on existing geometry classes, but the first pass should target obvious Euclidean 2D objects such as:

- `PointE2`
- `SegmentE2`
- circles, if present
- polylines / polygons, if present

### Behavior

- renders only Euclidean 2D geometry it recognizes,
- ignores everything else,
- provides standard 2D panning and zooming interaction,
- supports fitting the view to visible content.

### Interaction defaults

Suggested defaults:

- left drag: pan
- scroll: zoom
- double click: fit scene

These can be adjusted later.

### Navigation requirement

`Euclidean2View` should support direct 2D navigation by default.

This means the user must be able to:

- pan the current view,
- zoom in and out smoothly,
- inspect local detail without rebuilding the scene,
- reset or refit the camera to the visible scene.

The 2D camera model does not need trackball behavior, but it should behave like a standard planar camera with translation and scale.

---

## Spherical2View

### Purpose

Displays geometry from `koebe.geometries.spherical2`.

### Initial supported object types

The exact list depends on existing classes, but the first pass should target:

- `PointS2`
- spherical circles, if present
- spherical arcs / geodesic segments, if present

### Default sphere display

The sphere itself should be shown by default.

This is not a geometry object from the scene. It is part of the view presentation.

The sphere must be:

- visible by default,
- toggleable on/off,
- styled independently of scene geometry.

### Required API behavior

```python
view.show_sphere()
view.hide_sphere()
view.toggle_sphere()
```

### Camera requirement

`Spherical2View` should use a **quaternion-based trackball camera**.

This is required to avoid Euler-angle issues and to provide natural sphere rotation.

### Interaction defaults

Suggested defaults:

- left drag: rotate using quaternion trackball
- scroll: zoom
- double click: reset camera
- optional future modifier interactions:
  - shift + drag: pan
  - key press to reset view

### Default sphere style

The sphere should be visible but subtle.

A reasonable default presentation:

- soft fill with low alpha,
- light outline,
- scene geometry drawn more prominently.

---

## Rendering Rules

### Core rule

Views decide what to render by inspecting geometry type.

Conceptually:

```python
for geometry, style in scene.items():
    if self.supports(geometry):
        self.draw_geometry(geometry, style)
```

### Consequences

- no geometry classes need drawing methods,
- no adapter registration system is required initially,
- a single mixed scene can be reused across views,
- unsupported geometry does not break rendering.

---

## Renderer Layer

Views should delegate low-level drawing to renderer classes.

### Why separate views and renderers

A view manages:

- user interaction,
- scene ownership,
- camera state,
- visibility options.

A renderer manages:

- GPU objects,
- VisPy visuals,
- draw batching,
- efficient scene synchronization.

### Initial renderer split

- `vispy_euclidean2.py`
- `vispy_spherical2.py`

### Renderer responsibilities

- translate supported geometry into GPU-friendly draw data,
- update visuals only when data changes,
- preserve style separation,
- expose a simple `sync(scene)` and `draw()` path to views.

---

## Animation Model

Many scenes are static, but some are animated or interactive.

The system should support both efficiently.

### Requirements

- static scenes should not require continuous redraw,
- animation loop should be optional,
- frame callbacks should be possible.

### Target behavior

```python
@app.on_frame
def update(dt):
    ...
```

Views should redraw only when:

- the scene changes,
- camera/view state changes,
- animation is active.

---

## Event Model

Events should belong to the graphics layer, not geometry.

### Desired callback categories

- key press
- mouse press
- mouse release
- mouse move / drag
- wheel / zoom
- frame update

### Scope

Callbacks may be:

- app-wide,
- window-specific,
- view-specific

The first implementation can stay minimal.

---

## Performance Goals

This backend is being introduced primarily for rendering performance.

### Goals

- eliminate browser/server communication overhead,
- avoid JSON serialization for local rendering,
- support multiple simultaneous views,
- scale better with larger scenes,
- make interactive updates feasible.

### Early optimization priorities

1. use GPU-backed visuals,
2. avoid recreating all draw data on every redraw,
3. separate scene-dirty from camera-dirty updates,
4. keep view-side filtering simple.

### Non-goals for the first pass

- maximal batching sophistication,
- advanced picking,
- high-end shader effects,
- vector export,
- notebook integration.

Those can come later.

---

## Public API Goals

The public API should feel simple and mathematical.

### Example target usage

```python
from koebe.geometries.euclidean2 import PointE2, SegmentE2
from koebe.geometries.spherical2 import PointS2
from koebe.graphics.qt import App, Window, Scene
from koebe.graphics.qt.views import Euclidean2View, Spherical2View
from koebe.graphics.qt.style import Style, Stroke, Marker

app = App()
scene = Scene()

p = PointE2(0, 0)
q = PointE2(1, 0)
u = PointS2(1, 0, 0)

scene.add(p, Style(marker=Marker(color="white", size=8)))
scene.add(q, Style(marker=Marker(color="orange", size=8)))
scene.add(SegmentE2(p, q), Style(stroke=Stroke(color="gray", width=2)))
scene.add(u, Style(marker=Marker(color="cyan", size=10)))

win = Window("KoebePy", layout="grid")
win.add_view(Euclidean2View(scene), row=0, col=0)
win.add_view(Spherical2View(scene), row=0, col=1)

app.run()
```

This should remain the style target for the package.

### Example target usage with separate scenes

```python
from koebe.graphics.qt import App, Window, Scene
from koebe.graphics.qt.views import Euclidean2View, Spherical2View

app = App()

euclidean_scene = Scene()
spherical_scene = Scene()

win = Window("KoebePy", layout="grid")
win.add_view(Euclidean2View(euclidean_scene), row=0, col=0)
win.add_view(Spherical2View(spherical_scene), row=0, col=1)

app.run()
```

This pattern should be documented explicitly because it is just as important as the shared-scene case.

The design should support both without requiring a special multiview abstraction.

### Example with controls

```python
from koebe.geometries.euclidean2 import PointE2
from koebe.graphics.qt import App, Window, Scene
from koebe.graphics.qt.views import Euclidean2View
from koebe.graphics.qt.style import Style, Marker

app = App()
scene = Scene()

p = PointE2(0, 0)
scene.add(p, Style(marker=Marker(color="white", size=8)))

win = Window("Interactive Sketch", layout="grid")
view = Euclidean2View(scene)
win.add_view(view, row=0, col=0)

panel = win.add_panel(title="Controls", side="right")
status = panel.add_text("status", "Ready")

def set_size(value):
  scene.set_style(p, Style(marker=Marker(color="white", size=value)))
  status.set_text(f"marker size = {value}")

def reset_scene():
  scene.set_style(p, Style(marker=Marker(color="white", size=8)))
  status.set_text("reset")

panel.add_slider("size", min=2, max=20, value=8, on_change=set_size)
panel.add_button("Reset", on_click=reset_scene)

app.run()
```

---

## Initial Implementation Scope

The first milestone should include:

### Core package

- `App`
- `Window`
- `Scene`
- `Style`, `Stroke`, `Fill`, `Marker`
- `ControlPanel`

### Views

- `Euclidean2View`
- `Spherical2View`

### Features

- scene sharing across multiple views
- static rendering
- basic interaction
- basic control panel support
- optional animation loop
- sphere visible by default in `Spherical2View`
- sphere visibility toggle
- quaternion-based trackball camera in `Spherical2View`

### Explicitly deferred

- advanced object picking
- labels/text
- linked selection
- export tools
- Jupyter integration
- broad geometry coverage beyond the first useful subset

---

## Phased Development Plan

The implementation should proceed in deliberate phases so that the package becomes usable early while keeping the architecture clean.

Each phase should end in a working, testable state. The goal is to avoid overbuilding infrastructure before the first useful sketch can run.

### Phase 1: foundation and package skeleton

This phase establishes the package structure and the core non-rendering abstractions.

#### Include

- package layout under `koebe.graphics.qt`
- `__init__.py`
- `Scene`
- `Style`, `Stroke`, `Fill`, `Marker`
- `App`
- `Window`
- `ControlPanel`
- base view class
- minimal renderer base classes

#### Deliverables

- `Scene.add(...)`
- `Scene.addAll(...)`
- `Scene.set_style(...)`
- `Scene.remove(...)`
- `Scene.clear()`
- scene change notification mechanism
- basic Qt window creation
- ability to place a placeholder view inside a window
- ability to place a basic control panel beside a view

#### Goals

- lock in the separation between geometry, style, rendering, and controls
- ensure the scene model is stable before implementing specific view logic
- make it possible to open a native window with a view area and a control panel area

#### Not yet required

- full geometry rendering
- camera logic
- sophisticated control widgets
- animation

### Phase 2: minimal Euclidean2View

This phase should produce the first genuinely useful sketching view.

#### Include

- `Euclidean2View`
- a VisPy-backed Euclidean 2D renderer
- support for the first small set of Euclidean 2D geometry types

#### Initial geometry support

- `PointE2`
- `SegmentE2`
- circles, if available in the existing geometry package
- simple polylines or polygons, if those types already exist and are straightforward to support

#### Deliverables

- display of Euclidean geometry from a `Scene`
- panning
- zooming
- fit-to-scene
- redraw on scene change
- style application for points and line-like objects
- unsupported objects ignored cleanly

#### Goals

- make a useful 2D sketch window possible
- validate the scene-to-renderer pipeline
- validate that control callbacks can update the scene and trigger redraw

#### Example target outcome

By the end of this phase, a programmer should be able to:

- create a `Scene`
- add `PointE2` and `SegmentE2` objects with styles
- open a `Window`
- attach a `Euclidean2View`
- attach a small control panel
- restyle geometry interactively using buttons or sliders

### Phase 3: minimal Spherical2View

This phase adds the first 3D-style spherical viewing capability.

#### Include

- `Spherical2View`
- a VisPy-backed spherical renderer
- quaternion-based trackball camera support
- visible reference sphere shown by default

#### Initial geometry support

- `PointS2`
- spherical circles, if readily available
- spherical arcs or geodesic segments, if readily available

#### Deliverables

- sphere visible by default
- `show_sphere()` / `hide_sphere()` / `toggle_sphere()`
- trackball rotation
- zoom control
- camera reset behavior
- scene redraw on style or geometry updates

#### Goals

- validate the 3D/spherical interaction model
- ensure the spherical view can coexist with Euclidean views in the same window
- confirm that one scene can be shared across heterogeneous views

#### Example target outcome

By the end of this phase, a programmer should be able to display `PointS2` objects on a visible sphere and rotate the scene naturally with the mouse.

### Phase 4: control panel refinement and sketch ergonomics

Once both main views exist, the sketch-building workflow should be improved.

#### Include

- stable `Window.add_panel(...)`
- better `ControlPanel` convenience API
- stronger widget coverage for common sketch tasks
- clearer interaction between panels and scene updates

#### Deliverables

- sliders with change callbacks
- buttons with click callbacks
- checkboxes with toggle callbacks
- integer and floating-point input fields
- mutable text/status output controls
- cleaner callback patterns for recomputation and restyling

#### Goals

- make interactive mathematical sketches pleasant to write
- reduce boilerplate for common UI tasks
- confirm that panels belong naturally in the window layer rather than the scene layer

#### Example target outcome

By the end of this phase, a sketch should be able to use sliders, buttons, and status text to drive recomputation without custom Qt widget wiring by the sketch author.

### Phase 5: broader geometry coverage

With the foundations working, support should expand to additional geometry types that already exist in `koebe.geometries`.

#### Include

- more Euclidean 2D primitives
- more spherical primitives
- filled geometry where applicable
- better style handling across primitive types

#### Candidates

- circles
- arcs
- polygonal chains
- polygons
- other existing geometry classes that are common in KoebePy examples

#### Deliverables

- more complete type filtering in each view
- renderer support for additional line and fill primitives
- more consistent fit-to-scene behavior across object types

#### Goals

- broaden the practical usefulness of the backend
- reduce the need for ad hoc one-off drawing helpers
- align supported geometry with the most common sketch patterns in the library

### Phase 6: animation and event polish

This phase improves runtime behavior for dynamic sketches.

#### Include

- optional animation loop
- frame callbacks
- cleaner event routing
- improved redraw control

#### Deliverables

- `@app.on_frame` or equivalent frame callback API
- predictable redraw scheduling for static versus animated scenes
- better handling of mouse and keyboard callbacks at app/view scope
- reduced unnecessary redraw work

#### Goals

- support animated constructions and demonstrations
- keep static scenes efficient
- make interactive examples behave consistently

### Phase 7: stabilization and example-driven refinement

This phase is for validating the design against actual KoebePy usage.

#### Include

- one or more small example sketches
- API cleanup based on real usage
- documentation refinements
- basic tests for core scene and UI behavior

#### Deliverables

- example scripts using `Euclidean2View`
- example scripts using `Spherical2View`
- example script with a control panel driving scene updates
- example script with two views sharing one `Scene`
- example script with two views using separate scenes
- regression coverage for scene mutation and view refresh behavior

#### Goals

- confirm the public API is pleasant for mathematicians to use
- remove awkward or overengineered pieces before broader expansion
- prepare the package for broader adoption inside the project

### Phase ordering rationale

The phases are ordered so that:

1. the abstract model is stabilized first,
2. the simplest useful view is delivered early,
3. the more specialized spherical view comes next,
4. sketch ergonomics improve only after the rendering path is proven,
5. broader geometry support is added after the main architecture is validated,
6. animation and polish come after the static and interactive core is solid.

This order should make it possible to begin coding immediately without losing sight of the long-term structure.

---

## Open Questions for Later

These are intentionally deferred, not blockers for the first pass:

- exact supported geometry classes in `euclidean2` and `spherical2`
- preferred default colors/theme
- object picking API
- labeling/annotation API
- whether views should expose direct world/screen conversion methods uniformly
- whether a future adapter registry becomes useful as more geometry modules are added

---

## Summary

`koebe.graphics.qt` should be a new native rendering backend with these defining properties:

- no changes to `koebe.geometries`
- no changes to existing Flask viewers
- strict geometry/style separation
- scene stores one style per geometry object
- views render only what they understand
- one window may contain views backed by either one shared scene or multiple separate scenes
- initial views are `Euclidean2View` and `Spherical2View`
- `Spherical2View` shows the sphere by default
- `Spherical2View` uses a quaternion-based trackball camera
- implementation should be based on PySide6 + VisPy

This is the intended direction for the first Qt viewer implementation.
