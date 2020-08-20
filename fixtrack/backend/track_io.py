import os

import h5py as h5py
import numpy as np

import fixtrack.backend.track as tk
import fixtrack.common.utils as utils

DTYPE_TRACK_POINT = [
    ('pos', np.float64, 3),  # position vector
    ('vec', np.float64, 3),  # Heading vector
    ('det', np.bool),  # Detection flag
]


class TrackIO(object):
    @staticmethod
    def save(self, fname, overwrite=False):
        pass

    @staticmethod
    def load(fname):
        """
        Loads an H5 file and return a TrackCollection
        """
        fname = utils.expand_path(fname)

        assert os.path.exists(fname), f"Path '{fname}' does not exist."
        h5 = h5py.File(fname, mode="r")

        x, y = h5["X"][()], h5["Y"][()]

        xh, yh = h5["HX"][()], h5["HY"][()]

        assert x.shape == y.shape, "Different length x and y components in track"
        num_tracks, num_frames = x.shape

        assert xh.shape == yh.shape, "Different length x and y heading components in track"
        assert x.shape == xh.shape, "Num heading vecs does not match num position vecs"

        print(f"Loaded track file with {num_frames} frames and {num_tracks} tracks")

        d = h5["det"][()]
        tracks = []
        for track_idx in range(num_tracks):
            pos = np.hstack(
                [
                    x[track_idx, :].reshape(-1, 1),
                    y[track_idx, :].reshape(-1, 1),
                    np.zeros((num_frames, 1)),
                ]
            )
            vec = np.hstack(
                [
                    xh[track_idx, :].reshape(-1, 1),
                    yh[track_idx, :].reshape(-1, 1),
                    np.zeros((num_frames, 1)),
                ]
            )
            vec = utils.normalize_vecs(vec)
            det = d[track_idx]
            tracks.append(tk.Track(pos=pos, vec=vec, det=det))
        return tk.TrackCollection(tracks)
