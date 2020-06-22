import numpy as np
from matplotlib import cm
from PyQt5 import QtCore

from fixtrack.frontend.visual_wrapper import VisualWrapper


class PickableBase(VisualWrapper):
    class State(VisualWrapper.State):
        def __init__(self, data, **kwargs):
            super(PickableBase.State, self).__init__(**kwargs)
            self.data = data
            self.idx_selected = -1
            self.idx_selected_prev = -1
            self.idx_hover = -1
            self.idx_clicked = -1
            self.idx_mapping = None
            self.idx_imapping = None

            self.colors_raw = None
            self.colors = None

        def __str__(self):
            msg = ""
            for k in dir(self):
                if k.startswith("idx"):
                    msg += k + ": " + str(getattr(self, k)) + "\n"
            return msg

    class Config(VisualWrapper.Config):
        def __init__(self, vis_args={}, selectable=True, hoverable=True, **kwargs):
            super(PickableBase.Config, self).__init__(**kwargs)
            self.vis_args = vis_args
            self.selectable = selectable
            self.hoverable = hoverable

    sig_point_clicked = QtCore.pyqtSignal(int, int, int, int, int, tuple)

    _kwargs_ignore = []  # Define set of keywords to not pass to the underlying VisPy visual

    def __init__(
        self,
        visual,
        parent=None,
        enabled=True,
        visible=True,
        pickable=False,
        vis_args={},
        data=np.zeros((0, 3)),
        cmap_func=None,
        selectable=True,
        hoverable=True,
        **kwargs
    ):
        super(PickableBase, self).__init__(
            enabled=enabled,
            visible=visible,
            visual=visual,
            pickable=pickable,
        )
        # self._data = data
        self._state = PickableBase.State(data, **kwargs)
        self._cfg.vis_args = vis_args
        self._cfg.selectable = selectable
        self._cfg.hoverable = hoverable

        if cmap_func is None:
            self._cmap_func = self._default_cmap
        else:
            self._cmap_func = cmap_func

        self._init_data()

        self.set_data()

    def _default_cmap(self, data):
        return cm.rainbow(np.linspace(0.0, 1.0, len(data)))

    def _init_data(self):
        n = len(self._state.data)
        state = self._state
        if len(self._pa.unique_colors(id(self), throw=False)) != n:
            self._pa.gen_unique_colors(id(self), n)
        state.colors_raw = self._cmap_func(self._state.data)
        state.colors = state.colors_raw.copy()

    def _process_data(self, data):
        if data is not None:
            self._state.data = data.copy()
            self._init_data()
            self._clip_idxs()

    def _clip_idxs(self):
        state = self._state
        n = len(self._state.data)
        state.idx_selected = min(state.idx_selected, n - 1)
        state.idx_selected_prev = min(state.idx_selected_prev, n - 1)
        state.idx_clicked = min(state.idx_clicked, n - 1)
        state.idx_hover = min(state.idx_hover, n - 1)

    def _set_data(self):
        assert False, "Must define _set_data in derrived class"

    def _set_data_false(self):
        assert False, "Must define set_data_false in derrived class"

    def set_data(self, data=None, force_draw=False, redraw=True):
        if force_draw and data is None:
            self._process_data(self.data)
        else:
            self._process_data(data)

        self._highlight()

        if redraw:
            self._set_data()

    def set_idx_mapping(self, m):
        """
        Allow for remapping of indices to something else
        """
        assert len(m) == len(self._state.data), (len(m), len(self._state.data))
        self._state.idx_mapping = m
        if -1 not in self._state.idx_mapping:
            self._state.idx_mapping[-1] = -1
        self._state.idx_imapping = {v: k for k, v in self._state.idx_mapping.items()}

    def set_data_false(self):
        self._set_data_false()

    def _set_selected(self, idx):
        assert idx >= 0
        n = len(self._state.data)
        assert idx < n, (n, len(self._state.data))
        if idx != self._state.idx_selected:
            self._state.idx_selected_prev = self._state.idx_selected
            self._state.idx_selected = idx

    def set_selected(self, idx, data=None):
        self._process_data(data)
        idx = self.idx_imap(idx)
        self._set_selected(idx)

    def deselect(self):
        self._state.idx_selected = -1
        self._state.idx_selected_prev = -1
        self._state.idx_hover = -1
        self._state.idx_clicked = -1

    def idx_map(self, idx):
        if self._state.idx_mapping is None:
            return idx
        else:
            return self._state.idx_mapping[idx]

    def idx_imap(self, idx):
        if self._state.idx_imapping is None:
            return idx
        else:
            return self._state.idx_imapping[idx]

    @property
    def data(self):
        return self._state.data

    @data.setter
    def data(self, d):
        self.set_data(d)

    @property
    def idx_hover(self):
        return self.idx_map(self._state.idx_hover)

    @property
    def idx_selected(self):
        return self.idx_map(self._state.idx_selected)

    @property
    def idx_selected_prev(self):
        return self.idx_map(self._state.idx_selected_prev)

    @property
    def idx_clicked(self):
        return self.idx_map(self._state.idx_clicked)

    @property
    def pos_hover(self):
        if self._state.idx_hover >= 0:
            return self._state.data[self._state.idx_hover]
        return None

    @property
    def pos_selected(self):
        if self._state.idx_selected >= 0:
            return self._state.data[self._state.idx_selected]
        return None

    @property
    def pos_selected_prev(self):
        if self._state.idx_selected_prev >= 0:
            return self._state.data[self._state.idx_selected_prev]
        return None

    @property
    def pos_clicked(self):
        if self._state.idx_clicked >= 0:
            return self._state.data[self._state.idx_clicked]
        return None

    @property
    def color_hover(self):
        if self._state.idx_hover >= 0:
            return self._state.colors_raw[self._state.idx_hover]
        return None

    @property
    def color_selected(self):
        if self._state.idx_selected >= 0:
            return self._state.colors_raw[self._state.idx_selected]
        return None

    @property
    def color_selected_prev(self):
        if self._state.idx_selected_prev >= 0:
            return self._state.colors_raw[self._state.idx_selected_prev]
        return None

    @property
    def color_clicked(self):
        if self._state.idx_clicked >= 0:
            return self._state.colors_raw[self._state.idx_clicked]
        return None

    def _highlight(self):
        # Reset things
        self._state.colors = self._state.colors_raw.copy()
        self._highlight_selected()
        self._highlight_hovered()

    def _highlight_selected(self):
        cfg = self._cfg
        state = self._state
        if (state.idx_selected >= 0) and cfg.selectable:
            if "color_select" in cfg.vis_args:
                state.colors[self._selected_idxs()] = cfg.vis_args["color_select"]

    def _highlight_hovered(self):
        cfg = self._cfg
        state = self._state
        if (state.idx_hover >= 0) and cfg.hoverable:
            if (state.idx_hover != state.idx_selected) or (not cfg.selectable):
                if "color_hover" in cfg.vis_args:
                    state.colors[self._hover_idxs()] = cfg.vis_args["color_hover"]

    def _hover_idxs(self):
        sel = []
        if self._state.idx_hover >= 0:
            sel = [self._state.idx_hover]
        return sel

    def _selected_idxs(self):
        sel = []
        if self._state.idx_selected >= 0:
            sel = [self._state.idx_selected]
        return sel

    def on_mouse_press(self, event, img, object_id=None):
        if object_id is None:
            object_id = id(self)

        id_clicked, idx = self._pa.img_to_idx(img)
        if id_clicked == object_id:
            print("Picking point index", idx)
            self._state.idx_clicked = idx
            self._set_selected(idx)
            self._highlight()
            self.sig_point_clicked.emit(
                id_clicked,
                self.idx_selected,
                self.idx_selected_prev,
                self.idx_clicked,
                self.idx_hover,
                event.modifiers,
            )
            self.set_data()

    def on_mouse_release(self, event, img, object_id=None):
        self._state.idx_clicked = -1
        self._highlight()
        self.set_data()

    def on_mouse_move(self, event, img, object_id=None):
        if object_id is None:
            object_id = id(self)

        self._state.idx_hover = -1
        id_clicked, idx = self._pa.img_to_idx(img)
        if id_clicked == object_id:
            self._state.idx_hover = idx
        self._highlight()
        self.set_data()

    def flush(self):
        pass
