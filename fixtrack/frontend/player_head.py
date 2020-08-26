import os

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from fixtrack.frontend.range_slider import RangeSlider


class PlayerHeadWidget(QtWidgets.QWidget):
    sig_frame_change = QtCore.pyqtSignal(int)

    fname_play = os.path.join(os.path.dirname(__file__), "icons", "play.svg")
    fname_skip_ahead = os.path.join(os.path.dirname(__file__), "icons", "skip-forward.svg")
    fname_skip_back = os.path.join(os.path.dirname(__file__), "icons", "skip-back.svg")
    fname_pause = os.path.join(os.path.dirname(__file__), "icons", "pause.svg")

    def __init__(self, parent, video_reader):
        QtWidgets.QWidget.__init__(self, parent)

        self.dt = 1.0 / video_reader.fps
        self._playing = False

        self.video_reader = video_reader

        self._ids = [i for i in range(self.video_reader.num_frames)]

        self._id_2_idx = {i: i for i in self._ids}
        self._frame_num = self._ids[0]
        self._frame_idx = self._id_2_idx[self._frame_num]
        self._idx_sel_a = self._ids[0]
        self._idx_sel_b = self._ids[-1]

        self.play_button = QtWidgets.QToolButton(self.parent())
        self.icon_play = QtGui.QIcon(QtGui.QPixmap(self.fname_play))
        self.icon_pause = QtGui.QIcon(QtGui.QPixmap(self.fname_pause))
        self.play_button.setIcon(self.icon_play)
        self.play_button.clicked.connect(self.cb_play)
        self.play_button.setToolTip("Start/stop playback")

        self.frame_text = QtWidgets.QLineEdit(str(self.frame_num))
        self.cb_slider_text(self.frame_idx, resize=True)
        self.frame_text.setReadOnly(True)
        self.frame_text.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
        )

        nextButton = QtWidgets.QToolButton(self.parent())
        nextButton.setIcon(QtGui.QIcon(QtGui.QPixmap(self.fname_skip_ahead)))
        nextButton.clicked.connect(self.cb_last)
        nextButton.setToolTip("Skip to last frame")

        prevButton = QtWidgets.QToolButton(self.parent())
        prevButton.setIcon(QtGui.QIcon(QtGui.QPixmap(self.fname_skip_back)))
        prevButton.clicked.connect(self.cb_first)
        prevButton.setToolTip("Skip to first frame")

        self.play_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.play_slider.setRange(0, self.num_frames - 1)
        self.play_slider.sliderMoved.connect(self.cb_play_slider)
        self.play_slider.sliderReleased.connect(self.cb_play_slider)
        self.play_slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.play_slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)

        self.start_slider = RangeSlider(self.play_slider)
        self.start_slider.setRangeLimit(0, self.num_frames - 1)
        self.start_slider.setRange(0, self.num_frames - 1)
        self.start_slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.start_slider.setTickPosition(QtWidgets.QSlider.NoTicks)
        self.start_slider.setTickInterval(0)
        self.start_slider.sliderMoved.connect(self.cb_start_slider)

        self.rate_box = QtWidgets.QComboBox()
        self.rate_box.addItem("1/8x  ", QtCore.QVariant(1.0 / 8.0))
        self.rate_box.addItem("1/4x  ", QtCore.QVariant(1.0 / 4.0))
        self.rate_box.addItem("1/2x  ", QtCore.QVariant(1.0 / 2.0))
        self.rate_box.addItem("1x  ", QtCore.QVariant(1.0))
        self.rate_box.addItem("2x  ", QtCore.QVariant(2.0))
        self.rate_box.setFocusPolicy(QtCore.Qt.NoFocus)
        self.rate_box.setCurrentIndex(3)
        self.rate_box.activated.connect(self.cb_update_rate)
        self.rate_box.setToolTip("Change playback speed")

        lh = QtWidgets.QHBoxLayout()
        lv = QtWidgets.QVBoxLayout()

        lh.addWidget(self.frame_text)
        lh.addWidget(prevButton)
        lh.addWidget(self.play_button)
        lh.addWidget(nextButton)
        lh.addWidget(self.rate_box)
        lh.addStretch()
        lv.addLayout(lh)
        lv.addWidget(self.play_slider)
        lv.addWidget(self.start_slider)

        self.setLayout(lv)

        self.interval = self.dt * 1000 / self.rate_box.currentData()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.cb_timeout)

    def cb_last(self):
        self.cb_stop()
        self.cb_play_slider(self._ids[-1])
        self.play_slider.blockSignals(True)
        self.play_slider.setValue(self.frame_num)
        self.play_slider.blockSignals(False)

    def cb_first(self):
        self.cb_stop()
        self.cb_play_slider(self._ids[0])
        self.play_slider.blockSignals(True)
        self.play_slider.setValue(self.frame_num)
        self.play_slider.blockSignals(False)

    def cb_slider_text(self, idx, resize=False):
        def resize_frame_text_to_fit(self):
            text = self.frame_text.text()
            font = QtGui.QFont("", 0)
            fm = QtGui.QFontMetrics(font)
            pixelsWide = fm.width(text)
            pixelsHigh = fm.height()
            self.frame_text.setFixedSize(pixelsWide, pixelsHigh)

        msg = f"{idx:04d}/{self._ids[-1]:04d} [{self._idx_sel_a:04d}, {self._idx_sel_b:04d}]"
        self.frame_text.setText(msg)
        if resize:
            resize_frame_text_to_fit(self)

    def cb_play_slider(self, frame_num=None):
        if frame_num is None:
            frame_num = self.play_slider.value()
        self.cb_stop()
        self.set_frame_num(frame_num)

    def cb_start_slider(self, idx_a, idx_b, handle):
        self.cb_stop()
        self._idx_sel_a = idx_a
        self._idx_sel_b = idx_b
        if (self.frame_num < idx_a) or (handle == 0):
            self.set_frame_num(idx_a)
        elif (self.frame_num > idx_b) or (handle == 1):
            self.set_frame_num(idx_b)

    def toggle_play(self):
        if self._playing:
            self.cb_stop()
        else:
            self.cb_play()

    def cb_play(self):
        if self._playing:
            self.cb_stop()
        else:
            self.timer.start(self.interval)
            self.play_button.setIcon(self.icon_pause)
            self._playing = True

    def cb_stop(self):
        self.timer.stop()
        self.play_button.setIcon(self.icon_play)
        self._playing = False

    def cb_timeout(self):
        if self.frame_idx < self.num_frames - 1:
            self.incr()
            self.play_slider.setValue(self.frame_num)
        else:
            self.cb_stop()

    def cb_update_rate(self):
        running = self.timer.isActive()
        self.timer.stop()
        self.interval = self.dt * 1000 / self.rate_box.currentData()
        if running:
            self._playing = False
            self.cb_play()

    @property
    def num_frames(self):
        return len(self._ids)

    @property
    def frame_num(self):
        return self._frame_num

    @property
    def frame_idx(self):
        return self._frame_idx

    def incr(self, emit=True):
        self.jog(1, emit)

    def decr(self, emit=True):
        self.jog(-1, emit)

    def jog(self, delta, emit=True):
        self._frame_idx = np.clip(self._frame_idx + delta, 0, self.num_frames - 1)
        self._frame_num = self._ids[self._frame_idx]
        self._set_frame(emit)

    def _set_frame(self, emit):
        self.cb_slider_text(self._frame_num)
        self.play_slider.blockSignals(True)
        self.play_slider.setValue(self.frame_num)
        self.play_slider.blockSignals(False)
        if emit:
            self.sig_frame_change.emit(self._frame_idx)

    def set_frame_idx(self, n, emit=True):
        assert n >= 0 and n < self.num_frames
        if n == self._frame_idx:
            return
        self._frame_idx = n
        self._frame_num = self._ids[self._frame_idx]

        self._set_frame(emit)

    def set_frame_num(self, n, emit=True):
        assert n in self._ids
        if n == self._frame_num:
            print("Already on frame num %d" % (n))
            return
        self._frame_num = n
        self._frame_idx = self._id_2_idx[self._frame_num]

        self._set_frame(emit)
