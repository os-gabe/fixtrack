import os

import h5py as h5
import numpy as np

import fixtrack.common.utils as utils

DTYPE_TRACK_FRAME = [
    ('pos', np.float64, 3),  # position vector
    ('vec', np.float64, 3),  # Heading vector
    ('det', np.int),  # Detection flag
    # ('col', np.float64, 4),  # RGBA Color
]


class TrackReader(object):
    def __init__(self, fname, estimate_heading=False):
        self.fname = utils.expand_path(fname)
        assert os.path.exists(self.fname), f"Path '{self.fname}' does not exist."

        self.h5 = h5.File(self.fname, mode="r")

        x, y = self.h5["X"][()], self.h5["Y"][()]

        xh, yh = self.h5["HX"][()], self.h5["HY"][()]

        assert x.shape == y.shape, "Different length x and y components in track"
        self.num_tracks, self.num_frames = x.shape

        assert xh.shape == yh.shape, "Different length x and y heading components in track"
        assert x.shape == xh.shape, "Num heading vecs does not match num lenposition vecs"

        det = self.h5["det"][()]

        tracks = []
        for i in range(self.num_tracks):
            frames = np.empty((self.num_frames, ), dtype=DTYPE_TRACK_FRAME)
            frames["pos"][0:, 0] = x[i, :]
            frames["pos"][0:, 1] = y[i, :]
            frames["pos"][0:, 2] = 0.0

            frames["vec"][0:, 0] = xh[i, :]
            frames["vec"][0:, 1] = yh[i, :]
            frames["vec"][0:, 2] = 0.0

            frames["det"] = det[i]

            # frames["col"][:, 3] = det[i]

            tracks.append(frames)

        self.tracks = tracks

        if estimate_heading:
            self.estimate_heading()

    def estimate_heading(self):
        for track in self.tracks:
            track["vec"] = self.heading_from_track(track)

    @staticmethod
    def heading_from_track(track):
        # dxs = np.diff(track[:, 0])
        # dys = np.diff(track[:, 1])
        vecsa = np.zeros_like(track["vec"])
        vecsb = np.zeros_like(track["vec"])

        deltas = track["pos"][1:] - track["pos"][0:-1]
        vecsa[0:-1] = deltas
        vecsb[1:] = deltas

        vecsa[-1] = vecsa[-2]
        vecsb[0] = vecsb[1]

        vecs = 0.5 * (vecsa + vecsb)
        vecs = vecs / (np.linalg.norm(vecs, axis=-1, keepdims=True) + 1e-20)
        return vecs
