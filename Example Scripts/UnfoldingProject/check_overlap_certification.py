"""
overlapping_packings/ gets a packing+unfolding+metadata.txt saved for every
RAW overlap (num_overlappings > 0), not just CERTIFIED ones -- so a saved
file alone doesn't tell you whether it's a real overlap or packing-noise.
This cross-references each saved metadata.txt against the trial CSV (joined
on trial_seed + method, which metadata.txt and the CSV both record) to label
it REAL / NOISE, so you don't have to open a single .pkl to know which ones
are worth double-checking by hand.

Usage:
    python check_overlap_certification.py [overlapping_packings_dir] [csv1.csv csv2.csv ...]

With no args, scans ./overlapping_packings/ against every *_trials.csv found
under ./scaling_sweep_data/ and ./n_points_data/.
"""

import csv
import glob
import os
import re
import sys


def load_csv_index(csv_paths):
    """Map (trial_seed, method) -> trial CSV row, across all given CSVs.

    Only CSVs with a num_overlappings_certified column are usable -- older,
    pre-audit CSVs lack it entirely and can't tell you certified vs noise.
    """
    index = {}
    for path in csv_paths:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            if "num_overlappings_certified" not in (reader.fieldnames or []):
                print(f"(skipping {path}: pre-audit CSV, no certified-overlap column)")
                continue
            for row in reader:
                key = (row["trial_seed"], row["method"])
                index[key] = row
    return index


def parse_metadata(path):
    text = open(path).read()
    trial_seed = re.search(r"Trial Seed:\s*(\S+)", text).group(1)
    method = re.search(r"Method:\s*(\S+)", text).group(1)
    n_verts = re.search(r"Number of vertices:\s*(\S+)", text).group(1)
    raw_pairs = re.search(r"Number of overlapping pairs detected:\s*(\S+)", text).group(1)
    return trial_seed, method, n_verts, raw_pairs


def main():
    args = sys.argv[1:]
    overlap_dir = args[0] if args and not args[0].endswith(".csv") else "overlapping_packings"
    csv_args = [a for a in args if a.endswith(".csv")]
    csv_paths = csv_args if csv_args else (
        glob.glob("scaling_sweep_data/*_trials.csv") + glob.glob("n_points_data/*.csv")
    )

    if not csv_paths:
        print("No trial CSVs found -- pass them explicitly.")
        return

    index = load_csv_index(csv_paths)
    metadata_files = sorted(glob.glob(os.path.join(overlap_dir, "*_metadata.txt")))

    if not metadata_files:
        print(f"No metadata files found in {overlap_dir}/")
        return

    real_count = 0
    skipped = 0
    print(f"{'file':<70} {'method':<24} {'n':>6} {'raw':>4} {'certified':>10} {'deficit':>12} {'residual':>12} {'ratio':>8}")
    for path in metadata_files:
        trial_seed, method, n_verts, raw_pairs = parse_metadata(path)
        row = index.get((trial_seed, method))
        base = os.path.basename(path).replace("_metadata.txt", "")

        if row is None:
            skipped += 1  # legacy file from before save_trial_data tracked this run's seeds
            continue

        certified = int(row["num_overlappings_certified"]) > 0
        deficit = 1.0 - float(row["min_plane"])
        residual = float(row["packing_residual"])
        ratio = deficit / residual if residual else float("inf")
        label = "REAL" if certified else "noise"
        if certified:
            real_count += 1

        print(f"{base:<70} {method:<24} {n_verts:>6} {raw_pairs:>4} {label:>10} {deficit:>12.3e} {residual:>12.3e} {ratio:>8.2f}x")

    matched = len(metadata_files) - skipped
    print(f"\n{real_count} of {matched} matched saved files are CERTIFIED overlaps; the rest are packing noise.")
    if skipped:
        print(f"({skipped} older file(s) skipped -- no matching trial_seed in the loaded CSVs, likely pre-audit runs.)")


if __name__ == "__main__":
    main()
