import numpy as np

from fixtrack.frontend.pickable_base import PickableBase

from vispy import scene


class PickableLine(PickableBase):
    """
    Line segments that can highlight on hover and be selected
    """
    _kwargs_ignore = ["color_select", "color_hover"]

    def __init__(self, parent=None, data=np.zeros((0, 3)), **kwargs):
        super(PickableLine, self).__init__(
            scene.visuals.Line(pos=data, parent=parent, connect="segments"),
            data=data,
            parent=parent,
            **kwargs
        )
        self.visual.set_gl_state("translucent", depth_test=False, blend=True)

    @property
    def line_width(self):
        return self._cfg.vis_args["width"]

    @line_width.setter
    def line_width(self, s):
        self._cfg.vis_args["width"] = max(1, s)

    def _init_data(self):
        n = len(self._state.data)
        state = self._state
        self._pa.gen_unique_colors(id(self), n // 2)
        state.colors_raw = self._cmap_func(self._state.data)
        state.colors = state.colors_raw.copy()

    def _clip_idxs(self):
        state = self._state
        n = len(self._state.data) // 2
        state.idx_selected = min(state.idx_selected, n - 1)
        state.idx_selected_prev = min(state.idx_selected_prev, n - 1)
        state.idx_clicked = min(state.idx_clicked, n - 1)
        state.idx_hover = min(state.idx_hover, n - 1)

    def _set_data(self, data=None, force_draw=False):
        if len(self._state.data) > 1:
            kwargs = {
                k: v
                for k, v in self._cfg.vis_args.items() if k not in self._kwargs_ignore
            }
            assert len(self._state.data
                       ) == len(self._state.colors
                                ), (len(self._state.data), len(self._state.colors))
            self.visual.set_data(pos=self._state.data, color=self._state.colors, **kwargs)
        else:
            self.visual.set_data(np.zeros((0, 3)), color="red")

    def _set_data_false(self):
        if len(self._state.data) > 1:
            colors = self._pa.unique_colors(id(self)) / 255.0
            colors = np.repeat(colors, 2, axis=0)
            assert len(self._state.data) == len(colors), (len(self._state.data), len(colors))
            self.visual.set_data(
                pos=self._state.data,
                color=colors,
            )
        else:
            self.visual.set_data(np.zeros((0, 3)), color="red")

    def _hover_idxs(self):
        sel = []
        if self._state.idx_hover >= 0:
            idx = 2 * self._state.idx_hover
            sel = [idx, idx + 1]
        return sel

    def _selected_idxs(self):
        sel = []
        if self._state.idx_selected >= 0:
            idx = 2 * self._state.idx_selected
            sel = [idx, idx + 1]
        return sel
