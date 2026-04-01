import pickle
import sys

from koebe.datastructures.dcel import DCEL
from koebe.geometries.spherical2 import DiskS2

from matlab_test import build_dcel_with_gop

def profile_pickle(n_points=100, file_name='packing.pkl') -> (float, float, int):
    """
    :param n_points: number of points
    :param file_name: name of the pickle file
    :return: (float, float, int): time to pickle, time to unpickle, size in bytes
    """

    packing = build_dcel_with_gop(n_points)
    import time
    start_pickle = time.time()
    with open(file_name, 'wb') as file:
        pickle.dump(packing, file, protocol=pickle.HIGHEST_PROTOCOL)
        size = file.tell()
    stop_pickle = time.time()

    start_unpickle = time.time()
    with open(file_name, 'rb') as file:
        packing = pickle.load(file)
    stop_unpickle = time.time()
    return stop_pickle - start_pickle, stop_unpickle - start_unpickle, size




if __name__ == "__main__":
    print(profile_pickle(n_points=500))
    # dcel = DCEL()
    # dcel.Vertex(dcel, data=DiskS2(1.0, 2.0, 3.0, 4.0))
    #
    # # Saves to binary file
    # with open('my_dcel.pkl', 'wb') as f:
    #     pickle.dump(dcel, f)
    #
    # # Loads from binary file
    # with open('my_dcel.pkl', 'rb') as f:
    #     dcel_loaded = pickle.load(f)