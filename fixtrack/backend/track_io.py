import os

import h5py as h5py
import numpy as np

import fixtrack.backend.track as tk
import fixtrack.common.utils as utils

# DTYPE_TRACK_POINT = [
#     ('pos', np.float64, 3),  # position vector
#     ('vec', np.float64, 3),  # Heading vector
#     ('det', np.bool),  # Detection flag
# ]


class TrackIO(object):
    @staticmethod
    def save(fname, tracks):
        """
        Takes a TrackCollection and saves it to an h5 file
        """
        fname = utils.expand_path(fname)
        num_frames = tracks.num_frames
        num_tracks = tracks.num_tracks

        with h5py.File(fname, mode="w") as h5:
            h5.create_dataset("X", shape=(num_tracks, num_frames), dtype=np.float32)
            h5.create_dataset("Y", shape=(num_tracks, num_frames), dtype=np.float32)
            h5.create_dataset("HX", shape=(num_tracks, num_frames), dtype=np.float32)
            h5.create_dataset("HY", shape=(num_tracks, num_frames), dtype=np.float32)
            h5.create_dataset("det", shape=(num_tracks, num_frames), dtype=np.uint8)

            h5["X"][()] = np.vstack([tk["pos"][:, 0] for tk in tracks])
            h5["Y"][()] = np.vstack([tk["pos"][:, 1] for tk in tracks])
            h5["HX"][()] = np.vstack([tk["vec"][:, 0] for tk in tracks])
            h5["HY"][()] = np.vstack([tk["vec"][:, 1] for tk in tracks])
            h5["det"][()] = np.vstack([tk["det"] for tk in tracks])

    @staticmethod
    def blank(num_frames):
        pos = np.zeros((num_frames, 3))
        tracks = [tk.Track(pos=pos)]
        return tk.TrackCollection(tracks)

    @staticmethod
    def load(fname):
        """
        Loads an H5 file and return a TrackCollection
        """
        fname = utils.expand_path(fname)

        assert os.path.exists(fname), f"Path '{fname}' does not exist."
        with h5py.File(fname, mode="r") as h5:

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
