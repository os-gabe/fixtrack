import numpy as np
from PyQt5 import QtCore, QtWidgets


class PlayerHeadWidget(QtWidgets.QWidget):
    sig_frame_change = QtCore.pyqtSignal(int)

    def __init__(self, parent, video_reader, dt=0.5):
        QtWidgets.QWidget.__init__(self, parent)

        self.dt = dt
        self._playing = False

        self.video_reader = video_reader

        self._ids = [i for i in range(self.video_reader.num_frames)]

        self._id_2_idx = {i: i for i in self._ids}
        self._frame_num = self._ids[0]
        self._frame_idx = self._id_2_idx[self._frame_num]

        self.play_button = QtWidgets.QToolButton(self.parent())
        self.play_button.setIcon(
            self.parent().style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        )
        self.play_button.clicked.connect(self.cb_play)
        self.play_button.setToolTip("Start/stop playback")

        self.frame_text = QtWidgets.QLineEdit(str(self.frame_num))
        self.frame_text.setReadOnly(True)
        self.frame_text.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
        )

        nextButton = QtWidgets.QToolButton(self.parent())
        nextButton.setIcon(
            self.parent().style().standardIcon(QtWidgets.QStyle.SP_MediaSkipForward)
        )
        nextButton.clicked.connect(self.cb_last)
        nextButton.setToolTip("Skip to last frame")

        prevButton = QtWidgets.QToolButton(self.parent())
        prevButton.setIcon(
            self.parent().style().standardIcon(QtWidgets.QStyle.SP_MediaSkipBackward)
        )
        prevButton.clicked.connect(self.cb_first)
        prevButton.setToolTip("Skip to first frame")

        self.play_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.play_slider.setRange(0, self.num_frames - 1)
        self.play_slider.sliderMoved.connect(self.cb_slider_text)
        self.play_slider.sliderReleased.connect(self.cb_slider)
        self.play_slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.play_slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)

        self.rate_box = QtWidgets.QComboBox()

        self.rate_box.addItem("1/8x  ", QtCore.QVariant(1.0 / 8.0))
        self.rate_box.addItem("1/6x  ", QtCore.QVariant(1.0 / 6.0))
        self.rate_box.addItem("1/4x  ", QtCore.QVariant(1.0 / 4.0))
        self.rate_box.addItem("1/2x  ", QtCore.QVariant(1.0 / 2.0))
        self.rate_box.addItem("1x  ", QtCore.QVariant(1.0))
        self.rate_box.addItem("2x  ", QtCore.QVariant(2.0))
        self.rate_box.addItem("4x  ", QtCore.QVariant(4.0))
        self.rate_box.addItem("6x  ", QtCore.QVariant(6.0))
        self.rate_box.addItem("8x  ", QtCore.QVariant(8.0))
        self.rate_box.setCurrentIndex(4)
        self.rate_box.activated.connect(self.cb_update_rate)
        self.rate_box.setToolTip("Change playback speed")

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.frame_text)
        layout.addWidget(prevButton)
        layout.addWidget(self.play_button)
        layout.addWidget(nextButton)
        layout.addWidget(self.play_slider)
        layout.addWidget(self.rate_box)
        self.setLayout(layout)

        self.interval = self.dt * 1000 / self.rate_box.currentData()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.cb_timeout)

    def set_frame_id_to_idx_dict(self, d):
        self._id_2_idx = d
        self._ids = [k for k in self._id_2_idx]
        self.play_slider.setRange(self._ids[0], self._ids[-1])

        self._frame_num = self._ids[np.argmin(np.abs(np.array(self._ids) - self._frame_num))]
        self._frame_idx = self._id_2_idx[self._frame_num]
        self._set_frame(True)

    def cb_last(self):
        self.cb_stop()
        self.cb_slider(self._ids[-1])
        self.play_slider.blockSignals(True)
        self.play_slider.setValue(self.frame_num)
        self.play_slider.blockSignals(False)

    def cb_first(self):
        self.cb_stop()
        self.cb_slider(self._ids[0])
        self.play_slider.blockSignals(True)
        self.play_slider.setValue(self.frame_num)
        self.play_slider.blockSignals(False)

    def cb_slider_text(self, idx):
        msg = "%0" + str(len("%d" % self.num_frames)
                         ) + "d/" + "[%d, %d]" % (self._ids[0], self._ids[-1])
        self.frame_text.setText(msg % (idx))

    def cb_slider(self, frame_num=None):
        if frame_num is None:
            frame_num = self.play_slider.value()
        self.cb_stop()
        self.set_frame_num(frame_num)

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
            self.play_button.setIcon(
                self.parent().style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
            )
            self._playing = True

    def cb_stop(self):
        self.timer.stop()
        self.play_button.setIcon(
            self.parent().style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        )
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
