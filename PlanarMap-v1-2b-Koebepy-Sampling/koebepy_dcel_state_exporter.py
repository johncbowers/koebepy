"""Export DCEL structures in koebepy DCEL state format.

This module converts the PlanarMap-style JSON DCEL into the same structured
state payload used by koebepy DCEL serialization:

- vert_data
- dart_data
- edge_data
- face_data
- outer_face_idx

The output is plain JSON.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


class KoebepyDCELExporter:
    """Convert a DCEL topology to koebepy DCEL state format."""

    def __init__(self, koebepy_path: Optional[str] = None):
        """Initialize exporter.

        koebepy_path is accepted for backward compatibility but unused,
        because exporting plain DCEL state does not require importing koebepy.
        """
        _ = koebepy_path

    def dcel_json_to_state(
        self,
        vertices: List[Dict[str, Any]],
        halfedges: List[Dict[str, Any]],
        faces: List[Dict[str, Any]],
        outer_face_idx: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Convert JSON DCEL format to koebepy DCEL state dict.
        
        Args:
            vertices: List of vertex dicts with 'id', 'x', 'y', 'is_boundary', 'radius', 'incident_halfedge'
            halfedges: List of halfedge dicts with 'id', 'origin', 'twin', 'next', 'prev', 'face'
            faces: List of face dicts with 'id', 'halfedge', 'is_outer'
            outer_face_idx: Index of the outer face, or None
            
        Returns:
            State dict matching koebepy DCEL __reduce__ payload.
        """

        # Build vertex data: list of (incident_dart_idx, vertex_data_object)
        # For planar triangulations, vertex_data_object is None by default
        vert_data = []
        for v in vertices:
            incident_dart = v.get('incident_halfedge', 0)
            vert_data.append((incident_dart, None))
        
        # Build dart data: list of dicts with topology and data.
        dart_data = []
        for he in halfedges:
            dart_data.append({
            'edge': 0,  # overwritten after halfedge-to-edge mapping
                'origin': he['origin'],
                'face': he['face'],
                'prev': he['prev'],
                'next': he['next'],
                'twin': he['twin'],
                'data': None
            })
        
        # Need to establish edge indices from halfedge pairs
        # In DCEL, edges are undirected but represented as pairs of halfedges
        # For each halfedge, we need to know which edge it belongs to
        halfedge_to_edge: Dict[int, int] = {}
        edge_count = 0
        
        for he_id, he in enumerate(halfedges):
            if he_id not in halfedge_to_edge:
                twin_id = he['twin']
                halfedge_to_edge[he_id] = edge_count
                halfedge_to_edge[twin_id] = edge_count
                edge_count += 1
        
        # Update dart_data with correct edge indices
        for he_id, _he in enumerate(halfedges):
            dart_data[he_id]['edge'] = halfedge_to_edge[he_id]
        
        # Build edge data: list of (incident_dart_idx, edge_data_object)
        # For planar triangulations, edge_data_object is None by default
        edge_data = []
        edge_representative: Dict[int, int] = {}
        for he_id, _he in enumerate(halfedges):
            edge_id = halfedge_to_edge[he_id]
            if edge_id not in edge_representative:
                edge_representative[edge_id] = he_id
        
        for edge_id in range(edge_count):
            representative_dart = edge_representative.get(edge_id, 0)
            edge_data.append((representative_dart, None))
        
        # Build face data: list of (incident_dart_idx, face_data_object)
        # For planar triangulations, face_data_object is None
        face_data = []
        for f in faces:
            incident_dart = f.get('halfedge', 0)
            face_data.append((incident_dart, None))
        
        # Determine outer face index
        if outer_face_idx is None:
            # Find the face marked as outer
            for f in faces:
                if f.get('is_outer', False):
                    outer_face_idx = f['id']
                    break
        
        return {
            'vert_data': vert_data,
            'dart_data': dart_data,
            'edge_data': edge_data,
            'face_data': face_data,
            'outer_face_idx': outer_face_idx,
        }

    def export_dcel_state(
        self,
        vertices: List[Dict[str, Any]],
        halfedges: List[Dict[str, Any]],
        faces: List[Dict[str, Any]],
        outer_face_idx: Optional[int] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export a DCEL into koebepy DCEL state format.

        If output_path is provided, writes JSON.
        """
        state = self.dcel_json_to_state(vertices, halfedges, faces, outer_face_idx)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        return state

    def save_dcel_state(
        self,
        vertices: List[Dict[str, Any]],
        halfedges: List[Dict[str, Any]],
        faces: List[Dict[str, Any]],
        output_path: str,
        outer_face_idx: Optional[int] = None,
    ) -> None:
        """Save a DCEL as koebepy DCEL state JSON."""
        self.export_dcel_state(vertices, halfedges, faces, outer_face_idx, output_path)
        print(f"Saved DCEL state JSON to: {output_path}")


def export_dcel_state_from_json_file(
    json_dcel_path: str,
    output_state_path: str,
    koebepy_path: Optional[str] = None,
) -> None:
    """Convert a DCEL JSON file to koebepy DCEL state JSON."""
    exporter = KoebepyDCELExporter(koebepy_path)

    with open(json_dcel_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle various JSON formats
    if 'dcel' in data:
        # Format from triangulation_pipeline_scaffold
        dcel_data = data['dcel']
    elif 'maps' in data and data['maps']:
        # Planarmap Maple conversion payload: use first map by default
        dcel_data = data['maps'][0].get('dcel', {})
    else:
        # Assume the entire file is DCEL data
        dcel_data = data

    vertices = dcel_data.get('vertices', [])
    halfedges = dcel_data.get('halfedges', [])
    faces = dcel_data.get('faces', [])

    # Find outer face index
    outer_face_idx = None
    for face in faces:
        if face.get('is_outer', False):
            outer_face_idx = face['id']
            break

    exporter.save_dcel_state(
        vertices, halfedges, faces, output_state_path, outer_face_idx
    )


def pickle_dcel_from_json_file(
    json_dcel_path: str,
    output_pickle_path: str,
    koebepy_path: Optional[str] = None,
) -> None:
    """Backward-compatible wrapper.

    Old name retained, but now exports plain koebepy DCEL state JSON.
    """
    export_dcel_state_from_json_file(json_dcel_path, output_pickle_path, koebepy_path)


# Backward compatibility alias for class name.
KoebepyDCELPickler = KoebepyDCELExporter
