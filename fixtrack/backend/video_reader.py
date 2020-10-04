import os

import cv2
import fixtrack.common.utils as utils


class VideoReader(object):
    def __init__(self, fname, color_mode='RGB'):
        self.color_mode = color_mode.upper()
        assert self.color_mode in ['RGB', 'BGR', 'GRAY']

        self.fname = utils.expand_path(fname)
        assert os.path.exists(self.fname), f"Path '{self.fname}' does not exist."

        self.next_frame_num = 0

        self.cap = cv2.VideoCapture(self.fname)
        assert self.cap.isOpened(), f"Failed to open video {fname}"

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        print(f"Loaded {fname} encoded with frame rate of {self.fps}fps")

        self.num_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.img_shape = (self.height, self.width)
        self.mean_frame = None

    def get_frame(self, frame_num, color_mode="RGB"):
        assert frame_num < self.num_frames, \
            "frame_num is %d, must be less than num_frames = %d" % (frame_num, self.num_frames)
        assert frame_num >= 0, "frame_num is %d, must be greater than zero." % frame_num

        if frame_num != self.next_frame_num:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

        self.next_frame_num = frame_num + 1

        ret, frame = self.cap.read()
        if ret == 0:
            print("ERROR: couldn't load frame %d." % frame_num)
            return None

        if color_mode is None:
            color_mode = self.color_mode

        if color_mode == 'GRAY':
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        elif color_mode == 'RGB':
            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, frame)

        return frame
