import numpy as np

from fixtrack.frontend.pickable_base import PickableBase

from vispy import scene


class PickableMarkers(PickableBase):
    """
    Markers that can highlight on hover and be selected
    """
    class State(PickableBase.State):
        def __init__(self, **kwargs):
            super(PickableMarkers.State, self).__init__(**kwargs)
            self.sizes_raw = None
            self.sizes = None

    class Config(PickableBase.Config):
        def __init__(self, select_scale=1.0, hover_scale=1.0, **kwargs):
            super(PickableMarkers.Config, self).__init__(**kwargs)
            self.select_scale = select_scale
            self.hover_scale = hover_scale

    _kwargs_ignore = ["size", "color_select", "color_hover"]

    def __init__(self, parent=None, data=np.zeros((0, 3)), select_scale=2.0, **kwargs):
        super(PickableMarkers, self).__init__(
            scene.visuals.Markers(pos=data, parent=parent), data=data, parent=parent, **kwargs
        )
        self.visual.set_gl_state("translucent", depth_test=False, blend=True)
        self._cfg.select_scale = select_scale
        self._cfg.hover_scale = select_scale * 1.15
        self.multi_sel = None

    @property
    def marker_size(self):
        return self._cfg.vis_args["size"]

    @marker_size.setter
    def marker_size(self, s):
        self._cfg.vis_args["size"] = max(1, s)
        self._init_data()
        self.set_data()

    def _selected_idxs(self):
        sel = []
        if self.multi_sel is None:
            if self._state.idx_selected >= 0:
                sel = [self._state.idx_selected]
        else:
            sel = self.multi_sel
        return sel

    def _init_data(self):
        super(PickableMarkers, self)._init_data()
        n = len(self._state.data)
        self._state.sizes_raw = np.full((n, ), self._cfg.vis_args["size"])
        self._state.sizes = self._state.sizes_raw.copy()

    def _highlight(self):
        self._state.sizes = self._state.sizes_raw.copy()
        super(PickableMarkers, self)._highlight()

    def _highlight_selected(self):
        super(PickableMarkers, self)._highlight_selected()
        cfg = self._cfg
        state = self._state
        if (state.idx_selected >= 0) and cfg.pickable:
            state.sizes[self._selected_idxs()] = cfg.vis_args["size"] * cfg.select_scale

    def _highlight_hovered(self):
        super(PickableMarkers, self)._highlight_hovered()
        cfg = self._cfg
        state = self._state
        if (state.idx_hover >= 0) and cfg.hoverable:
            state.sizes[self._hover_idxs()] = cfg.vis_args["size"] * cfg.hover_scale

    def _set_data(self):
        if len(self._state.data) > 0:
            kwargs = {
                k: v
                for k, v in self._cfg.vis_args.items() if k not in self._kwargs_ignore
            }
            self._state.edge_colors[:, 3] = self._state.colors[:, 3]

            self.visual.set_data(
                pos=self._state.data,
                size=self._state.sizes,
                face_color=self._state.colors,
                edge_color=self._state.edge_colors,
                edge_width=3,
                **kwargs
            )
        else:
            self.visual.set_data(np.zeros((0, 3)))

    def _set_data_false(self):
        if len(self._state.data) > 0:
            colors = self._pa.unique_colors(id(self)) / 255.0
            colors[self._state.colors[:, 3] < 1.0e-3] = 0.0
            self.visual.set_data(
                pos=self._state.data,
                size=self._state.sizes,
                face_color=colors,
                edge_color=colors,
                edge_width=0,
            )
        else:
            self.visual.set_data(np.zeros((0, 3)))
