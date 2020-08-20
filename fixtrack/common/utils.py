import os

import numpy as np
from matplotlib import cm

NUM_COLORS = 20
rng = np.random.RandomState(seed=0)

_colors = cm.tab20(np.linspace(0.0, 1.0, NUM_COLORS))
# rng.shuffle(_colors)


def normalize_vecs(v):
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-20)


def color_from_index(idxs):
    return _colors[np.mod(idxs, NUM_COLORS)]


def expand_path(p):
    return os.path.abspath(os.path.expanduser(p))
