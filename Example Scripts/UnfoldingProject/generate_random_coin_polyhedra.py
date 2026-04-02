import os
import pickle

from matlab_packing_generation import build_dcel_with_gop

if __name__ == "__main__":

    current_dir = os.getcwd()
    child_path = os.path.join(current_dir, "TestSuite")
    os.chdir(child_path)

    for n_points in range(10, 210, 10):
        packing = build_dcel_with_gop(n_points)
        file_name = f"random_coin_polyhedra_{n_points}.pkl"
        with open(file_name, 'wb') as file:
            pickle.dump(packing, file, protocol=pickle.HIGHEST_PROTOCOL)

