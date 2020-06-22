from PyQt5 import QtCore

from fixtrack.frontend.picking import PickingAssistant


class VisualWrapper(QtCore.QObject):
    class State(object):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Config(object):
        def __init__(self, enabled=True, visible=True, pickable=False):
            self.enabled = enabled
            self.visible = visible
            self.pickable = pickable

    """
    Thin wrapper around visuals to facilitate dealing with extra state
    and Qt signals/slots.
    """

    def __init__(self, visual=None, enabled=True, visible=True, pickable=False, **kwargs):
        super(VisualWrapper, self).__init__()
        self.visual = visual
        self.visual.visible = visible  # Actual visibility
        self._pa = PickingAssistant()

        self._cfg = VisualWrapper.Config(enabled=enabled, visible=visible, pickable=pickable)
        self._state = VisualWrapper.State(**kwargs)

        self.enabled = self._cfg.enabled
        self.visible = self._cfg.visible

    def _set_data(self, data=None):
        # assert False, "Must define _set_data in derrived class"
        if data is not None:
            self.visual.set_data(data)

    def _set_data_false(self):
        # assert False, "Must define set_data_false in derrived class"
        pass

    def set_data(self, data=None):
        self._set_data(data)

    def set_data_false(self):
        self._set_data_false()

    @property
    def visible(self):
        return self._cfg.visible

    @visible.setter
    def visible(self, b):
        self._cfg.visible = b
        if self.enabled:
            self.visual.visible = self._cfg.visible
        else:
            self.visual.visible = False

    @property
    def enabled(self):
        return self._cfg.enabled

    @enabled.setter
    def enabled(self, ena):
        self._cfg.enabled = ena
        self.visible = self._cfg.visible

    @property
    def transform(self):
        return self.visual.transform

    @transform.setter
    def transform(self, t):
        self.visual.transform = t

    @property
    def parent(self):
        return self.visual.parent

    @parent.setter
    def parent(self, p):
        self.visual.parent = p

    def toggle_visible(self):
        self.visible ^= True

    def toggle_enabled(self):
        self.enabled ^= True

    def picking_vis_set(self):
        self.visual.update_gl_state(blend=False)
        # print("Setting state", self._cfg.pickable, self._cfg.visible)
        self.visual.visible = self._cfg.pickable and self._cfg.visible

    def picking_vis_restore(self):
        self.visual.update_gl_state(blend=True)
        self.visible = self._cfg.visible


class VisualCollection(QtCore.QObject):
    class Config(object):
        def __init__(self, enabled=True, visible=True):
            self.enabled = enabled
            self.visible = visible

    """
    Manage a collection of visual objects
    """

    def __init__(self, parent=None, enabled=True, visible=True):
        super(VisualCollection, self).__init__()
        self._parent = parent
        self._cfg = VisualCollection.Config(enabled=enabled, visible=visible)
        # self._key = 0
        self.visuals = {}

        # Needs to be called at the end of __init__ in any subclasses
        self._sync_visuals()

    def _sync_visuals(self):
        for v in self.visuals.values():
            v.enabled = self._cfg.enabled
            v.visible = self._cfg.visible
        self.enabled = self._cfg.enabled
        self.visible = self._cfg.visible

    # def gen_key(self):
    #     key = self._key
    #     self._key += 1
    #     return key

    def picking_vis_set(self):
        for v in self.visuals.values():
            v.picking_vis_set()

    def picking_vis_restore(self):
        for v in self.visuals.values():
            v.picking_vis_restore()

    def _set_data(self, data=None):
        for v in self.visuals.values():
            v.set_data(data)

    def _set_data_false(self):
        for v in self.visuals.values():
            v.set_data_false()

    def set_data(self, data=None):
        self._set_data(data)

    def set_data_false(self):
        self._set_data_false()

    @property
    def vis_dict(self):
        return self.visuals

    @property
    def vis_list(self):
        return [self.visuals[k] for k in sorted(self.visuals.keys())]

    @property
    def visible(self):
        return self._cfg.visible

    @visible.setter
    def visible(self, b):
        self._cfg.visible = b
        if not self._cfg.enabled:
            b = False
        for v in self.visuals.values():
            v.visible = b

    @property
    def enabled(self):
        return self._cfg.enabled

    @enabled.setter
    def enabled(self, b):
        self._cfg.enabled = b
        self.visible = self._cfg.visible

    def toggle_visible(self):
        self.visible ^= True

    def toggle_enabled(self):
        self.enabled ^= True
