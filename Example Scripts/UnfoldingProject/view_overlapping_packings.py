#!/usr/bin/env python3

# I have to do an analysis on how the number of overlapings for dfs, bfs, and shrotest_path.
# the variable that is changing is the n_points variable
# change tolerance to 3e-8 in hyPacker.maximalPacking, actually just change the parameter in coin_unfolding_modular
# try 10k passes (iterations)
"""
View and analyze saved overlapping DCEL structures.

Features:
- View one, many, or all overlapping cases
- Filter by base_seed, method, or trial number
- Load and inspect DCEL structures
- Compare statistics across cases
- Verify saved data integrity

Usage:
    python view_overlapping_packings.py [options]

Examples:
    # List all overlapping cases
    python view_overlapping_packings.py --list-all
    
    # View and visualize all cases from a specific base seed
    python view_overlapping_packings.py --base-seed 1774895576523358000 --load-all --visualize
    
    # View specific trial with visualization
    python view_overlapping_packings.py --base-seed 1774895576523358000 --trial 1 --method dfs --load-one base1774895576523358000_trial0001_dfs_... --visualize
    
    # Load and visualize one specific case
    python view_overlapping_packings.py --load-one <case_name> --visualize
    
    # Compare statistics for a base seed
    python view_overlapping_packings.py --base-seed 1774895576523358000 --stats

    # List  and visualize all overlapping cases
    python view_overlapping_packings.py --list-all --visualize
"""

import sys
import os
import argparse
import pickle
from pathlib import Path
from statistics import mean, median

# Add koebepy root to path for imports
koebepy_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(koebepy_root))

from inversive_distance import find_overlapping_pairs, visualize_trial_unfolding, visualize_trial_packing
from koebe.graphics.flask.multiviewserver import viewer


def parse_metadata(metadata_file):
    """Parse metadata file and extract key information."""
    info = {}
    try:
        with open(metadata_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if ': ' in line:
                    key, value = line.strip().split(': ', 1)
                    info[key] = value
    except Exception as e:
        print(f"Error reading metadata: {e}")
    return info


def list_all_cases(output_dir="overlapping_packings"):
    """List all saved overlapping cases with metadata."""
    if not os.path.exists(output_dir):
        print(f"Directory not found: {output_dir}")
        return []

    metadata_files = [f for f in os.listdir(output_dir) if f.endswith("_metadata.txt")]
    
    if not metadata_files:
        print("No saved overlapping cases found.")
        return []

    print(f"\nFound {len(metadata_files)} overlapping case(s)\n")
    print(f"{'Base Seed':<20} {'Trial':<8} {'Method':<8} {'Overlaps':<10} {'Verts':<8} {'Trial Seed':<20}")
    print("=" * 80)

    cases = []
    for metadata_file in sorted(metadata_files):
        case_name = metadata_file.replace("_metadata.txt", "")
        metadata_path = os.path.join(output_dir, metadata_file)
        metadata = parse_metadata(metadata_path)
        
        base_seed = metadata.get("Base Seed", "?")
        trial = metadata.get("Trial", "?")
        method = metadata.get("Method", "?")
        overlaps = metadata.get("Number of overlapping pairs detected", "?")
        verts = metadata.get("Number of vertices", "?")
        trial_seed = metadata.get("Trial Seed", "?")
        
        print(f"{base_seed:<20} {trial:<8} {method:<8} {overlaps:<10} {verts:<8} {trial_seed:<20}")
        
        cases.append({
            "name": case_name,
            "base_seed": base_seed,
            "trial": trial,
            "method": method,
            "overlaps": overlaps,
            "verts": verts,
            "trial_seed": trial_seed,
            "metadata_path": metadata_path,
            "metadata": metadata,
        })

    return cases


def find_cases(base_seed=None, trial=None, method=None, output_dir="overlapping_packings"):
    """Find cases matching filters."""
    cases = list_all_cases(output_dir)
    
    if not cases:
        return []

    return filter_cases(cases, base_seed=base_seed, trial=trial, method=method)


def filter_cases(cases, base_seed=None, trial=None, method=None):
    """Apply base-seed, trial, and method filters to an existing case list."""
    filtered = cases

    if base_seed is not None:
        filtered = [c for c in filtered if str(c["base_seed"]) == str(base_seed)]

    if trial is not None:
        filtered = [c for c in filtered if str(c["trial"]) == str(trial)]

    if method is not None:
        filtered = [c for c in filtered if c["method"].lower() == method.lower()]

    return filtered


def load_case(case_name, output_dir="overlapping_packings"):
    """Load a specific case and return DCELs."""
    packing_file = os.path.join(output_dir, f"{case_name}_packing.pkl")
    unfolding_file = os.path.join(output_dir, f"{case_name}_unfolding.pkl")
    
    if not os.path.exists(packing_file) or not os.path.exists(unfolding_file):
        print(f"Case files not found: {case_name}")
        return None, None
    
    try:
        with open(packing_file, 'rb') as f:
            packing = pickle.load(f)
        packing.markIndices()
        
        with open(unfolding_file, 'rb') as f:
            unfolding = pickle.load(f)
        unfolding.markIndices()
        
        return packing, unfolding
    except Exception as e:
        print(f"Error loading case {case_name}: {e}")
        return None, None


def load_and_verify_case(case, output_dir="overlapping_packings", visualize=False):
    """Load a case and verify overlaps match stored metadata."""
    packing, unfolding = load_case(case["name"], output_dir)
    
    if packing is None or unfolding is None:
        return None
    
    # Verify overlaps
    overlaps = find_overlapping_pairs(unfolding)
    stored_overlaps = int(case["overlaps"])
    
    print(f"\n{case['name']}")
    print("-" * 80)
    print(f"Base Seed: {case['base_seed']}")
    print(f"Trial: {case['trial']}, Method: {case['method']}")
    print(f"Packing: {len(packing.verts)} vertices, {len(packing.edges)} edges, {len(packing.faces)} faces")
    print(f"Unfolding: {len(unfolding.verts)} vertices, {len(unfolding.edges)} edges, {len(unfolding.faces)} faces")
    print(f"Overlapping pairs: {len(overlaps)} verified (stored: {stored_overlaps})")
    
    if len(overlaps) != stored_overlaps:
        print(f"  WARNING: Overlap count mismatch!")
    
    # Show first few overlapping pairs
    if overlaps:
        print(f"First 3 overlapping pairs: {overlaps[:3]}")
    
    # Visualize if requested
    if visualize:
        try:
            trial_index = int(case["trial"])
            method = case["method"]
            trial_seed_str = case["metadata"].get("Trial Seed", "0")
            trial_seed = int(trial_seed_str)
            root_idx_str = case["metadata"].get("Root vertex index", "0")
            root_idx = int(root_idx_str)
            print(f"\nVisualizing packing and unfolding...")
            print(f"  Packing has {len(packing.verts)} vertices")
            print(f"  Unfolding has {len(unfolding.verts)} vertices with root_idx={root_idx}")
            # First visualize the original spherical packing
            visualize_trial_packing(packing, trial_index, trial_seed)
            # Then visualize the unfolded plane with overlaps highlighted
            visualize_trial_unfolding(unfolding, method, trial_index, root_idx, overlaps)
        except Exception as e:
            print(f"Error during visualization: {e}")
            import traceback
            traceback.print_exc()
    
    return {
        "packing": packing,
        "unfolding": unfolding,
        "overlaps": overlaps,
        "verified": len(overlaps) == stored_overlaps,
    }


def stats_for_seed(base_seed, output_dir="overlapping_packings"):
    """Show statistics for all cases with given base_seed."""
    cases = find_cases(base_seed=base_seed, output_dir=output_dir)
    
    if not cases:
        print(f"No cases found for base_seed {base_seed}")
        return
    
    print(f"\nStatistics for base_seed {base_seed}")
    print("=" * 80)
    print(f"Total cases: {len(cases)}")
    
    overlap_counts = [int(c["overlaps"]) for c in cases]
    vert_counts = [int(c["verts"]) for c in cases]
    
    print(f"\nOverlapping pairs:")
    print(f"  Total: {sum(overlap_counts)}")
    print(f"  Average: {mean(overlap_counts):.1f}")
    print(f"  Median: {median(overlap_counts)}")
    print(f"  Range: {min(overlap_counts)} to {max(overlap_counts)}")
    
    print(f"\nPacking sizes:")
    print(f"  Average vertices: {mean(vert_counts):.1f}")
    print(f"  Median vertices: {median(vert_counts)}")
    print(f"  Range: {min(vert_counts)} to {max(vert_counts)}")
    
    # By method
    methods = {}
    for c in cases:
        method = c["method"]
        if method not in methods:
            methods[method] = {"count": 0, "overlaps": 0}
        methods[method]["count"] += 1
        methods[method]["overlaps"] += int(c["overlaps"])
    
    print(f"\nBy method:")
    for method, stats in sorted(methods.items()):
        avg = stats['overlaps'] / stats['count']
        print(f"  {method}: {stats['count']} cases, {stats['overlaps']} total overlaps (avg: {avg:.1f})")


def main():
    parser = argparse.ArgumentParser(
        description="View and analyze saved overlapping DCEL structures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--output-dir",
        default="overlapping_packings",
        help="Directory containing saved overlapping packings (default: overlapping_packings)"
    )
    
    parser.add_argument(
        "--list-all",
        action="store_true",
        help="List all saved overlapping cases"
    )
    
    parser.add_argument(
        "--base-seed",
        type=int,
        help="Filter by base seed"
    )
    
    parser.add_argument(
        "--trial",
        type=int,
        help="Filter by trial number"
    )
    
    parser.add_argument(
        "--method",
        help="Filter by unfolding method (e.g., bfs, dfs)"
    )
    
    parser.add_argument(
        "--load-all",
        action="store_true",
        help="Load and verify all matching cases"
    )
    
    parser.add_argument(
        "--load-one",
        help="Load and verify specific case by name"
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics for matching cases"
    )
    
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Visualize the overlapping unfoldings (when loading cases)"
    )
    
    args = parser.parse_args()
    
    # Default: list all if no options provided
    if not any([args.list_all, args.load_all, args.load_one, args.stats, args.visualize]):
        args.list_all = True
    
    if args.list_all:
        cases = list_all_cases(args.output_dir)
        if args.visualize:
            cases = filter_cases(
                cases,
                base_seed=args.base_seed,
                trial=args.trial,
                method=args.method,
            )
            if not cases:
                print("No cases match the filters")
                return
            print(f"\nVisualizing {len(cases)} case(s)...")
            for i, case in enumerate(cases, 1):
                print(f"\n[{i}/{len(cases)}]", end=" ")
                result = load_and_verify_case(case, args.output_dir, visualize=True)
                if not result:
                    print("  FAILED TO LOAD")
                elif not result["verified"]:
                    print("  VERIFICATION FAILED")
    
    if args.load_one:
        case_name = args.load_one
        cases = list_all_cases(args.output_dir)
        matching = [c for c in cases if c["name"] == case_name]
        if matching:
            load_and_verify_case(matching[0], args.output_dir, visualize=args.visualize)
        else:
            print(f"Case not found: {case_name}")
    
    if args.stats:
        if args.base_seed:
            stats_for_seed(args.base_seed, args.output_dir)
        else:
            print("Use --base-seed to show statistics for a specific seed")
    
    if args.load_all:
        cases = find_cases(
            base_seed=args.base_seed,
            trial=args.trial,
            method=args.method,
            output_dir=args.output_dir
        )
        
        if not cases:
            print("No cases match the filters")
            return
        
        print(f"\nLoading {len(cases)} case(s)...")
        for i, case in enumerate(cases, 1):
            print(f"\n[{i}/{len(cases)}]", end=" ")
            result = load_and_verify_case(case, args.output_dir, visualize=args.visualize)
            if not result:
                print("  FAILED TO LOAD")
            elif not result["verified"]:
                print("  VERIFICATION FAILED")


if __name__ == "__main__":
    main()
