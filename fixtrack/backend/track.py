import copy

import numpy as np
from scipy import signal
from fixtrack.common.utils import normalize_vecs

DTYPE_TRACK_POINT = [
    ('pos', np.float64, 3),  # position vector
    ('vec', np.float64, 3),  # Heading vector
    ('det', np.bool),  # Detection flag
]


class Track(object):
    default_vec = [1.0, 1.0, 0.0]
    default_vec = normalize_vecs(default_vec)

    def __init__(self, pos, vec=None, det=None, visible=True):
        n = len(pos)
        self.visible = visible
        self._data = np.zeros((n, ), dtype=DTYPE_TRACK_POINT)
        self._data["pos"] = pos

        if vec is not None:
            assert vec.shape == pos.shape
            self._data["vec"] = vec
        else:
            self._data["vec"] = self.default_vec

        if det is not None:
            assert len(det) == n
            self._data["det"] = det

    def _valid_idx(self, idx):
        assert (idx >= 0) and (idx < len(self)), f"Invalid frame index {idx}"

    def add_det(self, idx, pos, vec=None):
        if vec is None:
            vec = Track.default_vec

        self._valid_idx(idx)
        self["pos"][idx] = pos
        self["vec"][idx] = vec
        self["det"][idx] = True

    def rem_det(self, idx):
        self._valid_idx(idx)
        self["det"][idx] = False

    def filter_heading(self, fps, f_cut_hz, order=2):
        self["vec"] = self.filter_vec(
            data=self["vec"], fps=fps, f_cut_hz=f_cut_hz, order=order
        )

    def filter_position(self, fps, f_cut_hz, order=2):
        self["pos"] = self.filter_vec(
            data=self["pos"], fps=fps, f_cut_hz=f_cut_hz, order=order
        )

    def estimate_heading(self):
        """
        Estimate heading based on direction of travel
        """
        vecsa = np.zeros_like(self["vec"])
        vecsb = np.zeros_like(self["vec"])

        deltas = self["pos"][1:] - self["pos"][0:-1]
        vecsa[0:-1] = deltas
        vecsb[1:] = deltas

        vecsa[-1] = vecsa[-2]
        vecsb[0] = vecsb[1]

        vecs = 0.5 * (vecsa + vecsb)
        vecs = normalize_vecs(vecs)

        self["vec"] = vecs

    @staticmethod
    def filter_vec(data, fps, f_cut_hz, order=1):
        fsamp = fps
        fnyq = 0.5 * fsamp
        wn = f_cut_hz / fnyq
        b, a = signal.butter(order, wn)
        return signal.filtfilt(b, a, data, axis=0)

    @property
    def shape(self):
        return self.data.shape

    @property
    def pos(self):
        return self["pos"]

    @pos.setter
    def pos(self, p):
        self["pos"] = p

    @property
    def vec(self):
        return self["vec"]

    @vec.setter
    def vec(self, v):
        self["vec"] = v

    @property
    def det(self):
        return self["det"]

    @det.setter
    def det(self, d):
        self["det"] = d

    def copy(self):
        return copy.deepcopy(self)

    def __str__(self):
        return str(self.data)

    def __eq__(self, other):
        return np.all([np.all(self[key] == other[key]) for key in self._data.dtype.names])

    def __len__(self):
        return len(self._data)

    def __getitem__(self, i):
        return self._data[i]

    def __setitem__(self, i, val):
        self._data[i] = val


class TrackCollection(object):
    def __init__(self, tracks):
        n = len(tracks)
        assert n > 0, "Must provide 1 or more tracks"
        n = len(tracks[0])
        self.tracks = []
        for i, t in enumerate(tracks):
            ni = len(t)
            assert len(t) == n, f"Track {i} with len {ni} did not match track[0] with len {n}"
            self.tracks.append(t)

    def _valid_idxs(self, idx_track, idx_frame):
        assert (idx_track >=
                0) and (idx_track < self.num_tracks), f"Invalid track index {idx_track}"
        self.tracks[idx_track]._valid_idx(idx_frame)

    def estimate_heading(self, idxs_track=None):
        if idxs_track is None:
            idxs_track = range(self.num_tracks)

        for idx in idxs_track:
            self.tracks[idx].estimate_heading()

    def filter_heading(self, fps, f_cut_hz, order=2, idxs_track=None):
        if idxs_track is None:
            idxs_track = range(self.num_tracks)

        for idx in idxs_track:
            self.tracks[idx].filter_heading(fps, f_cut_hz=f_cut_hz, order=order)

    def filter_position(self, fps, f_cut_hz, order=2, idxs_track=None):
        if idxs_track is None:
            idxs_track = range(self.num_tracks)

        for idx in idxs_track:
            self.tracks[idx].filter_position(fps, f_cut_hz=f_cut_hz, order=order)

    def add_det(self, idx_track, idx_frame, pos, vec=None):
        self._valid_idxs(idx_track, idx_frame)
        self.tracks[idx_track].add_det(idx=idx_frame, pos=pos, vec=vec)

    def rem_det(self, idx_track, idx_frame):
        self._valid_idxs(idx_track, idx_frame)
        self.tracks[idx_track].rem_det(idx=idx_frame)

    def add_track(self, track=None):
        if track is not None:
            assert isinstance(track, Track)
            n = len(track)
            n0 = self.num_frames
            assert n == self.num_frames, f"Track has wrong number of frames {n}, expected {n0}"
        else:
            track = Track(pos=np.zeros((self.num_frames, 3)))
        self.tracks.append(track)
        return self.num_tracks - 1

    def rem_track(self, idx):
        assert (idx >= 0) and (idx < self.num_tracks), f"Invalid track index {idx}"
        self.tracks.pop(idx)

    @property
    def num_tracks(self):
        return len(self.tracks)

    @property
    def num_frames(self):
        return len(self.tracks[0])

    def __getitem__(self, i):
        return self.tracks[i]

    def __setitem__(self, i, val):
        self.tracks[i] = val
