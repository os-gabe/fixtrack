import os

import cv2
import numpy as np

import fixtrack.common.utils as utils


class VideoReader(object):
    def __init__(self, fname, color_mode='RGB'):
        self.color_mode = color_mode.upper()
        assert self.color_mode in ['RGB', 'BGR', 'GRAY']

        self.fname = utils.expand_path(fname)
        assert os.path.exists(self.fname), f"Path '{self.fname}' does not exist."

        self.next_frame_num = 0

        self.cap = cv2.VideoCapture(self.fname)
        self.num_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.img_shape = (self.height, self.width)
        self.mean_frame = None

    def get_mean_frame(self):
        if self.mean_frame is None:
            shape = self.get_frame(0).shape
            frames = np.zeros(shape, dtype=np.float64)
            for fn in range(self.num_frames):
                frames += cv2.GaussianBlur(self.get_frame(fn), (99, 99), 0)
            self.mean_frame = (frames / self.num_frames).astype(np.uint8)
        return self.mean_frame

    def get_frame(self, frame_num, color_mode="RGB"):
        assert frame_num < self.num_frames, \
            "frame_num is %d, must be less than num_frames = %d" % (frame_num, self.num_frames)
        assert frame_num >= 0, "frame_num is %d, must be greater than zero." % frame_num

        if frame_num != self.next_frame_num:
            print("Setting CAP_PROP_POS_FRAMES to %d." % frame_num)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

        self.next_frame_num = frame_num + 1
        # print("Loading frame %d of %d." % (frame_num, self.num_frames))

        ret, frame = self.cap.read()
        if ret == 0:
            print("ERROR: couldn't load frame %d." % frame_num)
            # Returning None leads to somewhat better error messages.
            return None

        if color_mode is None:
            color_mode = self.color_mode

        if color_mode == 'GRAY':
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        elif color_mode == 'RGB':
            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, frame)

        return frame
