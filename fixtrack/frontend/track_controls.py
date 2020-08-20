import os

import numpy as np
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QButtonGroup, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QRadioButton,
    QVBoxLayout, QWidget
)

from fixtrack.common.utils import color_from_index


class TopLevelControls(QWidget):
    fname_add = os.path.join(os.path.dirname(__file__), "icons", "plus.svg")

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout(self)
        self.btn_add_track = QPushButton(self)
        self.btn_add_track.setIcon(QtGui.QIcon(QtGui.QPixmap(self.fname_add)))
        self.btn_add_track.setToolTip("Add a new track")

        self.btn_add_track.clicked.connect(self.add_new_track)

        layout.addWidget(self.btn_add_track)

        self.setLayout(layout)

    def add_new_track(self, clicked):
        self.parent()._parent.canvas.tracks.add_track()
        self.parent()._parent.canvas.update_trace_data()
        self.parent()._parent.canvas.on_frame_change()
        self.parent()._parent.setup_track_edit_bar()


class TrackEditLayoutBar(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self._parent = parent
        self.reset()

    def reset(self):
        self.track_widgets = {}
        self.vbox = QVBoxLayout()
        self.name = QLabel("")
        self.vbox.addWidget(self.name)
        self.top_level_ctrls = None
        self.radio_button_group = QButtonGroup(self)

    def add_track(self, index, select=False, last=False):
        if self.top_level_ctrls is None:
            self.top_level_ctrls = TopLevelControls(self)
            self.vbox.addWidget(self.top_level_ctrls)

        assert index not in self.track_widgets, "Attempting to add duplicate track %s" % (
            index
        )

        self.track_widgets[index] = TrackEditItem(
            index=index,
            parent=self,
            radio_bg=self.radio_button_group,
            select=select,
        )

        self.vbox.addWidget(self.track_widgets[index])

        self.track_widgets[index].sig_set_track_vis.connect(
            self.parent().canvas.slot_set_track_vis
        )

        if last:
            self.finalize_layout()

    def finalize_layout(self):
        self.vbox.addStretch()
        self.setLayout(self.vbox)
        self.radio_button_group.setExclusive(True)


class TrackEditItem(QGroupBox):
    groupbox_style = """
     QGroupBox {
         border: 4px solid #%s;
         border-radius: 15px;
         margin-top: 15px;
         margin-left: 15px;
         margin-right: 15px;
         margin-bottom: 15px;
     }
     QGroupBox::title  {
        subcontrol-origin: margin;
        subcontrol-position: top center;
    }
    """
    sig_set_track_vis = QtCore.pyqtSignal(int, int)

    fname_eye = os.path.join(os.path.dirname(__file__), "icons", "eye.svg")
    fname_eye_off = os.path.join(os.path.dirname(__file__), "icons", "eye-off.svg")
    fname_del = os.path.join(os.path.dirname(__file__), "icons", "minus.svg")

    def __init__(self, index, parent, radio_bg, select):
        QWidget.__init__(self, parent)
        layout = QGridLayout()
        self.index = index

        self.setTitle(f"Track {self.index}")

        # Visible
        r, c = 0, 0
        self.btn_visible = QPushButton(self)
        self.btn_visible.setToolTip("Toggle track visibility")
        self.btn_visible.setCheckable(True)
        self.btn_visible.setChecked(False)
        self.icon_eye = QtGui.QIcon(QtGui.QPixmap(self.fname_eye))
        self.icon_eye_off = QtGui.QIcon(QtGui.QPixmap(self.fname_eye_off))
        self.btn_visible.setIcon(self.icon_eye)
        self.btn_visible.clicked.connect(self.cb_btn_visible)
        layout.addWidget(self.btn_visible, r, c, 1, 1, QtCore.Qt.AlignHCenter)

        # Delete track
        c += 1
        self.btn_del = QPushButton(self)
        self.btn_del.setToolTip("Delete this track")
        self.btn_del.setIcon(QtGui.QIcon(QtGui.QPixmap(self.fname_del)))
        self.btn_del.clicked.connect(self.cb_btn_del)
        layout.addWidget(self.btn_del, r, c, 1, 1, QtCore.Qt.AlignHCenter)

        # Select track
        c += 1
        self.selected = QRadioButton("Select")
        self.selected.setToolTip("Select track for editing")
        radio_bg.addButton(self.selected)
        self.selected.setChecked(select)
        layout.addWidget(self.selected, r, c + 1, 1, 1, QtCore.Qt.AlignHCenter)

        self.setLayout(layout)
        c = (color_from_index(self.index) * 255).astype(np.uint8)
        self.setStyleSheet(self.groupbox_style % (f"{c[0]:02X}{c[1]:02X}{c[2]:02X}"))

    def cb_btn_visible(self, checked):
        self.sig_set_track_vis.emit(self.index, not checked)
        if checked:
            self.btn_visible.setIcon(self.icon_eye_off)
        else:
            self.btn_visible.setIcon(self.icon_eye)

    def cb_btn_del(self, checked):
        self.parent()._parent.canvas.tracks.rem_track(self.index)
        self.parent()._parent.canvas.update_trace_data()
        self.parent()._parent.canvas.on_frame_change()
        self.parent()._parent.setup_track_edit_bar()
