from PyQt5 import QtCore, QtWidgets

from fixtrack.frontend.canvas import VideoCanvas
from fixtrack.frontend.player_head import PlayerHeadWidget


class VideoWidget(QtWidgets.QWidget):
    def __init__(
        self,
        parent,
        video=None,
        track=None,
        estimate_heading=False,
        frame_rate=30.0,
        bgcolor="white"
    ):
        QtWidgets.QWidget.__init__(self)

        self.canvas = VideoCanvas(
            self, video=video, track=track, estimate_heading=estimate_heading, bgcolor=bgcolor
        )

        self.canvas.native.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.canvas.create_native()
        self.canvas.native.setParent(self)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.canvas.native)

        self.player_head = PlayerHeadWidget(self, self.canvas.video, 1.0 / frame_rate)
        self.layout.addWidget(self.player_head)

        self.player_head.sig_frame_change.connect(self.canvas.set_img)

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
        elif key == QtCore.Qt.Key_0:
            self.canvas.cam_track = 0
        elif key == QtCore.Qt.Key_1:
            self.canvas.cam_track = 1
        elif key == QtCore.Qt.Key_2:
            self.canvas.cam_track = 2
        elif key == QtCore.Qt.Key_3:
            self.canvas.cam_track = 3
        elif key == QtCore.Qt.Key_4:
            self.canvas.cam_track = 4
        elif key == QtCore.Qt.Key_5:
            self.canvas.cam_track = 5
        elif key == QtCore.Qt.Key_6:
            self.canvas.cam_track = 6
        # elif key == QtCore.Qt.Key_X:
        #     # self.visuals[f"track_edit{idx_tk}"]
        #     for i in range(self.canvas.track.num_tracks):
        #         self.canvas.visuals[f"track_edit{i}"].visible ^= True
        else:
            pass
