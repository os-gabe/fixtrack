from PyQt5 import QtCore, QtWidgets

from fixtrack.frontend.widget import VideoWidget


class FixtrackWindow(QtWidgets.QMainWindow):
    def __init__(self, fname_video, fname_track, estimate_heading, filter_heading):
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

        #
        bgcolor = [.15, .16, .16]
        # bgcolor = [1., 1., 1.]
        self.main_widget = VideoWidget(
            self,
            fname_video=fname_video,
            fname_track=fname_track,
            estimate_heading=estimate_heading,
            filter_heading=filter_heading,
            bgcolor=bgcolor
        )
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        # self.statusBar().showMessage("FixTrack", 1000)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, "Commands", "TODO: Write instructions here")