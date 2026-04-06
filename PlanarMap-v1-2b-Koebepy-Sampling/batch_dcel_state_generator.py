"""Batch generate koebepy DCEL state JSON triangulations from planarmap.

This script orchestrates the full pipeline:
1. Run planarmap multiple times to generate random triangulations
2. Parse the output to DCEL JSON format
3. Convert to koebepy DCEL state JSON objects
4. Organize them into a test suite structure

Attribution:
- Uses external PlanarMap output format by Gilles Schaeffer.
- Reference: https://www.lix.polytechnique.fr/~schaeffe/PagesWeb/PlanarMap/index-en.html
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from planarmap_config import get_planarmap_bin


def run_planarmap_batch(
    planarmap_bin: str,
    count: int,
    output_dir: str,
    args: List[str],
    seed_base: int = 42,
) -> List[str]:
    """Generate multiple random triangulations using planarmap.
    
    Args:
        planarmap_bin: Path to planarmap executable
        count: Number of triangulations to generate
        output_dir: Directory to save JSON outputs
        args: Additional arguments to pass to planarmap (e.g., -n 20)
        seed_base: Starting seed for random number generator
        
    Returns:
        List of JSON file paths created
    """
    
    os.makedirs(output_dir, exist_ok=True)
    json_paths: List[str] = []
    max_attempts = max(count * 20, count)

    for attempt in range(max_attempts):
        if len(json_paths) >= count:
            break

        seed = seed_base + attempt
        valid_idx = len(json_paths)
        json_out = os.path.join(output_dir, f"triangulation_{valid_idx:04d}.json")

        print(
            f"\n[{valid_idx+1}/{count}] Generating triangulation candidate "
            f"(attempt={attempt+1}, seed={seed})..."
        )
        
        # Import the pipeline here to avoid circular imports
        from triangulation_pipeline_scaffold import (
            run_planarmap_capture,
            convert_planarmap_text_to_json,
        )
        
        try:
            # Build command: planarmap [user args] -X seed -p -O3
            cmd_args = list(args) + ["-X", str(seed), "-p", "-O3"]
            
            raw_output = run_planarmap_capture(planarmap_bin, cmd_args)
            payload = convert_planarmap_text_to_json(raw_output, require_triangulation=True)

            # Keep only valid triangulations: every parsed map block must have
            # an empty validation_errors list.
            if payload.get("source_format") == "planarmap-maple":
                invalid_maps = [
                    m.get("map_index", idx)
                    for idx, m in enumerate(payload.get("maps", []))
                    if m.get("validation_errors")
                ]
                if invalid_maps:
                    print(
                        "  -> Skipping candidate: non-triangulation faces detected "
                        f"in map blocks {invalid_maps}"
                    )
                    continue

            payload["sequence_index"] = valid_idx
            payload["seed"] = seed
            
            with open(json_out, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
            
            print(f"  -> Wrote JSON to: {json_out}")
            json_paths.append(json_out)
            
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    if len(json_paths) < count:
        raise RuntimeError(
            f"Only generated {len(json_paths)} valid triangulations out of requested "
            f"{count} after {max_attempts} attempts."
        )

    return json_paths


def json_to_states(
    json_paths: List[str],
    state_output_dir: str,
    koebepy_path: str,
) -> List[str]:
    """Convert JSON DCEL files to koebepy DCEL state JSON objects.
    
    Args:
        json_paths: List of JSON file paths to convert
        state_output_dir: Directory to save state JSON files
        koebepy_path: Path to koebepy module
        
    Returns:
        List of state JSON file paths created
    """

    from koebepy_dcel_state_exporter import KoebepyDCELExporter

    os.makedirs(state_output_dir, exist_ok=True)
    exporter = KoebepyDCELExporter(koebepy_path)
    state_paths = []
    
    for i, json_path in enumerate(json_paths):
        print(f"\n[{i+1}/{len(json_paths)}] Converting {os.path.basename(json_path)}...")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle different JSON formats
        if 'maps' in data:
            # Multiple maps per file (from maple output)
            for map_idx, map_data in enumerate(data.get('maps', [])):
                seq_id = data.get('sequence_index', i)
                state_name = f"triangulation_{seq_id:04d}_map{map_idx}_state.json"
                state_path = os.path.join(state_output_dir, state_name)

                dcel_dict = map_data.get('dcel', {})
                vertices = dcel_dict.get('vertices', [])
                halfedges = dcel_dict.get('halfedges', [])
                faces = dcel_dict.get('faces', [])

                try:
                    exporter.save_dcel_state(vertices, halfedges, faces, state_path)
                    state_paths.append(state_path)
                except Exception as e:
                    print(f"    ERROR on map {map_idx}: {e}")
        else:
            # Single map per file
            seq_id = data.get('sequence_index', i)
            state_name = f"triangulation_{seq_id:04d}_state.json"
            state_path = os.path.join(state_output_dir, state_name)

            # Extract DCEL from various possible formats
            if 'dcel' in data:
                dcel_dict = data['dcel']
            else:
                # Assume entire file is DCEL
                dcel_dict = data

            vertices = dcel_dict.get('vertices', [])
            halfedges = dcel_dict.get('halfedges', [])
            faces = dcel_dict.get('faces', [])

            try:
                exporter.save_dcel_state(vertices, halfedges, faces, state_path)
                state_paths.append(state_path)
            except Exception as e:
                print(f"    ERROR: {e}")

    return state_paths


def organize_test_suite(
    state_paths: List[str],
    test_suite_dir: str,
    test_suite_json_path: Optional[str] = None,
) -> None:
    """Organize DCEL state files into a test suite structure.
    
    Creates a TestSuite directory with symlinks/copies and a manifest.
    
    Args:
        state_paths: List of state JSON file paths
        test_suite_dir: Output directory for the test suite
        test_suite_json_path: Optional path to write a manifest JSON
    """

    os.makedirs(test_suite_dir, exist_ok=True)

    manifest = {
        "triangulation_count": len(state_paths),
        "test_suite_path": test_suite_dir,
        "state_files": [],
    }

    for i, state_path in enumerate(state_paths):
        state_name = os.path.basename(state_path)
        dst_path = os.path.join(test_suite_dir, state_name)

        # Copy instead of symlink for portability
        try:
            import shutil
            shutil.copy2(state_path, dst_path)
            print(f"  Copied {state_name}")
            manifest["state_files"].append({
                "index": i,
                "filename": state_name,
                "path": dst_path,
            })
        except Exception as e:
            print(f"  ERROR copying {state_name}: {e}")

    if test_suite_json_path:
        with open(test_suite_json_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        print(f"\nWrote test suite manifest to: {test_suite_json_path}")


def main():
    default_planarmap_bin = get_planarmap_bin("../planarmap.exe")

    parser = argparse.ArgumentParser(
        description="Batch generate koebepy DCEL state files for triangulation test suites"
    )
    parser.add_argument(
        "--planarmap-bin",
        default=default_planarmap_bin,
        help="Path to planarmap executable"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of triangulations to generate"
    )
    parser.add_argument(
        "--output-dir",
        default="./batch_output",
        help="Directory to save intermediate JSON files"
    )
    parser.add_argument(
        "--state-output-dir",
        default="./state_output",
        help="Directory to save koebepy DCEL state JSON files"
    )
    parser.add_argument(
        "--test-suite-dir",
        default="./TestSuite",
        help="Directory to organize final test suite"
    )
    parser.add_argument(
        "--test-suite-manifest",
        default="./TestSuite/manifest.json",
        help="Path to write test suite manifest"
    )
    parser.add_argument(
        "--koebepy-path",
        default=r"c:\Users\Derby\Documents\College\Junior Year\Summer 2025\CS 480\koebepy",
        help="Path to koebepy module"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Starting seed for random generation"
    )
    parser.add_argument(
        "--skip-json",
        action="store_true",
        help="Skip JSON generation, only process existing JSONs"
    )
    parser.add_argument(
        "--skip-state",
        action="store_true",
        help="Skip state generation, only organize existing state JSON files"
    )

    # Backward-compatible alias for older scripts.
    parser.add_argument(
        "--skip-pickle",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    
    args, planarmap_args = parser.parse_known_args()
    
    # Step 1: Generate JSON from planarmap
    if not args.skip_json:
        print("=" * 70)
        print("STEP 1: Generate JSON DCEL files from planarmap")
        print("=" * 70)
        json_paths = run_planarmap_batch(
            args.planarmap_bin,
            args.count,
            args.output_dir,
            planarmap_args,
            seed_base=args.seed,
        )
    else:
        # Collect existing JSON files
        output_dir = Path(args.output_dir)
        json_paths = sorted(output_dir.glob("triangulation_*.json"))
        json_paths = [str(p) for p in json_paths]
        print(f"Found {len(json_paths)} existing JSON files to process")
    
    if not json_paths:
        print("ERROR: No JSON files to process")
        return 1
    
    # Step 2: Convert JSON to koebepy DCEL state files
    skip_state = args.skip_state or args.skip_pickle
    if not skip_state:
        print("\n" + "=" * 70)
        print("STEP 2: Convert JSON to koebepy DCEL state JSON")
        print("=" * 70)
        state_paths = json_to_states(
            json_paths,
            args.state_output_dir,
            args.koebepy_path,
        )
    else:
        # Collect existing state files.
        state_dir = Path(args.state_output_dir)
        state_paths = sorted(state_dir.glob("triangulation_*_state.json"))
        state_paths = [str(p) for p in state_paths]
        print(f"Found {len(state_paths)} existing state files to organize")

    if not state_paths:
        print("ERROR: No state files to organize")
        return 1
    
    # Step 3: Organize into test suite
    print("\n" + "=" * 70)
    print("STEP 3: Organize into test suite")
    print("=" * 70)
    organize_test_suite(
        state_paths,
        args.test_suite_dir,
        args.test_suite_manifest,
    )

    print("\n" + "=" * 70)
    print(f"SUCCESS: Generated test suite with {len(state_paths)} triangulations")
    print(f"Test suite location: {args.test_suite_dir}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
