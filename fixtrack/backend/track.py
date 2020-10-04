import copy
from collections import deque

import numpy as np
from scipy import signal

from fixtrack.common.utils import normalize_vecs

DTYPE_TRACK_POINT = [
    ('pos', np.float64, 3),  # position vector
    ('vec', np.float64, 3),  # Heading vector
    ('det', np.bool),  # Detection flag
    ('ctr', np.bool),  # Control point boolean flag
]


class Track(object):
    def undoable(func):
        def decorated_func(self, *args, **kwargs):
            self._undo_queue.append(self._data.copy())
            func(self, *args, **kwargs)

        return decorated_func

    default_vec = [1.0, 0.0, 0.0]
    default_vec = normalize_vecs(default_vec)

    def __init__(self, pos, vec=None, det=None, visible=True, undo_len=10):
        n = len(pos)
        self.visible = visible
        self._data = np.zeros((n, ), dtype=DTYPE_TRACK_POINT)
        self._data["ctr"] = False
        self._data["pos"] = pos

        if vec is not None:
            assert vec.shape == pos.shape
            self._data["vec"] = vec
        else:
            self._data["vec"] = self.default_vec

        if det is not None:
            assert len(det) == n
            self._data["det"] = det

        self._undo_queue = deque(maxlen=undo_len)
        self._redo_queue = deque(maxlen=undo_len)

    def _valid_idx(self, idx):
        assert (idx >= 0) and (idx < len(self)), f"Invalid frame index {idx}"

    def undo(self):
        if len(self._undo_queue) == 0:
            return
        self._redo_queue.append(self._data.copy())
        self._data = self._undo_queue.pop()

    def redo(self):
        if len(self._redo_queue) == 0:
            return
        self._undo_queue.append(self._data.copy())
        self._data = self._redo_queue.pop()

    def clear_undo_queue(self):
        self._undo_queue.clear()
        self._redo_queue.clear()

    @undoable
    def add_undo_event(self):
        pass

    @undoable
    def add_det(self, idx, pos, vec=None, interp_l=False, interp_r=False, ctrl_pt=True):
        det_next = np.where(self["det"][idx + 1:])[0]
        det_prev = np.where(self["det"][idx - 1::-1])[0]

        if vec is None:
            if (len(det_prev) > 0) and (len(det_next) > 0) and interp_l and interp_r:
                print("Two way interp")
                v0 = self["pos"][idx + det_next[0] + 1] - pos
                v1 = pos - self["pos"][idx - det_prev[0] - 1]
                vec = 0.5 * (v0 + v1)
            elif (len(det_prev) > 0) and interp_l:
                print("Interp from prev")
                vec = pos - self["pos"][idx - det_prev[0] - 1]
            elif (len(det_next) > 0) and interp_r:
                print("Interp from next")
                vec = self["pos"][idx + det_next[0] + 1] - pos
            else:
                print("Using default vec")
                vec = Track.default_vec
            vec = normalize_vecs(vec)

        self._valid_idx(idx)
        self["pos"][idx] = pos
        self["vec"][idx] = vec
        self["det"][idx] = True

        if interp_r and (idx < len(self)) and (len(det_next) > 0):
            det_next = idx + det_next[0] + 1
            self["det"][idx:det_next] = True
            self["pos"][idx:det_next] = np.linspace(
                self["pos"][idx], self["pos"][det_next], det_next - idx
            )
            self["vec"][idx:det_next] = np.linspace(
                self["vec"][idx], self["vec"][det_next], det_next - idx
            )

        if interp_l and (idx > 0) and (len(det_prev) > 0):
            det_prev = idx - det_prev[0] - 1
            self["det"][det_prev:idx + 1] = True
            self["pos"][det_prev:idx + 1] = np.linspace(
                self["pos"][det_prev], self["pos"][idx], idx - det_prev + 1
            )
            self["vec"][det_prev:idx + 1] = np.linspace(
                self["vec"][det_prev], self["vec"][idx], idx - det_prev + 1
            )

        self["vec"] = normalize_vecs(self["vec"])

        self.add_ctrl_pt(idx)

    def _next_ctrl_pt(self, idx):
        m = np.where(self["ctr"])[0]
        m = m[m > idx]
        if len(m) == 0:
            return len(self) - 1
        return m[0]

    def _prev_ctrl_pt(self, idx):
        m = np.where(self["ctr"])[0]
        m = m[m < idx]
        if len(m) == 0:
            return 0
        return m[-1]

    # We can't directly make move_pos @undoable because it happens in the gui at a high rate
    def move_pos(self, idx, pos, interp_l=False, interp_r=False):
        self._valid_idx(idx)
        delta = pos - self["pos"][idx]
        self["pos"][idx] = pos

        if interp_l:
            idxr = np.arange(self._prev_ctrl_pt(idx), idx + 1)
            wr = np.linspace(0, 1.0, len(idxr))
            self["pos"][idxr[:-1], 0] += delta[0] * wr[:-1]
            self["pos"][idxr[:-1], 1] += delta[1] * wr[:-1]

        if interp_r:
            idxf = np.arange(idx, self._next_ctrl_pt(idx) + 1)
            wf = np.linspace(1.0, 0, len(idxf))
            self["pos"][idxf[1:], 0] += delta[0] * wf[1:]
            self["pos"][idxf[1:], 1] += delta[1] * wf[1:]

    # We can't directly make move_vec @undoable because it happens in the gui at a high rate
    def move_vec(self, idx, vec, interp_l=False, interp_r=False):
        self._valid_idx(idx)
        vec = normalize_vecs(vec)
        delta = vec - self["vec"][idx]
        self["vec"][idx] = vec

        if interp_l:
            idxr = np.arange(self._prev_ctrl_pt(idx), idx + 1)
            wr = np.linspace(0, 1.0, len(idxr))
            self["vec"][idxr[:-1], 0] += delta[0] * wr[:-1]
            self["vec"][idxr[:-1], 1] += delta[1] * wr[:-1]

        if interp_r:
            idxf = np.arange(idx, self._next_ctrl_pt(idx) + 1)
            wf = np.linspace(1.0, 0, len(idxf))
            self["vec"][idxf[1:], 0] += delta[0] * wf[1:]
            self["vec"][idxf[1:], 1] += delta[1] * wf[1:]

        self["vec"] = normalize_vecs(self["vec"])

    @undoable
    def rem_dets(self, idx_a, idx_b):
        self._valid_idx(idx_b)
        self._valid_idx(idx_a)
        self["det"][idx_a:idx_b] = False
        self["ctr"][idx_a:idx_b] = False

    @undoable
    def add_ctrl_pt(self, idx):
        self._valid_idx(idx)
        self["ctr"][idx] = True

    @undoable
    def rem_ctrl_pt(self, idx):
        self._valid_idx(idx)
        self["ctr"][idx] = False

    @undoable
    def rem_det(self, idx):
        self._valid_idx(idx)
        self["det"][idx] = False
        self["ctr"][idx] = False

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

    def _valid_idxs(self, idx_track, idx_frame):
        c0 = idx_track >= 0
        c1 = idx_track < self.num_tracks
        assert c0 and c1, f"Invalid track index {idx_track}"
        self.tracks[idx_track]._valid_idx(idx_frame)

    def undo(self, track_idx):
        self.tracks[track_idx].undo()

    def redo(self, track_idx):
        self.tracks[track_idx].redo()

    def add_det(self, idx_track, idx_frame, pos, vec=None, interp_l=False, interp_r=False):
        self._valid_idxs(idx_track, idx_frame)
        self.tracks[idx_track].add_det(
            idx=idx_frame, pos=pos, vec=vec, interp_l=interp_l, interp_r=interp_r
        )

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

    def link_tracks(self, idx_a, idx_b, frame_a, frame_b):
        idx_a, idx_b = sorted([idx_a, idx_b])
        # frame_a, frame_b = XXX

        assert (idx_a >= 0) and (idx_a < self.num_tracks), f"Invalid track index {idx_a}"
        assert (idx_b >= 0) and (idx_b < self.num_tracks), f"Invalid track index {idx_b}"

        olap = self.tracks[idx_a]["det"] & self.tracks[idx_b]["det"]

        ib = self.tracks[idx_b]["det"] & (~self.tracks[idx_a]["det"])

        tnew = self.tracks[idx_a].copy()
        tnew["pos"][ib] = self.tracks[idx_b]["pos"][ib]
        tnew["vec"][ib] = self.tracks[idx_b]["vec"][ib]
        tnew["ctr"][ib] = self.tracks[idx_b]["ctr"][ib]
        tnew["det"][ib] = self.tracks[idx_b]["det"][ib]
        tnew["det"][olap] = False
        tnew["ctr"][olap] = False
        self.tracks[idx_a] = tnew

        # self.rem_track(idx_b)

        return idx_b

    def break_track(self, idx_track, idx_frame):
        msg = f"Invalid track index {idx_track}"
        assert (idx_track >= 0) and (idx_track < self.num_tracks), msg
        msg = f"Invalid frame index {idx_frame}"
        assert (idx_frame >= 0) and (idx_frame < self.num_frames), msg

        track_b = self.tracks[idx_track].copy()

        self.tracks[idx_track]["det"][:idx_frame] = False
        self.tracks[idx_track]["ctr"][:idx_frame] = False

        track_b["det"][idx_frame:] = False
        track_b["ctr"][idx_frame:] = False

        self.add_track(track_b)

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
