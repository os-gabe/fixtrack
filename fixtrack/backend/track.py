import copy
from collections import deque

import numpy as np
from scipy import signal

from fixtrack.common.utils import normalize_vecs

DTYPE_TRACK_POINT = [
    ('pos', np.float64, 3),  # position vector
    ('vec', np.float64, 3),  # Heading vector
    ('det', np.bool),  # Detection flag
]


class Track(object):
    def undoable(func):
        def decorated_func(self, *args, **kwargs):
            self.undo_queue.append(self._data.copy())
            func(self, *args, **kwargs)

        return decorated_func

    default_vec = [1.0, 1.0, 0.0]
    default_vec = normalize_vecs(default_vec)

    def __init__(self, pos, vec=None, det=None, visible=True, undo_len=10):
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

        self.undo_queue = deque(maxlen=undo_len)

    def _valid_idx(self, idx):
        assert (idx >= 0) and (idx < len(self)), f"Invalid frame index {idx}"

    def undo(self):
        if len(self.undo_queue) == 0:
            return
        self._data = self.undo_queue.pop()

    def clear_undo_queue(self):
        self.undo_queue.clear()

    @undoable
    def add_det(self, idx, pos, vec=None, interp=False):
        if vec is None:
            vec = Track.default_vec

        self._valid_idx(idx)
        self["pos"][idx] = pos
        self["vec"][idx] = vec
        self["det"][idx] = True

        if interp:
            det_next = np.where(self["det"][idx + 1:])[0]
            if len(det_next) > 0:
                det_next = idx + det_next[0] + 1
                self["det"][idx:det_next] = True
                self["pos"][idx:det_next] = np.linspace(
                    self["pos"][idx], self["pos"][det_next], det_next - idx
                )
                # self["vec"][idx:det_next] = np.linspace(
                #     self["vec"][idx], self["vec"][det_next], det_next - idx
                # )
            if idx > 0:
                det_prev = np.where(self["det"][idx - 1::-1])[0]
                if len(det_prev) > 0:
                    det_prev = idx - det_prev[0] - 1
                    self["det"][det_prev:idx + 1] = True
                    self["pos"][det_prev:idx + 1] = np.linspace(
                        self["pos"][det_prev], self["pos"][idx], idx - det_prev + 1
                    )
                    # self["vec"][det_prev:idx] = np.linspace(
                    #     self["vec"][det_prev], self["vec"][idx], idx - det_prev
                    # )

    # @undoable
    def move_pos(self, idx, pos, window=500, exp=3):
        delta = pos - self["pos"][idx]
        idxf = np.arange(idx, min(len(self), idx + window))
        idxr = np.arange(max(0, idx - window), idx + 1)

        wr = np.linspace(0, 1.0, len(idxr))
        wf = np.linspace(1.0, 0, len(idxf))

        self["pos"][idxf, 0] += delta[0] * wf**3
        self["pos"][idxf, 1] += delta[1] * wf**3
        self["pos"][idxr[:-1], 0] += delta[0] * wr[:-1]**3
        self["pos"][idxr[:-1], 1] += delta[1] * wr[:-1]**3

    # @undoable
    def move_vec(self, idx, vec, window=500):
        delta = vec - self["vec"][idx]
        idxf = np.arange(idx, min(len(self), idx + window))
        idxr = np.arange(max(0, idx - window), idx + 1)

        wr = np.linspace(0, 1.0, len(idxr))
        wf = np.linspace(1.0, 0, len(idxf))

        self["vec"][idxf, 0] += delta[0] * wf**3
        self["vec"][idxf, 1] += delta[1] * wf**3
        self["vec"][idxr[:-1], 0] += delta[0] * wr[:-1]**3
        self["vec"][idxr[:-1], 1] += delta[1] * wr[:-1]**3

    @undoable
    def rem_det(self, idx):
        self._valid_idx(idx)
        self["det"][idx] = False

    @undoable
    def filter_heading(self, fps, f_cut_hz, order=2):
        det = self["det"]
        vec = self["vec"][det]
        vecf = self.filter_vec(data=vec, fps=fps, f_cut_hz=f_cut_hz, order=order)
        self["vec"][det] = vecf

    @undoable
    def filter_position(self, fps, f_cut_hz, order=2):
        det = self["det"]
        self["pos"][det] = self.filter_vec(
            data=self["pos"][det], fps=fps, f_cut_hz=f_cut_hz, order=order
        )

    @undoable
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

        self["vec"][self["det"]] = vecs[self["det"]]

    def jog_heading(self, delta, idx_a, idx_b):
        vecs = self["vec"][idx_a:idx_b]
        angs = np.arctan2(vecs[:, 1], vecs[:, 0])
        angs += delta
        vx = np.cos(angs)
        vy = np.sin(angs)
        self["vec"][idx_a:idx_b, 0] = vx
        self["vec"][idx_a:idx_b, 1] = vy

    @staticmethod
    def filter_vec(data, fps, f_cut_hz, order=1):
        """
        Low pass filter an array of values
        """
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
    def __init__(self, tracks, undo_len=10):
        n = len(tracks)
        assert n > 0, "Must provide 1 or more tracks"
        n = len(tracks[0])
        self.tracks = []
        for i, t in enumerate(tracks):
            ni = len(t)
            assert len(t) == n, f"Track {i} with len {ni} did not match track[0] with len {n}"
            self.tracks.append(t)

        self.undo_queue = deque(maxlen=undo_len)

    def _valid_idxs(self, idx_track, idx_frame):
        assert (idx_track >=
                0) and (idx_track < self.num_tracks), f"Invalid track index {idx_track}"
        self.tracks[idx_track]._valid_idx(idx_frame)

    def undo(self):
        if len(self.undo_queue) == 0:
            return
        track_idxs = self.undo_queue.pop()
        for idx in track_idxs:
            self.tracks[idx].undo()

    def clear_undo_queue(self):
        self.undo_queue.clear()
        for tk in self.tracks:
            tk.clear_undo_queue()

    def estimate_heading(self, idxs_track=None):
        if idxs_track is None:
            idxs_track = range(self.num_tracks)

        for idx in idxs_track:
            self.tracks[idx].estimate_heading()

        self.undo_queue.append(idxs_track)

    def filter_heading(self, fps, f_cut_hz, order=2, idxs_track=None):
        print("filtering", fps, f_cut_hz, order, idxs_track)
        if idxs_track is None:
            idxs_track = range(self.num_tracks)

        for idx in idxs_track:
            self.tracks[idx].filter_heading(fps, f_cut_hz=f_cut_hz, order=order)
        self.undo_queue.append(idxs_track)

    def filter_position(self, fps, f_cut_hz, order=2, idxs_track=None):
        if idxs_track is None:
            idxs_track = range(self.num_tracks)

        for idx in idxs_track:
            self.tracks[idx].filter_position(fps, f_cut_hz=f_cut_hz, order=order)
        self.undo_queue.append(idxs_track)

    def add_det(self, idx_track, idx_frame, pos, vec=None, interp=False):
        self._valid_idxs(idx_track, idx_frame)
        self.tracks[idx_track].add_det(idx=idx_frame, pos=pos, vec=vec, interp=interp)
        self.undo_queue.append([idx_track])

    def rem_det(self, idx_track, idx_frame):
        self._valid_idxs(idx_track, idx_frame)
        self.tracks[idx_track].rem_det(idx=idx_frame)
        self.undo_queue.append([idx_track])

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
        self.clear_undo_queue()

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
