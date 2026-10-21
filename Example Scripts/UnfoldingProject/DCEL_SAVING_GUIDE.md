# DCEL Saving Integration Guide

## Overview

Your `inversive_distance.py` now has integrated functionality to automatically save DCEL structures (both packing and unfolding) whenever overlapping circles are detected during trials. This allows you to archive problematic cases for later analysis, debugging, and reproduction.

## Quick Start

Run your trials with overlap detection enabled (default behavior):

```python
from inversive_distance import compare_methods

result = compare_methods(
    methods=["bfs", "dfs"],
    n_points=50,
    n_iterations=1000,
    trials=10,
    save_overlapping_decls=True,  # Enable DCEL saving (default: True)
    overlapping_output_dir="overlapping_packings",  # Output directory
)

# Access saved files
saved_cases = result["saved_overlapping_decls"]
print(f"Saved {len(saved_cases)} overlapping cases")
for case in saved_cases:
    print(f"  Trial {case['trial']}, Method: {case['method']}, Overlaps: {case['num_overlaps']}")
```

## Parameters

### New Parameters in `compare_methods()` and `compare_bfs_dfs()`:

- **`save_overlapping_decls`** (bool, default: `True`)
  - Enables automatic saving of DCEL structures when overlapping is detected
  - Set to `False` to disable saving

- **`overlapping_output_dir`** (str, default: `"overlapping_packings"`)
  - Directory where DCEL pickle files and metadata will be saved
  - Directory is created automatically if it doesn't exist

## File Outputs

When overlapping is detected during trial analysis, the following files are saved:

For a trial with overlapping, you'll see files like:
```
overlapping_packings/
├── trial0001_bfs_3overlaps_50verts_packing.pkl
├── trial0001_bfs_3overlaps_50verts_unfolding.pkl
└── trial0001_bfs_3overlaps_50verts_metadata.txt
```

### File Descriptions:

1. **`*_packing.pkl`**: The original spherical circle packing (DCEL) that produced overlaps
   - Useful for understanding the input geometry
   - Can be reused to test other unfolding methods

2. **`*_unfolding.pkl`**: The unfolded plane DCEL where overlaps were detected
   - Contains the problematic geometry with circle overlaps
   - Can be visualized and analyzed

3. **`*_metadata.txt`**: Human-readable metadata about the case
   - Trial number, random seed, method name
   - Number of vertices and overlapping pairs
   - Instructions for loading the DCEL files in Python

## Loading Saved DCEL Structures

### Basic Loading:

```python
import pickle

# Load the packings (input geometry)
with open("overlapping_packings/trial0001_bfs_3overlaps_50verts_packing.pkl", "rb") as f:
    packing = pickle.load(f)
packing.markIndices()

# Load the unfolding (where overlaps were detected)
with open("overlapping_packings/trial0001_bfs_3overlaps_50verts_unfolding.pkl", "rb") as f:
    unfolding = pickle.load(f)
unfolding.markIndices()
```

### Analyzing Saved Cases:

```python
import pickle
import os

# Find all saved overlapping cases
output_dir = "overlapping_packings"
saved_cases = [f for f in os.listdir(output_dir) if f.endswith("_metadata.txt")]

for metadata_file in sorted(saved_cases):
    with open(os.path.join(output_dir, metadata_file), "r") as f:
        print(f.read())
    print("-" * 60)
```

## Example: Full Workflow

```python
from inversive_distance import compare_methods, find_overlapping_pairs
import pickle

# Run trials with automatic saving of overlapping cases
result = compare_methods(
    methods=["bfs", "dfs"],
    n_points=50,
    n_iterations=1000,
    trials=100,
    save_overlapping_decls=True,
    overlapping_output_dir="my_overlapping_cases",
)

# Process all saved overlapping cases
print(f"\nFound {len(result['saved_overlapping_decls'])} overlapping cases:")

for case in result["saved_overlapping_decls"]:
    print(f"\nTrial {case['trial']}, Method: {case['method']}")
    print(f"  Seed: {case['seed']}")
    print(f"  Vertices: {case['num_verts']}")
    print(f"  Overlapping pairs: {case['num_overlaps']}")
    print(f"  Files saved:")
    print(f"    - {case['packing_file']}")
    print(f"    - {case['unfolding_file']}")
    
    # Load and re-analyze if needed
    with open(case['unfolding_file'], 'rb') as f:
        unfolding = pickle.load(f)
    
    # Verify overlaps are still detected
    overlaps = find_overlapping_pairs(unfolding)
    print(f"  Verified: {len(overlaps)} overlaps found in stored unfolding")
```

## Reproduction and Debugging

When you find an overlapping case, you can use the stored seed to reproduce it exactly:

```python
from inversive_distance import compare_methods
import pickle

# Reproduce the exact trial
result = compare_methods(
    methods=["bfs"],
    n_points=50,
    n_iterations=1000,
    trials=1,
    base_seed=1234567890,  # Use the seed from the metadata file
)

# Load the saved case to compare
with open("overlapping_packings/trial0001_bfs_3overlaps_50verts_unfolding.pkl", "rb") as f:
    original_unfolding = pickle.load(f)

# Now you can debug why overlaps occur
```

## Return Value Structure

The `compare_methods()` function now returns:

```python
{
    "methods": ["bfs", "dfs", ...],
    "base_seed": 1234567890,
    "trial_seeds": [seed1, seed2, ...],
    "runs": {method_name: [summaries...]},
    "profiles": {method_name: profile_dict},
    "saved_overlapping_decls": [
        {
            "trial": 1,
            "method": "bfs",
            "seed": 9876543210,
            "num_verts": 50,
            "num_overlaps": 3,
            "root_idx": 0,
            "packing_file": "overlapping_packings/trial0001_bfs_3overlaps_50verts_packing.pkl",
            "unfolding_file": "overlapping_packings/trial0001_bfs_3overlaps_50verts_unfolding.pkl",
            "metadata_file": "overlapping_packings/trial0001_bfs_3overlaps_50verts_metadata.txt",
        },
        # ... more cases if found
    ]
}
```

## Technical Details

### Pickle Protocol

- Uses `pickle.HIGHEST_PROTOCOL` for maximum compression and compatibility
- Should work with Python 3.7+
- DCEL objects have a `__reduce__()` method that handles serialization of circular object references

### Performance Notes

- Saving typically adds minimal overhead (~1-2ms per DCEL)
- File sizes: ~100KB-500KB depending on number of vertices
- Loading from disk is generally fast due to pickle protocol

### Disabling Saves

If you want to run trials without saving (for cleaner runs):

```python
result = compare_methods(
    methods=["bfs", "dfs"],
    n_points=50,
    n_iterations=1000,
    trials=10,
    save_overlapping_decls=False,  # Disable saving
)
```

## Integration with Batch Processing

When running large test suites, you can batch process saved overlapping cases:

```python
import pickle
import os
import json
from inversive_distance import find_overlapping_pairs, evaluate_algorithm

def analyze_saved_overlaps(output_dir="overlapping_packings"):
    """Analyze all saved overlapping cases."""
    analysis = {}
    
    for filename in os.listdir(output_dir):
        if filename.endswith("_packing.pkl"):
            base_name = filename.replace("_packing.pkl", "")
            packing_path = os.path.join(output_dir, filename)
            unfolding_path = os.path.join(output_dir, f"{base_name}_unfolding.pkl")
            
            with open(packing_path, 'rb') as f:
                packing = pickle.load(f)
            packing.markIndices()
            
            with open(unfolding_path, 'rb') as f:
                unfolding = pickle.load(f)
            unfolding.markIndices()
            
            overlaps = find_overlapping_pairs(unfolding)
            analysis[base_name] = {
                "num_overlaps": len(overlaps),
                "num_verts": len(packing.verts),
                "first_overlap_pair": overlaps[0] if overlaps else None,
            }
    
    return analysis

# Print summary
results = analyze_saved_overlaps()
print(json.dumps(results, indent=2))
```

## Troubleshooting

### "Cannot load overlapping DCEL files"

If you get pickle errors when loading:
1. Ensure you run `packing.markIndices()` and `unfolding.markIndices()` immediately after loading
2. Check that the koebe library version hasn't changed significantly
3. Verify the pickle file wasn't corrupted (check file size > 0)

### Directory Not Created

The `overlapping_output_dir` is created automatically. If files aren't being saved:
1. Check that `save_overlapping_decls=True` is set
2. Verify that overlaps are actually being detected in your trials
3. Check filesystem permissions for the working directory

### Large File Sizes

If pickle files are larger than expected:
1. This is normal - DCEL structures include all vertex/edge/face/dart data
2. Consider archiving old overlapping cases periodically
3. Only the `*_packing.pkl` and `*_unfolding.pkl` files are large; metadata files are tiny
