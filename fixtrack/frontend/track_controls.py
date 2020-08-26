import os

import numpy as np
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QButtonGroup, QGridLayout, QGroupBox, QHBoxLayout, QPushButton, QRadioButton, QVBoxLayout,
    QWidget, QCheckBox, QDialog, QDialogButtonBox, QLineEdit, QLabel
)

from fixtrack.common.utils import color_from_index


class FilterDialog(QDialog):
    def __init__(self, index, *args, **kwargs):
        super(FilterDialog, self).__init__(*args, **kwargs)

        self.setWindowTitle(f"Filter Track {index}")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()

        gl = QGridLayout()
        gl.addWidget(QCheckBox("Filter Position"), 0, 0, 1, 1, QtCore.Qt.AlignRight)
        gl.addWidget(QCheckBox("Filter Heading"), 1, 0, 1, 1, QtCore.Qt.AlignRight)

        le1 = QLineEdit()
        le1.setValidator(QtGui.QDoubleValidator(0.1, 30.0, 2, self))
        le1.setPlaceholderText("Cutoff Frequency")
        gl.addWidget(le1, 0, 1, 1, 1)
        gl.addWidget(QLabel("Hz"), 0, 2, 1, 1, QtCore.Qt.AlignRight)

        le2 = QLineEdit()
        le2.setValidator(QtGui.QDoubleValidator(0.1, 30.0, 2, self))
        le2.setPlaceholderText("Cutoff Frequency")
        gl.addWidget(le2, 1, 1, 1, 1)
        gl.addWidget(QLabel("Hz"), 1, 2, 1, 1, QtCore.Qt.AlignRight)

        self.layout.addLayout(gl)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class TopLevelControls(QWidget):
    fname_add = os.path.join(os.path.dirname(__file__), "icons", "plus.svg")
    fname_eye = os.path.join(os.path.dirname(__file__), "icons", "eye.svg")
    fname_heading = os.path.join(os.path.dirname(__file__), "icons", "compass.svg")
    fname_filter = os.path.join(os.path.dirname(__file__), "icons", "sliders.svg")

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        hl1 = QHBoxLayout()
        hl2 = QHBoxLayout()
        vl = QVBoxLayout()
        self.vis_toggle_state = True

        self.btn_add_track = QPushButton(self)
        self.btn_add_track.setIcon(QtGui.QIcon(QtGui.QPixmap(self.fname_add)))
        self.btn_add_track.setToolTip("Add new track")
        self.btn_add_track.clicked.connect(self.cb_add_new_track)
        hl1.addWidget(self.btn_add_track)

        self.btn_toggle_vis = QPushButton(self)
        self.btn_toggle_vis.setToolTip("Show/hide all tracks")
        self.btn_toggle_vis.setIcon(QtGui.QIcon(QtGui.QPixmap(self.fname_eye)))
        self.btn_toggle_vis.clicked.connect(self.cb_toggle_vis)
        hl1.addWidget(self.btn_toggle_vis)

        # self.btn_est_heading = QPushButton(self)
        # self.btn_est_heading.setIcon(QtGui.QIcon(QtGui.QPixmap(self.fname_heading)))
        # self.btn_est_heading.setToolTip("Estimate heading from direction of travel")
        # self.btn_est_heading.clicked.connect(self.cb_est_heading)
        # hl2.addWidget(self.btn_est_heading)

        # self.btn_filt = QPushButton(self)
        # self.btn_filt.setIcon(QtGui.QIcon(QtGui.QPixmap(self.fname_filter)))
        # self.btn_filt.setToolTip("Filter heading vector")
        # self.btn_filt.clicked.connect(self.cb_filt)
        # hl2.addWidget(self.btn_filt)

        vl.addLayout(hl1)
        vl.addLayout(hl2)
        # vl.addWidget(QCheckBox("Interpolate"))
        # vl.addWidget(QCheckBox("Smooth Heading"))
        # vl.addWidget(QCheckBox("Smooth Position"))
        # vl.addWidget(QCheckBox("Position"))
        self.setLayout(vl)

    # def cb_est_heading(self, clicked):
    #     canvas = self.parent()._parent.track_edit_bar._parent.canvas
    #     canvas.tracks.estimate_heading()
    #     canvas.on_frame_change()

    # def cb_filt(self, clicked):
    #     canvas = self.parent()._parent.track_edit_bar._parent.canvas
    #     canvas.tracks.filter_heading(canvas.video.fps, f_cut_hz=5.0)
    #     canvas.on_frame_change()

    def cb_toggle_vis(self, clicked):
        for idx, tw in self.parent()._parent.track_edit_bar.track_widgets.items():
            if tw.btn_visible.isChecked() != self.vis_toggle_state:
                tw.btn_visible.animateClick()
        self.vis_toggle_state ^= True

    def cb_add_new_track(self, clicked):
        self.parent()._parent.canvas.tracks.add_track()
        self.parent()._parent.canvas.on_frame_change()
        self.parent()._parent.canvas.on_frame_change()
        self.parent()._parent.setup_track_edit_bar()


class TrackEditLayoutBar(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self._parent = parent
        self.reset()

    def idx_selected(self):
        for idx, wid in self.track_widgets.items():
            if wid.btn_selected.isChecked():
                print(f"{idx} is checked")
                return idx
        return -1

    def reset(self):
        self.track_widgets = {}
        self.vbox = QVBoxLayout()
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
            self.parent().canvas.visuals["tracks"].slot_set_track_vis
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
    fname_del = os.path.join(os.path.dirname(__file__), "icons", "trash-2.svg")
    fname_rem = os.path.join(os.path.dirname(__file__), "icons", "minus.svg")

    fname_heading = os.path.join(os.path.dirname(__file__), "icons", "compass.svg")
    fname_filter = os.path.join(os.path.dirname(__file__), "icons", "filter.svg")

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

        # Remove detections
        c += 1
        self.btn_rem = QPushButton(self)
        self.btn_rem.setToolTip("Remove detections for cropped range")
        self.btn_rem.setIcon(QtGui.QIcon(QtGui.QPixmap(self.fname_rem)))
        self.btn_rem.clicked.connect(self.cb_btn_rem)
        layout.addWidget(self.btn_rem, r, c, 1, 1, QtCore.Qt.AlignHCenter)

        # Estimate heading
        c += 1
        self.btn_heading = QPushButton(self)
        self.btn_heading.setToolTip("Estimate heading from direction of travel")
        self.btn_heading.setIcon(QtGui.QIcon(QtGui.QPixmap(self.fname_heading)))
        self.btn_heading.clicked.connect(self.cb_btn_heading)
        layout.addWidget(self.btn_heading, r, c, 1, 1, QtCore.Qt.AlignHCenter)

        # Filter
        c += 1
        self.btn_filter = QPushButton(self)
        self.btn_filter.setToolTip("Filter track")
        self.btn_filter.setIcon(QtGui.QIcon(QtGui.QPixmap(self.fname_filter)))
        self.btn_filter.clicked.connect(self.cb_btn_filter)
        layout.addWidget(self.btn_filter, r, c, 1, 1, QtCore.Qt.AlignHCenter)

        # Select track
        c = 0
        r += 1
        self.btn_selected = QRadioButton("Select")
        self.btn_selected.setToolTip("Select track for editing")
        radio_bg.addButton(self.btn_selected)
        self.btn_selected.setChecked(select)
        # self.btn_selected.clicked.connect(self.cb_btn_selected)
        layout.addWidget(self.btn_selected, r, c, 1, 2, QtCore.Qt.AlignHCenter)
        c += 2
        self.btn_interp = QCheckBox("Interp")
        self.btn_interp.setToolTip("Interpolate when adding new points")
        self.btn_selected.setChecked(select)
        # self.btn_interp.clicked.connect(self.cb_btn_interp)
        layout.addWidget(self.btn_interp, r, c, 1, 2, QtCore.Qt.AlignHCenter)

        self.setLayout(layout)
        c = (color_from_index(self.index) * 255).astype(np.uint8)
        self.setStyleSheet(self.groupbox_style % (f"{c[0]:02X}{c[1]:02X}{c[2]:02X}"))

    def cb_btn_heading(self, checked):
        self.parent()._parent.canvas.tracks[self.index].estimate_heading()
        self.parent()._parent.canvas.on_frame_change()

    def cb_btn_filter(self, checked):
        dlg = FilterDialog(self.index, self)
        if dlg.exec_():
            print("Success!")
        else:
            print("Cancel!")
        canvas = self.parent()._parent.canvas
        canvas.tracks[self.index].filter_position(canvas.video.fps, f_cut_hz=15.0)
        canvas.tracks[self.index].filter_heading(canvas.video.fps, f_cut_hz=15.0)
        # canvas.tracks[self.index].filter_position(canvas.video.fps, f_cut_hz=10.0)
        canvas.on_frame_change()

    def cb_btn_visible(self, checked):
        self.sig_set_track_vis.emit(self.index, not checked)
        if checked:
            self.btn_visible.setIcon(self.icon_eye_off)
        else:
            self.btn_visible.setIcon(self.icon_eye)

    def cb_btn_del(self, checked):
        self.parent()._parent.canvas.tracks.rem_track(self.index)
        self.parent()._parent.canvas.on_frame_change()
        self.parent()._parent.setup_track_edit_bar()

    def cb_btn_rem(self, checked):
        aa = self.parent()._parent.player_controls._idx_sel_a
        bb = self.parent()._parent.player_controls._idx_sel_b
        print(f"Removing detections for track {self.index} frames {aa}-{bb}")
        self.parent()._parent.canvas.tracks[self.index][aa:bb]["det"] = False
        self.parent()._parent.canvas.on_frame_change()
