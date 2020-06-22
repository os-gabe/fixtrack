import numpy as np

from matplotlib import cm

from PyQt5 import QtCore

from fixtrack.frontend.visual_wrapper import (VisualCollection, VisualWrapper)
from fixtrack.frontend.pickable_markers import PickableMarkers

from vispy import scene


class Track(VisualCollection):
    """
    A visual collection consisting of a line and pickable markers showing a path
    """

    sig_frame_change = QtCore.pyqtSignal(int)

    def __init__(
        self,
        parent=None,
        enabled=True,
        visible=True,
        line_args={},
        marker_args={},
        data=np.zeros((0, 3)),
        zoffset=0.0,
    ):
        super(Track, self).__init__(parent=parent, enabled=enabled, visible=visible)
        self._line_args = line_args
        self._zoffset = zoffset
        self.visuals["markers"] = PickableMarkers(
            parent=parent,
            vis_args=marker_args,
            data=data,
            pickable=True,
            cmap_func=self._cmap
        )
        # self.visuals["markers"].transform = scene.transforms.STTransform(
        #     translate=[0.0, 0.0, self._zoffset]
        # )
        self.zoffset = zoffset

        self.visuals["line"] = VisualWrapper(
            scene.visuals.Line(
                pos=self.visuals["markers"].data,
                antialias=True,
                method="gl",
                parent=self.visuals["markers"].visual,
            ),
            pickable=False
        )

        self.visuals["markers"].sig_point_clicked.connect(self.slot_point_clicked)
        self._sync_visuals()
        self.set_data()

    def _cmap(self, data):
        c = cm.rainbow(np.linspace(0.0, 1.0, len(data)))
        c[:, 3] = 0.7
        return c

    def slot_point_clicked(
        self, id_clicked, idx_sel, idx_sel_prev, idx_clicked, idx_hover, modifiers
    ):
        self.sig_frame_change.emit(idx_clicked)

    def _set_data(self, data=None):
        self.visuals["markers"].set_data(data)
        if len(self.visuals["markers"]._state.data) > 0:
            self.visuals["line"].visual.set_data(
                pos=self.visuals["markers"]._state.data,
                color=self.visuals["markers"]._state.colors,
                **self._line_args
            )
        else:
            self.visuals["line"].visual.set_data(pos=np.zeros((0, 3)))

    def set_frame_num(self, idx, data=None):
        self.visuals["markers"].set_selected(idx, data)
        self.visuals["markers"].set_data()
        self.visuals["line"].visual.visible = self.visuals["markers"].visual.visible
        self.visuals["line"].visual.set_data(
            pos=self.data, color=self.visuals["markers"]._state.colors, **self._line_args
        )

    @property
    def zoffset(self):
        return self._zoffset

    @zoffset.setter
    def zoffset(self, val):
        self._zoffset = val
        self.visuals["markers"].transform = scene.transforms.STTransform(
            translate=[0.0, 0.0, self._zoffset]
        )

    @property
    def transform(self):
        return self.visuals["markers"].visual.transform

    @transform.setter
    def transform(self, t):
        self.visuals["markers"].visual.transform = t

    @property
    def data(self):
        return self.visuals["markers"]._state.data

    @data.setter
    def data(self, d):
        self.set_data(d)

    @property
    def idx_selected(self):
        return self.visuals["markers"].idx_selected

    @property
    def idx_clicked(self):
        return self.visuals["markers"].idx_clicked

    @property
    def pos_selected(self):
        return self.visuals["markers"].pos_selected

    @property
    def pos_clicked(self):
        return self.visuals["markers"].pos_clicked

    @property
    def color_selected(self):
        return self.visuals["markers"].color_selected

    def on_mouse_press(self, event, img):
        self.visuals["markers"].on_mouse_press(event, img)

    def on_mouse_release(self, event, img):
        self.visuals["markers"].on_mouse_release(event, img)

    def on_mouse_move(self, event, img):
        self.visuals["markers"].on_mouse_move(event, img)
