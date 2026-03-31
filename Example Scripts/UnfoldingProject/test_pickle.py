import pickle
from koebe.datastructures.dcel import DCEL
from koebe.geometries.spherical2 import DiskS2

dcel = DCEL()
dcel.Vertex(dcel, data=DiskS2(1.0, 2.0, 3.0, 4.0))

# Saves to binary file
with open('my_dcel.pkl', 'wb') as f:
    pickle.dump(dcel, f)

# Loads from binary file
with open('my_dcel.pkl', 'rb') as f:
    dcel_loaded = pickle.load(f)