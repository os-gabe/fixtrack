from PyQt5 import QtCore, QtWidgets

from fixtrack.frontend.canvas import VideoCanvas
from fixtrack.frontend.player_head import PlayerHeadWidget
from fixtrack.frontend.track_controls import TrackEditLayoutBar


class VideoWidget(QtWidgets.QWidget):
    def __init__(
        self,
        parent,
        fname_video=None,
        fname_track=None,
        estimate_heading=False,
        filter_heading=False,
        bgcolor="white"
    ):
        QtWidgets.QWidget.__init__(self)

        self.canvas = VideoCanvas(
            self,
            fname_video=fname_video,
            fname_track=fname_track,
            estimate_heading=estimate_heading,
            filter_heading=filter_heading,
            bgcolor=bgcolor
        )

        self.canvas.native.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.canvas.create_native()
        self.canvas.native.setParent(self)

        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        # self.scroll_area.SizeAdjustPolicy(QScrollArea.AdjustToContentsOnFirstShow)
        sp = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.scroll_area.setSizePolicy(sp)
        self.setup_track_edit_bar()

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(self.canvas.native)
        self.player_head = PlayerHeadWidget(self, self.canvas.video)
        vlayout.addWidget(self.player_head)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.scroll_area)
        hlayout.addLayout(vlayout)

        self.setLayout(hlayout)

        self.player_head.sig_frame_change.connect(self.canvas.on_frame_change)
        self.player_head.sig_frame_change.emit(0)

    def setup_track_edit_bar(self):
        self.track_edit_bar = TrackEditLayoutBar(self)
        for i in range(self.canvas.tracks.num_tracks):
            self.track_edit_bar.add_track(
                index=i, select=(i == 0), last=(i == (self.canvas.tracks.num_tracks - 1))
            )
        self.scroll_area.setWidget(self.track_edit_bar)

    def slot_marker_clicked(self, idx_track, idx_frame):
        pass

    def keyPressEvent(self, event):
        key = event.key()
        print(key)
        if key == QtCore.Qt.Key_Escape:
            QtWidgets.QApplication.quit()

        c0 = event.modifiers() == QtCore.Qt.ControlModifier
        if key == QtCore.Qt.Key_Q and c0:
            QtWidgets.QApplication.quit()

        if key == QtCore.Qt.Key_Space:
            self.player_head.toggle_play()
        elif key == QtCore.Qt.Key_Left:
            self.player_head.decr()
        elif key == QtCore.Qt.Key_Right:
            self.player_head.incr()
        elif key == QtCore.Qt.Key_C:
            self.canvas.toggle_cam()
        elif key == QtCore.Qt.Key_V:
            self.canvas.visuals["img"].visible ^= True
