from PyQt5 import QtCore, QtWidgets

from fixtrack.frontend.widget import VideoWidget


class FixtrackWindow(QtWidgets.QMainWindow):
    def __init__(self, fname_video, fname_track):
        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Track Fixer")

        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit, QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QtWidgets.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&About', self.about)

        bgcolor = [0.15, 0.16, 0.16]
        self.main_widget = VideoWidget(
            self, fname_video=fname_video, fname_track=fname_track, bgcolor=bgcolor
        )
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, "Commands", "TODO: Write instructions here")
