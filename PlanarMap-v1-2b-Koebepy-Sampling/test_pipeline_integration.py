#!/usr/bin/env python3
"""Integration test: verify PlanarMap to koebepy DCEL state pipeline."""

import json
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))


def test_imports() -> bool:
    print("\n=== TEST 1: Module Imports ===")
    try:
        from koebepy_dcel_state_exporter import KoebepyDCELExporter, export_dcel_state_from_json_file
        import triangulation_pipeline_scaffold
        import batch_dcel_state_generator
        _ = (KoebepyDCELExporter, export_dcel_state_from_json_file, triangulation_pipeline_scaffold, batch_dcel_state_generator)
        print("PASS: imports")
        return True
    except Exception as exc:
        print(f"FAIL: import error: {exc}")
        return False


def test_state_export_single() -> bool:
    print("\n=== TEST 2: Single State Export ===")
    try:
        from koebepy_dcel_state_exporter import export_dcel_state_from_json_file
        from triangulation_pipeline_scaffold import (
            load_fixture_triangulation,
            build_dcel_from_triangulation,
            dcel_to_dict,
        )

        # Build a fixture DCEL JSON source on the fly so the test does not rely on
        # optional sample files that may be cleaned up during repo maintenance.
        coords, triangles = load_fixture_triangulation()
        dcel = build_dcel_from_triangulation(coords, triangles)

        with tempfile.NamedTemporaryFile(suffix="_source.json", delete=False, mode="w", encoding="utf-8") as src_tmp:
            src = Path(src_tmp.name)
            json.dump({"dcel": dcel_to_dict(dcel)}, src_tmp, indent=2)

        with tempfile.NamedTemporaryFile(suffix="_state.json", delete=False) as tmp:
            out = Path(tmp.name)

        export_dcel_state_from_json_file(str(src), str(out))

        data = json.loads(out.read_text(encoding="utf-8"))
        required = ["vert_data", "dart_data", "edge_data", "face_data", "outer_face_idx"]
        missing = [k for k in required if k not in data]
        src.unlink(missing_ok=True)
        out.unlink(missing_ok=True)

        if missing:
            print(f"FAIL: missing keys: {missing}")
            return False

        print("PASS: single state export")
        return True
    except Exception as exc:
        print(f"FAIL: single export error: {exc}")
        return False


def test_examples_folder() -> bool:
    print("\n=== TEST 3: Examples Folder ===")
    examples = SCRIPT_DIR / "dcel_examples"
    expected = {
        "one_map_state.json",
        "one_dual_tri_map_state.json",
        "fixture_state.json",
    }
    if not examples.exists():
        print("FAIL: dcel_examples folder missing")
        return False

    found = {p.name for p in examples.glob("*.json")}
    missing = sorted(expected - found)
    if missing:
        print(f"FAIL: missing example files: {missing}")
        return False

    print("PASS: examples present")
    return True


def test_batch_api() -> bool:
    print("\n=== TEST 4: Batch API ===")
    try:
        import inspect
        from batch_dcel_state_generator import run_planarmap_batch, json_to_states, organize_test_suite

        print(f"run_planarmap_batch args: {list(inspect.signature(run_planarmap_batch).parameters.keys())}")
        print(f"json_to_states args: {list(inspect.signature(json_to_states).parameters.keys())}")
        print(f"organize_test_suite args: {list(inspect.signature(organize_test_suite).parameters.keys())}")
        print("PASS: batch API")
        return True
    except Exception as exc:
        print(f"FAIL: batch API error: {exc}")
        return False


def main() -> int:
    print("=" * 70)
    print("PlanarMap to koebepy DCEL State Pipeline Tests")
    print("=" * 70)

    tests = [
        test_imports,
        test_state_export_single,
        test_examples_folder,
        test_batch_api,
    ]

    results = [(t.__name__, t()) for t in tests]
    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, ok in results:
        print(f"{'PASS' if ok else 'FAIL'}: {name}")

    print(f"\n{passed}/{total} tests passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
