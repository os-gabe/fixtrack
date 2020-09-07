from PyQt5 import QtCore, QtWidgets

from fixtrack.frontend.widget import VideoWidget


class FixtrackWindow(QtWidgets.QMainWindow):
    title = "Track Fixer"

    def __init__(self, fname_video, fname_track):
        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(self.title)

        bgcolor = [0.15, 0.16, 0.16]
        self.main_widget = VideoWidget(
            self, fname_video=fname_video, fname_track=fname_track, bgcolor=bgcolor
        )
        self.main_widget.mutated.connect(self.mutated)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def mutated(self, b):
        title = self.title
        if b:
            title += "*"
        self.setWindowTitle(title)
