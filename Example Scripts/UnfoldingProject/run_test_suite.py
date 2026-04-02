import json
import os
import pickle
import time

from join_unfolding_algorithms import *
from unfolding_testing import inversive_distances_test


if __name__ == "__main__":
    current_dir = os.getcwd()
    child_path = os.path.join(current_dir, "TestSuite")
    os.chdir(child_path)

    join_algorithms = [depth_first_search_unfolding, shortest_paths_unfolding,
                       min_degree_shortest_paths_unfolding, max_degree_shortest_paths_unfolding,
                       shortest_shortest_paths_unfolding, longest_shortest_paths_unfolding,
                       normal_order_unfolding]

    # join_algorithms = [depth_first_search_unfolding]

    failure_map: dict[str, list[str]] = {}
    for join_algorithm in join_algorithms:
        failure_map[join_algorithm.__name__] = []

    packing_files: list[str] = []

    for file_name in os.listdir(child_path):
        if file_name.endswith(".pkl"):
            packing_files.append(file_name)

    start_test = time.time()
    for file_name in packing_files:
        packing: DCEL
        with open(file_name, 'rb') as file:
            packing = pickle.load(file)
            packing.markIndices()
        for join_algorithm in join_algorithms:
            unfolding, _ = join_algorithm(packing)
            passed = inversive_distances_test(unfolding, packing)
            if not passed:
                failure_map[join_algorithm.__name__].append(file_name)
    end_test = time.time()
    elapsed_time = end_test - start_test
    print(f"tested {len(packing_files)} packings with {len(join_algorithms)} algorithms in {elapsed_time} seconds")


    with open("results.json", "w") as file:
        json.dump(failure_map, file, indent=4, sort_keys=True)

