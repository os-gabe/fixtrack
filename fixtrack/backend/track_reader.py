import os

import h5py as h5
import numpy as np

import fixtrack.common.utils as utils

DTYPE_TRACK_FRAME = [
    ('pos', np.float64, 3),
]


class TrackReader(object):
    def __init__(self, fname):
        self.fname = utils.expand_path(fname)
        assert os.path.exists(self.fname), f"Path '{self.fname}' does not exist."

        self.h5 = h5.File(self.fname, mode="r")

        x, y = self.h5["X"][()], self.h5["Y"][()]
        # d = self.h5['det'].value

        assert x.shape == y.shape, "Malformed track H5 file"
        ntracks, nframes = x.shape

        tracks = []
        for i in range(ntracks):
            frames = np.empty((nframes, ), dtype=DTYPE_TRACK_FRAME)
            frames["pos"][:, 0] = x[i, :]
            frames["pos"][:, 1] = y[i, :]
            frames["pos"][:, 2] = 100
            tracks.append(frames)
        self.tracks = tracks


# tin_h5 = h5.File(tracks_src_file, 'r')
# Point = namedtuple('Point', 'x y')
# #AH: uncomment to revert
# #X = Point(tin_h5['x'].value, tin_h5['y'].value)
# X = Point(tin_h5['X'].value, tin_h5['Y'].value)
# #AH: UNCOMMENT TO GET ORIGINAL DEFINITION OF HX
# #H = Point(tin_h5['heading_x'].value, tin_h5['heading_y'].value)
# H = Point(tin_h5['HX'].value, tin_h5['HY'].value)
# #AH: ADDING ARBITRARY VALUE OF 1 TO HX AND HY
# #AH: uncomment to revert
# #H = Point(tin_h5['heading_x'].value + 1, tin_h5['heading_y'].value + 1)
# #AH: uncomment to revert
# #D = tin_h5['detected'].value
# D = tin_h5['det'].value

# #uncomment to revert
# #total_tracks = tin_h5['x'].shape[0]
# #total_frames = tin_h5['x'].shape[1]

# total_tracks = tin_h5['X'].shape[0]
# total_frames = tin_h5['X'].shape[1]

# #S_track = -1
# S_label = -1
# L = np.repeat(np.array([range(total_tracks)]), total_frames, axis=0)
# next_track_label = total_tracks
