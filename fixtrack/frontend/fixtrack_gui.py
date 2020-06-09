import time

import matplotlib
import numpy as np
from PyQt5 import QtCore, QtWidgets
from vispy import scene

from fixtrack.backend.track_reader import TrackReader
from fixtrack.backend.video_reader import VideoReader
from fixtrack.frontend.player_head import PlayerHeadWidget

# Make sure that we are using QT5
matplotlib.use('Qt5Agg')


class VideoCanvas(scene.SceneCanvas):
    def __init__(self, parent, video=None, track=None, **kwargs):
        scene.SceneCanvas.__init__(self, keys="interactive", **kwargs)
        self.unfreeze()
        self.track = TrackReader(track)
        self.video = VideoReader(video)

        # Setup the scene
        self.view = self.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(
            aspect=1, up="-z", rect=(0, 0, self.video.width, self.video.height)
        )

        self.visuals = {}
        self._parent = parent

        # Add video visual
        self.visuals["img"] = scene.visuals.Image(parent=self.view.scene)

        self.frame_num = 0

        for idx_tk, tk in enumerate(self.track.tracks):
            self.visuals[f"track_{idx_tk}"] = scene.visuals.Line(
                tk["pos"][:, :2], method="agg", width=10, parent=self.view.scene
            )

        self.visuals["markers"] = scene.visuals.Markers(parent=self.view.scene)
        self.visuals["axes"] = scene.visuals.XYZAxis(parent=self.view.scene)

        self.visuals["mouse"] = scene.visuals.Line(
            width=15, method="agg", parent=self.view.scene
        )
        self.mouse_pos = [[0.0, 0.0, 0.0]]

        self.ts = time.time()

        self.freeze()

        # self.show()

    def set_img(self, frame_num=None):
        t = time.time()
        self.ts = t
        if frame_num is not None:
            self.frame_num = frame_num
        img = self.video.get_frame(self.frame_num)

        self.frame_num += 1
        if self.frame_num >= self.video.num_frames:
            self.frame_num = 0

        self.visuals["img"].set_data(img)

        data = [tk["pos"][frame_num] for tk in self.track.tracks]
        data = np.vstack(data)

        self.visuals["markers"].set_data(data, size=15)

        tmp = np.vstack(self.mouse_pos)
        tmp[:, 2] = 50
        self.visuals["mouse"].set_data(tmp[:, :2], width=10)

        self.update()

    def on_mouse_press(self, event):
        self.mouse_pos = [self.view.camera.transform.imap(event.pos)[:3]]

    def on_mouse_release(self, event):
        pass

    def on_mouse_move(self, event):
        epos = self.view.camera.transform.imap(event.pos)[:3]
        self.mouse_pos.append(epos)

    def on_key_press(self, event):
        # Forward the Qt event to the parent
        self._parent.keyPressEvent(event._native)

    def on_key_release(self, event):
        # Forward the Qt event to the parent
        self._parent.keyReleaseEvent(event._native)


class VideoWidget(QtWidgets.QWidget):
    def __init__(self, parent, video=None, track=None, frame_rate=30.0, bgcolor="white"):
        QtWidgets.QWidget.__init__(self)

        self.canvas = VideoCanvas(self, video=video, track=track, bgcolor=bgcolor)

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
        if key == QtCore.Qt.Key_Space:
            self.player_head.toggle_play()
        else:
            pass


class FixtrackWindow(QtWidgets.QMainWindow):
    def __init__(self, video, track, frame_rate):
        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit, QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QtWidgets.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&About', self.about)

        #
        self.main_widget = VideoWidget(
            self, video=video, track=track, frame_rate=frame_rate, bgcolor="white"
        )
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        self.statusBar().showMessage("FixTrack", 10000)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, "Commands", "TODO: Write instructions here")
