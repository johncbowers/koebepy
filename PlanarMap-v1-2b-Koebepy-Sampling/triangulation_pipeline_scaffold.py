"""Triangulation/map conversion pipeline.

This script can:
1) build a DCEL from a fixture triangulation,
2) run the original planarmap executable with passthrough flags,
3) parse existing planarmap output (Maple or edge-list),
4) write JSON suitable for later DCEL/pickling workflows.

Attribution:
- Integrates with external PlanarMap output by Gilles Schaeffer.
- Reference: https://www.lix.polytechnique.fr/~schaeffe/PagesWeb/PlanarMap/index-en.html
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

from planarmap_config import get_planarmap_bin


@dataclass
class Vertex:
	"""A DCEL vertex identified by a stable integer id."""

	id: int
	x: Optional[float] = None
	y: Optional[float] = None
	is_boundary: bool = False
	radius: Optional[float] = None
	incident_halfedge: Optional[int] = None


@dataclass
class HalfEdge:
	"""Directed edge record in a DCEL."""

	id: int
	origin: int
	twin: int
	next: int
	prev: int
	face: int


@dataclass
class Face:
	"""Face record in a DCEL."""

	id: int
	halfedge: int
	is_outer: bool


@dataclass
class DCEL:
	"""Container for all DCEL primitives."""

	vertices: List[Vertex]
	halfedges: List[HalfEdge]
	faces: List[Face]


EDGE_LINE_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")
MAP_BLOCK_RE = re.compile(r"(Map|Dual)(\d+)\s*:=\s*\[(.*?)\];", re.DOTALL)
MAP_VERTEX_RE = re.compile(r"\[\s*(\d+)\s*,\s*\[([^\]]*)\]\s*\]")


def load_fixture_triangulation() -> Tuple[List[Tuple[float, float]], List[Tuple[int, int, int]]]:
	"""Return a tiny, known-good triangulation fixture.

	Geometry:
	- Convex quadrilateral with vertices in CCW order.
	- Triangulation uses diagonal (0, 2).
	"""

	vertices = [
		(0.0, 0.0),  # 0
		(1.0, 0.0),  # 1
		(1.0, 1.0),  # 2
		(0.0, 1.0),  # 3
	]

	# Both triangles are CCW.
	triangles = [
		(0, 1, 2),
		(0, 2, 3),
	]

	return vertices, triangles


def parse_maple_maps(text: str) -> List[Tuple[int, Dict[int, List[int]]]]:
	"""Parse planarmap Maple output blocks into rotation data.

	If both Map and Dual blocks exist, prefer Dual blocks because they reflect
	`-d` output and are the intended source for triangulation workflows.

	Returns a list of tuples: (map_index, {vertex_label: [signed_edge_labels...]})
	"""

	map_blocks: List[Tuple[int, Dict[int, List[int]]]] = []
	dual_blocks: List[Tuple[int, Dict[int, List[int]]]] = []

	for map_match in MAP_BLOCK_RE.finditer(text):
		block_kind = map_match.group(1)
		map_idx = int(map_match.group(2))
		body = map_match.group(3)
		rotation: Dict[int, List[int]] = {}

		for vertex_match in MAP_VERTEX_RE.finditer(body):
			v_label = int(vertex_match.group(1))
			labels_blob = vertex_match.group(2).strip()
			if labels_blob:
				signed_labels = [int(tok.strip()) for tok in labels_blob.split(",")]
			else:
				signed_labels = []
			rotation[v_label] = signed_labels

		if not rotation:
			continue

		if block_kind == "Dual":
			dual_blocks.append((map_idx, rotation))
		else:
			map_blocks.append((map_idx, rotation))

	return dual_blocks if dual_blocks else map_blocks


def parse_edge_list_blocks(text: str) -> List[List[Tuple[int, int]]]:
	"""Parse planarmap edge-list output into blocks of undirected edges."""

	blocks: List[List[Tuple[int, int]]] = []
	current: List[Tuple[int, int]] = []

	for raw_line in text.splitlines():
		line = raw_line.strip()
		match = EDGE_LINE_RE.match(line)
		if match:
			a = int(match.group(1))
			b = int(match.group(2))
			current.append((a, b))
			continue

		if current:
			blocks.append(current)
			current = []

	if current:
		blocks.append(current)

	return blocks


def detect_planarmap_output_kind(text: str) -> str:
	"""Detect whether output resembles Maple map output or edge-list output."""

	if MAP_BLOCK_RE.search(text):
		return "maple"
	if any(EDGE_LINE_RE.match(line.strip()) for line in text.splitlines()):
		return "edgelist"
	return "unknown"


def build_dcel_from_maple_rotation(rotation: Dict[int, List[int]]) -> DCEL:
	"""Build a DCEL from planarmap Maple rotation-system output.

	The rotation system gives cyclic order of signed edge labels around each vertex.
	For each edge id k, +k and -k represent opposite darts.
	"""

	sorted_labels = sorted(rotation.keys())
	label_to_vid = {label: i for i, label in enumerate(sorted_labels)}
	vertices = [
		Vertex(id=label_to_vid[label], x=None, y=None, is_boundary=False, radius=None)
		for label in sorted_labels
	]

	halfedges: List[HalfEdge] = []
	dart_key_to_id: Dict[Tuple[int, int], int] = {}
	edge_seen_signs: Dict[int, set] = {}
	sigma: Dict[int, int] = {}

	for v_label in sorted_labels:
		v_id = label_to_vid[v_label]
		signed_labels = rotation[v_label]
		if not signed_labels:
			continue

		local_dart_ids: List[int] = []
		for signed in signed_labels:
			edge_id = abs(signed)
			sign = 1 if signed > 0 else -1
			key = (edge_id, sign)
			if key in dart_key_to_id:
				raise ValueError(
					f"Malformed map: duplicate dart label occurrence {signed} at vertex {v_label}."
				)

			dart_id = len(halfedges)
			dart_key_to_id[key] = dart_id
			edge_seen_signs.setdefault(edge_id, set()).add(sign)
			halfedges.append(
				HalfEdge(
					id=dart_id,
					origin=v_id,
					twin=-1,
					next=-1,
					prev=-1,
					face=-1,
				)
			)
			local_dart_ids.append(dart_id)

			if vertices[v_id].incident_halfedge is None:
				vertices[v_id].incident_halfedge = dart_id

		deg = len(local_dart_ids)
		for i, dart_id in enumerate(local_dart_ids):
			sigma[dart_id] = local_dart_ids[(i + 1) % deg]

	for edge_id, signs in edge_seen_signs.items():
		if signs != {-1, 1}:
			raise ValueError(
				f"Malformed map: edge id {edge_id} does not have both + and - darts."
			)

	for (edge_id, sign), dart_id in dart_key_to_id.items():
		twin_id = dart_key_to_id.get((edge_id, -sign))
		if twin_id is None:
			raise ValueError(f"Missing twin for edge id {edge_id}, sign {sign}.")
		halfedges[dart_id].twin = twin_id

	# Face permutation in combinatorial maps: phi = sigma o alpha.
	# alpha is twin involution; sigma is rotation around vertex.
	for dart_id, he in enumerate(halfedges):
		alpha = he.twin
		if alpha not in sigma:
			raise ValueError(f"Malformed map: no vertex rotation for dart {alpha}.")
		he.next = sigma[alpha]

	for dart_id, he in enumerate(halfedges):
		# Build prev as inverse of next.
		next_id = he.next
		halfedges[next_id].prev = dart_id

	faces: List[Face] = []
	visited = [False] * len(halfedges)

	for start in range(len(halfedges)):
		if visited[start]:
			continue

		face_id = len(faces)
		faces.append(Face(id=face_id, halfedge=start, is_outer=False))

		cur = start
		guard = 0
		while not visited[cur]:
			visited[cur] = True
			halfedges[cur].face = face_id
			cur = halfedges[cur].next
			guard += 1
			if guard > len(halfedges):
				raise ValueError("Face traversal exceeded dart count; malformed next pointers.")

	return DCEL(vertices=vertices, halfedges=halfedges, faces=faces)


def build_dcel_from_triangulation(
	vertex_coords: List[Tuple[float, float]],
	triangles: List[Tuple[int, int, int]],
) -> DCEL:
	"""Build a canonical DCEL from triangle indices.

	Assumptions for this first iteration:
	- Vertex ids are 0..V-1.
	- Triangles are consistently oriented (CCW for bounded faces).
	- Input is a connected triangulation of a single outer boundary.
	"""

	vertices = [Vertex(id=i, x=xy[0], y=xy[1]) for i, xy in enumerate(vertex_coords)]
	halfedges: List[HalfEdge] = []
	faces: List[Face] = []

	# Directed-edge map for bounded faces only:
	# (u, v) -> halfedge id that goes u -> v.
	directed_to_he: Dict[Tuple[int, int], int] = {}

	for tri in triangles:
		face_id = len(faces)
		a, b, c = tri
		tri_directed = [(a, b), (b, c), (c, a)]
		tri_he_ids: List[int] = []

		for u, v in tri_directed:
			key = (u, v)
			if key in directed_to_he:
				raise ValueError(f"Duplicate directed edge in bounded faces: {key}")

			he_id = len(halfedges)
			halfedges.append(HalfEdge(id=he_id, origin=u, twin=-1, next=-1, prev=-1, face=face_id))
			directed_to_he[key] = he_id
			tri_he_ids.append(he_id)

			if vertices[u].incident_halfedge is None:
				vertices[u].incident_halfedge = he_id

		# Link the 3 bounded halfedges around the triangular face.
		for i in range(3):
			cur = tri_he_ids[i]
			nxt = tri_he_ids[(i + 1) % 3]
			prv = tri_he_ids[(i - 1) % 3]
			halfedges[cur].next = nxt
			halfedges[cur].prev = prv

		faces.append(Face(id=face_id, halfedge=tri_he_ids[0], is_outer=False))

	# Create the outer face record now; outer halfedges are appended next.
	outer_face_id = len(faces)
	faces.append(Face(id=outer_face_id, halfedge=-1, is_outer=True))

	# For every bounded halfedge without a reverse partner, create an outer halfedge.
	# We also store each outer edge destination explicitly to wire outer next/prev later.
	outer_by_origin: Dict[int, int] = {}
	outer_destination: Dict[int, int] = {}

	for (u, v), he_id in directed_to_he.items():
		rev_key = (v, u)
		if rev_key in directed_to_he:
			# Interior pair: bounded edge has bounded twin.
			rev_id = directed_to_he[rev_key]
			halfedges[he_id].twin = rev_id
		else:
			# Boundary edge: create twin on outer face with reversed direction.
			out_id = len(halfedges)
			halfedges.append(
				HalfEdge(
					id=out_id,
					origin=v,
					twin=he_id,
					next=-1,
					prev=-1,
					face=outer_face_id,
				)
			)
			halfedges[he_id].twin = out_id

			outer_by_origin[v] = out_id
			outer_destination[out_id] = u

			vertices[v].is_boundary = True
			vertices[u].is_boundary = True
			if vertices[v].incident_halfedge is None:
				vertices[v].incident_halfedge = out_id

	# Wire the outer cycle by matching destination -> next origin.
	for out_id, dest in outer_destination.items():
		if dest not in outer_by_origin:
			raise ValueError(
				"Boundary linking failed: expected one outer halfedge starting at "
				f"vertex {dest}, but found none."
			)
		nxt_id = outer_by_origin[dest]
		halfedges[out_id].next = nxt_id

	# Backfill prev from next links.
	for out_id in outer_destination:
		nxt_id = halfedges[out_id].next
		halfedges[nxt_id].prev = out_id

	# Choose a representative halfedge for the outer face.
	if outer_destination:
		first_outer_he = next(iter(outer_destination.keys()))
		faces[outer_face_id].halfedge = first_outer_he

	return DCEL(vertices=vertices, halfedges=halfedges, faces=faces)


def validate_dcel(dcel: DCEL) -> List[str]:
	"""Return a list of validation errors; empty means valid."""

	errors: List[str] = []

	# 1) Vertex ids should be contiguous 0..V-1.
	expected_vertex_ids = list(range(len(dcel.vertices)))
	actual_vertex_ids = [v.id for v in dcel.vertices]
	if actual_vertex_ids != expected_vertex_ids:
		errors.append("Vertex ids are not contiguous 0..V-1.")

	# 2) Twin validity and involution.
	for he in dcel.halfedges:
		if he.twin < 0 or he.twin >= len(dcel.halfedges):
			errors.append(f"Halfedge {he.id} has invalid twin index {he.twin}.")
			continue
		if dcel.halfedges[he.twin].twin != he.id:
			errors.append(f"Halfedge {he.id} fails twin involution check.")

	# 3) next/prev reciprocity and face indices.
	for he in dcel.halfedges:
		if he.next < 0 or he.next >= len(dcel.halfedges):
			errors.append(f"Halfedge {he.id} has invalid next index {he.next}.")
			continue
		if he.prev < 0 or he.prev >= len(dcel.halfedges):
			errors.append(f"Halfedge {he.id} has invalid prev index {he.prev}.")
			continue
		if dcel.halfedges[he.next].prev != he.id:
			errors.append(f"Halfedge {he.id} fails next->prev reciprocity check.")
		if dcel.halfedges[he.prev].next != he.id:
			errors.append(f"Halfedge {he.id} fails prev->next reciprocity check.")
		if he.face < 0 or he.face >= len(dcel.faces):
			errors.append(f"Halfedge {he.id} has invalid face index {he.face}.")

	# 4) Face cycles should close.
	for face in dcel.faces:
		if face.halfedge < 0:
			errors.append(f"Face {face.id} has no representative halfedge.")
			continue

		cycle_ids: List[int] = []
		current = face.halfedge
		guard = 0
		while True:
			cycle_ids.append(current)
			current = dcel.halfedges[current].next
			guard += 1
			if current == face.halfedge:
				break
			if guard > len(dcel.halfedges):
				errors.append(f"Face {face.id} cycle traversal did not close.")
				break

	# 5) Euler characteristic for connected planar embedding.
	# E is number of undirected edges, so E = halfedge_count / 2.
	if len(dcel.halfedges) % 2 != 0:
		errors.append("Halfedge count is odd; cannot derive undirected edge count.")
	else:
		v_count = len(dcel.vertices)
		e_count = len(dcel.halfedges) // 2
		f_count = len(dcel.faces)
		euler = v_count - e_count + f_count
		if euler != 2:
			errors.append(
				f"Euler characteristic failed: V-E+F = {euler}, expected 2."
			)

	return errors


def validate_triangulation_faces(dcel: DCEL) -> List[str]:
	"""Require every non-outer face to be a triangle."""

	errors: List[str] = []
	for face in dcel.faces:
		if face.is_outer:
			continue

		cycle_len = 0
		cur = face.halfedge
		guard = 0
		while True:
			cycle_len += 1
			cur = dcel.halfedges[cur].next
			guard += 1
			if cur == face.halfedge:
				break
			if guard > len(dcel.halfedges):
				errors.append(f"Face {face.id} cycle traversal did not close.")
				break

		if cycle_len != 3:
			errors.append(
				f"Face {face.id} has cycle length {cycle_len}; expected 3 for triangulation."
			)

	return errors


def dcel_to_dict(dcel: DCEL) -> Dict[str, object]:
	"""Serialize DCEL to plain dict for inspection and future JSON interchange."""

	return {
		"index_base": 0,
		"vertices": [asdict(v) for v in dcel.vertices],
		"halfedges": [asdict(he) for he in dcel.halfedges],
		"faces": [asdict(f) for f in dcel.faces],
	}


def graph_block_to_dict(edges: List[Tuple[int, int]]) -> Dict[str, object]:
	"""Serialize an undirected edge list block to JSON-friendly dict."""

	verts = sorted({u for u, _ in edges} | {v for _, v in edges})
	return {
		"vertex_labels": verts,
		"edges": [{"u": u, "v": v} for u, v in edges],
	}


def run_planarmap_capture(planarmap_bin: str, planarmap_args: List[str]) -> str:
	"""Run planarmap and return stdout text.

	If no explicit output mode is provided, force Maple map output (-p -O3)
	so a full DCEL can be reconstructed.
	"""

	filtered_args = [arg for arg in planarmap_args if arg != "--"]
	has_print = any(arg == "-p" for arg in filtered_args)
	has_output_mode = any(arg.startswith("-O") for arg in filtered_args)

	cmd = [planarmap_bin] + filtered_args
	if not has_print:
		cmd.append("-p")
	if not has_output_mode:
		cmd.append("-O3")

	proc = subprocess.run(
		cmd,
		check=False,
		capture_output=True,
		text=True,
	)
	if proc.returncode != 0:
		stderr = proc.stderr.strip()
		raise RuntimeError(
			f"planarmap failed with code {proc.returncode}. "
			f"stderr: {stderr if stderr else '<empty>'}"
		)
	return proc.stdout


def convert_planarmap_text_to_json(text: str, require_triangulation: bool) -> Dict[str, object]:
	"""Convert planarmap textual output into structured JSON payload."""

	output_kind = detect_planarmap_output_kind(text)

	if output_kind == "maple":
		parsed_maps = parse_maple_maps(text)
		maps_payload: List[Dict[str, object]] = []

		for map_idx, rotation in parsed_maps:
			dcel = build_dcel_from_maple_rotation(rotation)
			errors = validate_dcel(dcel)
			if require_triangulation:
				errors.extend(validate_triangulation_faces(dcel))

			maps_payload.append(
				{
					"map_index": map_idx,
					"vertex_rotation": rotation,
					"dcel": dcel_to_dict(dcel),
					"validation_errors": errors,
				}
			)

		return {
			"source_format": "planarmap-maple",
			"maps": maps_payload,
		}

	if output_kind == "edgelist":
		blocks = parse_edge_list_blocks(text)
		return {
			"source_format": "planarmap-edgelist",
			"graphs": [graph_block_to_dict(block) for block in blocks],
			"note": (
				"Edge-list format does not contain enough embedding information to "
				"reconstruct DCEL face cycles uniquely."
			),
		}

	raise ValueError(
		"Unrecognized planarmap output format. Use Maple output (-O3 -p) "
		"for full DCEL reconstruction."
	)


def main() -> int:
	"""Run conversion pipeline and optionally write JSON output."""

	default_planarmap_bin = get_planarmap_bin("../planarmap.exe")

	parser = argparse.ArgumentParser(
		description=(
			"Convert triangulation/map sources to JSON. "
			"Supports fixture, existing planarmap output text, or direct planarmap execution."
		)
	)
	parser.add_argument(
		"--run-planarmap",
		action="store_true",
		help="Run planarmap executable; unknown args are forwarded as planarmap flags.",
	)
	parser.add_argument(
		"--planarmap-bin",
		default=default_planarmap_bin,
		help="Path to planarmap executable when using --run-planarmap.",
	)
	parser.add_argument(
		"--from-planarmap-output",
		default="",
		help="Path to an existing text file containing planarmap output.",
	)
	parser.add_argument(
		"--require-triangulation",
		action="store_true",
		help="Require all faces to be triangles in reconstructed DCELs.",
	)
	parser.add_argument(
		"--out-json",
		default="",
		help="Optional path to write converted JSON output.",
	)
	args, passthrough_flags = parser.parse_known_args()

	if args.run_planarmap and args.from_planarmap_output:
		raise ValueError("Use only one of --run-planarmap or --from-planarmap-output.")

	if args.run_planarmap:
		raw_output = run_planarmap_capture(args.planarmap_bin, passthrough_flags)
		payload = convert_planarmap_text_to_json(
			raw_output,
			require_triangulation=args.require_triangulation,
		)
		payload["source"] = "planarmap-subprocess"
		payload["planarmap_bin"] = args.planarmap_bin
		payload["planarmap_args"] = [flag for flag in passthrough_flags if flag != "--"]
	elif args.from_planarmap_output:
		with open(args.from_planarmap_output, "r", encoding="utf-8") as fh:
			raw_output = fh.read()
		payload = convert_planarmap_text_to_json(
			raw_output,
			require_triangulation=args.require_triangulation,
		)
		payload["source"] = "planarmap-output-file"
		payload["input_file"] = args.from_planarmap_output
	else:
		coords, triangles = load_fixture_triangulation()
		dcel = build_dcel_from_triangulation(coords, triangles)
		errors = validate_dcel(dcel)
		errors.extend(validate_triangulation_faces(dcel))
		payload = {
			"source": "fixture-triangulation",
			"dcel": dcel_to_dict(dcel),
			"validation_errors": errors,
		}

	if args.out_json:
		with open(args.out_json, "w", encoding="utf-8") as fh:
			json.dump(payload, fh, indent=2)
		print(f"Wrote JSON to: {args.out_json}")
	else:
		print(json.dumps(payload, indent=2))

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
