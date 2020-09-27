import os

from fixtrack.frontend.widget import VideoWidget
from PyQt5 import QtCore, QtWidgets


class FixtrackWindow(QtWidgets.QMainWindow):
    title = "Track Fixer"

    def __init__(self, fname_video, fname_track, range_slider=True):
        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(self.title)
        self.statusBar().showMessage(os.path.split(fname_video)[1])

        bgcolor = [0.09, 0.09, 0.11]
        self.main_widget = VideoWidget(
            self,
            fname_video=fname_video,
            fname_track=fname_track,
            range_slider=range_slider,
            bgcolor=bgcolor
        )
        self.main_widget.mutated.connect(self.mutated)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        # self.main_widget.show_msg.connect(self.statusBar().showMessage)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def mutated(self, b):
        title = self.title
        if b:
            title += "*"
        self.setWindowTitle(title)
