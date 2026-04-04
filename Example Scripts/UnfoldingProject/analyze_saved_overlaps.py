#!/usr/bin/env python3
"""
Utility script to batch analyze all saved overlapping DCEL structures.

This script helps you:
- List all saved overlapping cases
- Load and verify saved DCEL structures
- Extract statistics and metadata
- Re-analyze overlapping cases

Usage:
    python analyze_saved_overlaps.py [directory]
    
Default directory: overlapping_packings
"""

import pickle
import os
import sys
import json
from pathlib import Path
from inversive_distance import find_overlapping_pairs

def load_metadata(metadata_file):
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
        print(f"  Error reading metadata: {e}")
    return info

def analyze_case(output_dir, case_name):
    """Analyze a single overlapping case."""
    packing_file = os.path.join(output_dir, f"{case_name}_packing.pkl")
    unfolding_file = os.path.join(output_dir, f"{case_name}_unfolding.pkl")
    metadata_file = os.path.join(output_dir, f"{case_name}_metadata.txt")
    
    if not os.path.exists(packing_file) or not os.path.exists(unfolding_file):
        return None
    
    try:
        # Load DCEL structures
        with open(packing_file, 'rb') as f:
            packing = pickle.load(f)
        packing.markIndices()
        
        with open(unfolding_file, 'rb') as f:
            unfolding = pickle.load(f)
        unfolding.markIndices()
        
        # Verify overlaps
        overlaps = find_overlapping_pairs(unfolding)
        
        # Load metadata
        metadata = load_metadata(metadata_file) if os.path.exists(metadata_file) else {}
        
        return {
            "case_name": case_name,
            "packing_file": packing_file,
            "unfolding_file": unfolding_file,
            "metadata_file": metadata_file,
            "packing_size": len(packing.verts),
            "unfolding_size": len(unfolding.verts),
            "verified_overlaps": len(overlaps),
            "stored_overlaps": int(metadata.get("Number of overlapping pairs detected", "0")),
            "metadata": metadata,
            "file_sizes": {
                "packing": os.path.getsize(packing_file),
                "unfolding": os.path.getsize(unfolding_file),
            }
        }
    except Exception as e:
        print(f"  Error analyzing case: {e}")
        return None

def analyze_directory(output_dir="overlapping_packings"):
    """Analyze all overlapping cases in a directory."""
    if not os.path.exists(output_dir):
        print(f"Directory not found: {output_dir}")
        return []
    
    print(f"Scanning directory: {output_dir}")
    print("=" * 70)
    
    # Find all metadata files
    metadata_files = [f for f in os.listdir(output_dir) if f.endswith("_metadata.txt")]
    
    if not metadata_files:
        print("No saved overlapping cases found.")
        return []
    
    print(f"Found {len(metadata_files)} overlapping case(s)\n")
    
    cases = []
    for i, metadata_file in enumerate(sorted(metadata_files), 1):
        case_name = metadata_file.replace("_metadata.txt", "")
        print(f"{i}. {case_name}")
        
        case_info = analyze_case(output_dir, case_name)
        if case_info:
            cases.append(case_info)
            print(f"   Packing: {case_info['packing_size']} vertices, "
                  f"{case_info['file_sizes']['packing']/1024:.1f} KB")
            print(f"   Unfolding: {case_info['unfolding_size']} vertices, "
                  f"{case_info['file_sizes']['unfolding']/1024:.1f} KB")
            print(f"   Overlaps: {case_info['verified_overlaps']} verified "
                  f"(stored: {case_info['stored_overlaps']})")
            
            # Verify metadata integrity
            if case_info['verified_overlaps'] != case_info['stored_overlaps']:
                print(f"   WARNING: Overlap count mismatch!")
            
            if case_info['metadata']:
                trial = case_info['metadata'].get("Trial", "?")
                method = case_info['metadata'].get("Method", "?")
                seed = case_info['metadata'].get("Seed", "?")
                print(f"   Trial {trial}, Method: {method}, Seed: {seed}")
        print()
    
    return cases

def format_statistics(cases):
    """Format and display statistics across all cases."""
    if not cases:
        return
    
    print("\nStatistics")
    print("=" * 70)
    
    total_cases = len(cases)
    total_overlaps = sum(c['verified_overlaps'] for c in cases)
    total_packing_size = sum(c['packing_size'] for c in cases)
    total_file_size = sum(c['file_sizes']['packing'] + c['file_sizes']['unfolding'] 
                         for c in cases) / 1024 / 1024
    
    print(f"Total cases: {total_cases}")
    print(f"Total overlapping pairs: {total_overlaps}")
    print(f"Average overlaps per case: {total_overlaps / total_cases:.1f}")
    print(f"Average packing size: {total_packing_size / total_cases:.1f} vertices")
    print(f"Total disk space used: {total_file_size:.1f} MB")
    
    # Group by method
    methods = {}
    for case in cases:
        method = case['metadata'].get("Method", "unknown")
        if method not in methods:
            methods[method] = {"count": 0, "overlaps": 0}
        methods[method]["count"] += 1
        methods[method]["overlaps"] += case['verified_overlaps']
    
    print("\nBy method:")
    for method, stats in sorted(methods.items()):
        avg = stats['overlaps'] / stats['count']
        print(f"  {method.upper()}: {stats['count']} cases, "
              f"{stats['overlaps']} total overlaps (avg: {avg:.1f})")
    
    # Top offenders
    print("\nTop 5 highest overlap counts:")
    sorted_cases = sorted(cases, key=lambda c: c['verified_overlaps'], reverse=True)
    for i, case in enumerate(sorted_cases[:5], 1):
        trial = case['metadata'].get("Trial", "?")
        method = case['metadata'].get("Method", "?")
        overlaps = case['verified_overlaps']
        print(f"  {i}. Trial {trial} ({method}): {overlaps} overlaps")

def export_summary(cases, output_file="overlap_summary.json"):
    """Export case information to JSON for further analysis."""
    summary = {
        "total_cases": len(cases),
        "cases": []
    }
    
    for case in cases:
        summary["cases"].append({
            "name": case['case_name'],
            "trial": case['metadata'].get("Trial"),
            "method": case['metadata'].get("Method"),
            "seed": case['metadata'].get("Seed"),
            "vertices": case['packing_size'],
            "overlaps": case['verified_overlaps'],
            "packing_file": case['packing_file'],
            "unfolding_file": case['unfolding_file'],
        })
    
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nExported summary to {output_file}")

def main():
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "overlapping_packings"
    
    cases = analyze_directory(output_dir)
    
    if cases:
        format_statistics(cases)
        export_summary(cases)
        
        print("\n" + "=" * 70)
        print(f"To load a specific case:")
        print(f"  import pickle")
        print(f"  with open('{cases[0]['packing_file']}', 'rb') as f:")
        print(f"      packing = pickle.load(f)")
        print(f"  packing.markIndices()")
        print("=" * 70)

if __name__ == "__main__":
    main()
