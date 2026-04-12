#!/usr/bin/env python3
"""
Example: Using DCEL saving to track overlapping coin packings.

This script demonstrates how to:
1. Run trials with automatic DCEL saving for overlapping cases
2. Load and analyze saved DCEL structures
3. Reproduce overlapping cases using seeds

Run this from the UnfoldingProject directory:
    python example_save_overlapping_decls.py
"""

import pickle
import os
from inversive_distance import compare_methods, find_overlapping_pairs

def main():
    print("=" * 70)
    print("Example: DCEL Saving Integration")
    print("=" * 70)
    
    # Run trials with DCEL saving enabled (default)
    print("\n1. Running trials with DCEL saving enabled...")
    print("-" * 70)
    
    result = compare_methods(
        methods=["bfs", "dfs"],
        n_points=50,
        n_iterations=1000,
        trials=250,
        pair_scope="all",
        include_tree_edges=False,
        save_overlapping_decls=True,
        overlapping_output_dir="overlapping_packings_demo",
    )
    
    # Summary of results
    print("\n2. Results Summary")
    print("-" * 70)
    
    saved_cases = result.get("saved_overlapping_decls", [])
    
    if not saved_cases:
        print("No overlapping cases detected in these trials.")
        print("(This is expected with a high iteration count; try lower n_iterations)")
        return
    
    print(f"Found {len(saved_cases)} overlapping case(s):\n")
    
    for i, case in enumerate(saved_cases, 1):
        print(f"Case {i}:")
        print(f"  Trial Number: {case['trial']}")
        print(f"  Unfolding Method: {case['method']}")
        print(f"  Random Seed: {case['seed']}")
        print(f"  Vertices: {case['num_verts']}")
        print(f"  Overlapping Pairs: {case['num_overlaps']}")
        print(f"  Root Vertex Index: {case['root_idx']}")
        print(f"  Files:")
        print(f"    Packing: {case['packing_file']}")
        print(f"    Unfolding: {case['unfolding_file']}")
        print()
    
    # Load and analyze the first saved case
    if saved_cases:
        print("\n3. Loading and Analyzing First Saved Case")
        print("-" * 70)
        
        first_case = saved_cases[0]
        print(f"Loading case from trial {first_case['trial']} ({first_case['method']})...\n")
        
        # Load packing
        with open(first_case['packing_file'], 'rb') as f:
            packing = pickle.load(f)
        packing.markIndices()
        
        # Load unfolding
        with open(first_case['unfolding_file'], 'rb') as f:
            unfolding = pickle.load(f)
        unfolding.markIndices()
        
        print(f"Packing loaded: {len(packing.verts)} vertices")
        print(f"Unfolding loaded: {len(unfolding.verts)} vertices")
        
        # Verify overlaps
        overlaps = find_overlapping_pairs(unfolding)
        print(f"Verified: {len(overlaps)} overlapping pairs found in unfolding")
        
        if overlaps:
            print(f"First overlapping pair: {overlaps[0]}")
            print(f"Last overlapping pair: {overlaps[-1]}")
        
        # Display metadata
        print(f"\nMetadata file: {first_case['metadata_file']}")
        print("\nMetadata content:")
        print("-" * 70)
        with open(first_case['metadata_file'], 'r') as f:
            print(f.read())
        print("-" * 70)
        
        # Show how to reproduce this exact case
        print("\n4. How to Reproduce This Case")
        print("-" * 70)
        print(f"To reproduce this exact trial, use:")
        print(f"  result = compare_methods(")
        print(f"      methods=['{first_case['method']}'],")
        print(f"      n_points={first_case['num_verts']},")
        print(f"      n_iterations=1000,")
        print(f"      trials=1,")
        print(f"      base_seed={first_case['seed']},")
        print(f"  )")
        
    # Summary statistics
    print("\n5. Statistics")
    print("-" * 70)
    
    methods = {}
    for case in saved_cases:
        method = case['method']
        if method not in methods:
            methods[method] = {"trials": 0, "total_overlaps": 0}
        methods[method]["trials"] += 1
        methods[method]["total_overlaps"] += case['num_overlaps']
    
    for method, stats in methods.items():
        avg_overlaps = stats['total_overlaps'] / stats['trials']
        print(f"{method.upper()}: {stats['trials']} overlapping trial(s), "
              f"{stats['total_overlaps']} total overlapping pairs "
              f"(avg: {avg_overlaps:.1f} per trial)")
    
    print("\n" + "=" * 70)
    print("Example completed!")
    print(f"Check the 'overlapping_packings_demo/' directory for saved DCEL files")
    print("=" * 70)


if __name__ == "__main__":
    main()
