import numpy as np
from PyQt5 import QtCore
from vispy import scene, util

from fixtrack.frontend.pickable_line import PickableLine
from fixtrack.frontend.pickable_markers import PickableMarkers
from fixtrack.frontend.visual_wrapper import VisualCollection, VisualWrapper
from fixtrack.common.utils import color_from_index, normalize_vecs


class TrackCollectionVisual(VisualCollection):
    """
    A visual collection consisting of a line, pickable markers, and heading vectors
    """

    sig_frame_change = QtCore.pyqtSignal(int)

    def __init__(
        self,
        tracks,
        parent=None,
        enabled=True,
        visible=True,
    ):
        super(TrackCollectionVisual,
              self).__init__(parent=parent, enabled=enabled, visible=visible)
        self.tracks = tracks

        pos, seg, vec = self.get_data()
        self.visuals["headings"] = PickableLine(
            parent=parent.view.scene,
            data=vec,
            pickable=True,
            selectable=False,
            hoverable=True,
            vis_args={
                "width": 10,
                "color_hover": [0, 0, 0, 0.85],
                "color_select": [1, 0, 0, 0.65]
            },
            cmap_func=self.cmap_vec_func,
        )

        self.visuals["markers"] = PickableMarkers(
            parent=parent.view.scene,
            data=pos,
            pickable=True,
            selectable=False,
            hoverable=True,
            vis_args={
                "size": 15,
                "color_hover": [1, 0, 0, 0.5],
                "color_select": [1, 1, 0, 0.5],
            },
            select_scale=2.5,
            cmap_func=self.cmap_pos_func,
        )
        self.visuals["markers"].sig_point_clicked.connect(self.slot_marker_clicked)

        self.visuals["traces"] = VisualWrapper(
            scene.visuals.Line(
                seg,
                connect="segments",
                color=self.cmap_seg_func(seg),
                width=5,
                parent=parent.view.scene
            ),
            segs=seg,
            width=10,
            connect="segments",
        )
        self._sync_visuals()
        self.set_data()

    @property
    def frame_num(self):
        return self._parent.frame_num

    def on_frame_change(self, frame_num=None):
        pos, seg, vec = self.get_data()
        if frame_num is not None:
            self.visuals["markers"].set_selected(frame_num)
        self.visuals["markers"].set_data(pos)
        self.visuals["headings"].set_data(vec)

        self.visuals["traces"].visual.set_data(pos=seg, color=self.cmap_seg_func(seg))

    def slot_set_track_vis(self, idx, vis):
        self.tracks[idx].visible = vis
        self.on_frame_change()

    def track_address_from_vec_idx(self, vec_idx):
        track_idx = vec_idx // self.tracks.num_frames
        frame_idx = vec_idx % self.tracks.num_frames
        return track_idx, frame_idx

    def get_data(self, vec_len=25):
        pos = np.vstack([track["pos"] for track in self.tracks])
        seg = np.vstack([np.repeat(track["pos"], 2, axis=0)[1:-1] for track in self.tracks])
        v = normalize_vecs(np.vstack([track["vec"] for track in self.tracks.tracks]))
        vec = np.zeros((2 * len(pos), 3))
        vec[0::2] = pos
        vec[1::2] = pos + v * vec_len
        return pos, seg, vec

    def cmap_pos_func(self, data, alpha=0.5):
        c = color_from_index(range(self.tracks.num_tracks))
        c[:, 3] = alpha
        assert (len(data) % self.tracks.num_tracks) == 0
        chunk_len = len(data) // self.tracks.num_tracks
        colors = np.empty((len(data), 4))
        colors[:, 3] = alpha
        if "markers" in self.visuals:
            self.visuals["markers"].multi_sel = []
        for track_idx, track in enumerate(self.tracks):
            frame_idx = track_idx * chunk_len
            colors[frame_idx:frame_idx + chunk_len] = c[track_idx]
            if "markers" in self.visuals:
                self.visuals["markers"].multi_sel.append(frame_idx + self.frame_num)
            det = track["det"]
            colors[frame_idx:frame_idx + chunk_len][:, 3] *= det
            colors[frame_idx:frame_idx + chunk_len][:, 3] *= track.visible
            if hasattr(self._parent._parent, "player_controls"):
                idx_a = self._parent._parent.player_controls._idx_sel_a
                idx_b = self._parent._parent.player_controls._idx_sel_b
                colors[frame_idx:frame_idx + chunk_len][:idx_a, 3] *= 0
                colors[frame_idx:frame_idx + chunk_len][idx_b:, 3] *= 0
        return colors

    def cmap_seg_func(self, data, alpha=0.5):
        c = color_from_index(range(self.tracks.num_tracks))
        c[:, 3] = alpha
        assert (len(data) % self.tracks.num_tracks) == 0
        chunk_len = len(data) // self.tracks.num_tracks
        colors = np.empty((len(data), 4))
        colors[:, 3] = alpha
        for track_idx, track in enumerate(self.tracks):
            frame_idx = track_idx * chunk_len
            det = np.repeat(track["det"], 2)

            colors[frame_idx:frame_idx + chunk_len] = c[track_idx]
            colors[frame_idx:frame_idx + chunk_len][:, 3] *= det[1:-1]
            colors[frame_idx:frame_idx + chunk_len][:, 3] *= det[0:-2]
            colors[frame_idx:frame_idx + chunk_len][:, 3] *= det[2:]

            colors[frame_idx:frame_idx + chunk_len][:, 3] *= track.visible

            if hasattr(self._parent._parent, "player_controls"):
                idx_a = self._parent._parent.player_controls._idx_sel_a
                idx_b = self._parent._parent.player_controls._idx_sel_b
                colors[frame_idx:frame_idx + chunk_len][:idx_a * 2, 3] *= 0
                colors[frame_idx:frame_idx + chunk_len][idx_b * 2:, 3] *= 0
        return colors

    def cmap_vec_func(self, data, alpha=0.5):
        c = color_from_index(range(self.tracks.num_tracks))
        c[:, 3] = alpha
        assert (len(data) % self.tracks.num_tracks) == 0
        chunk_len = len(data) // self.tracks.num_tracks
        colors = np.empty((len(data), 4))
        colors[:, 3] = alpha
        for track_idx, track in enumerate(self.tracks):
            frame_idx = track_idx * chunk_len
            det = np.repeat(track["det"], 2)
            colors[frame_idx:frame_idx + chunk_len] = c[track_idx]
            colors[frame_idx:frame_idx + chunk_len][:, 3] *= det
            colors[frame_idx:frame_idx + chunk_len][:, 3] *= track.visible
            if hasattr(self._parent._parent, "player_controls"):
                idx_a = self._parent._parent.player_controls._idx_sel_a
                idx_b = self._parent._parent.player_controls._idx_sel_b
                colors[frame_idx:frame_idx + chunk_len][:idx_a * 2, 3] *= 0
                colors[frame_idx:frame_idx + chunk_len][idx_b * 2:, 3] *= 0
        return colors

    def slot_marker_clicked(
        self, id_clicked, idx_sel, idx_sel_prev, idx_clicked, idx_hover, modifiers
    ):
        idx_track, idx_frame = self.track_address_from_vec_idx(idx_clicked)
        self._parent._parent.track_edit_bar.track_widgets[idx_track].btn_selected.animateClick(
        )
        self._parent._parent.player_controls.set_frame_num(idx_frame)

    def on_mouse_press(self, event, img):
        edit_bar = self._parent._parent.track_edit_bar
        for v in self.visuals.values():
            if hasattr(v, "on_mouse_press"):
                v.on_mouse_press(event, img)
        c0 = self.visuals["markers"].idx_clicked >= 0
        c1 = self.visuals["headings"].idx_clicked >= 0
        if (util.keys.SHIFT in event.modifiers) and (event.button == 1) and not (c0 or c1):
            if not isinstance(self._parent.view.camera, scene.PanZoomCamera):
                return
            click_pos = self._parent.view.camera.transform.imap(event.pos)[:3]
            idx_track = edit_bar.idx_selected()
            if idx_track >= 0:
                interp = edit_bar.track_widgets[idx_track].btn_interp.isChecked()
                self.tracks[idx_track].add_det(self.frame_num, click_pos, interp=interp)
                self._parent.on_frame_change()
        # elif (util.keys.SHIFT in event.modifiers) and (event.button == 1) and (c0 or c1):
        #     idx_track, idx_frame = self.track_address_from_vec_idx(
        #         max(self.visuals["headings"].idx_clicked, self.visuals["markers"].idx_clicked)
        #     )
        elif (util.keys.SHIFT in event.modifiers) and (event.button == 2) and (c0 or c1):
            idx_track, idx_frame = self.track_address_from_vec_idx(
                max(self.visuals["headings"].idx_clicked, self.visuals["markers"].idx_clicked)
            )
            self.tracks.tracks[idx_track]["det"][idx_frame] = False
            self.visuals["headings"].deselect()
            self.visuals["markers"].deselect()
            self._parent.on_frame_change()

    def on_mouse_release(self, event, img):
        for v in self.visuals.values():
            if hasattr(v, "on_mouse_release"):
                v.on_mouse_release(event, img)
        self._parent.view.camera.interactive = True

    def on_mouse_move(self, event, img):
        for v in self.visuals.values():
            if hasattr(v, "on_mouse_move"):
                v.on_mouse_move(event, img)

        click_pos = self._parent.view.camera.transform.imap(event.pos)[:3]
        if not isinstance(self._parent.view.camera, scene.PanZoomCamera):
            return

        trail = event.trail()
        if (util.keys.SHIFT in event.modifiers) and (event.button == 1):
            if (self.visuals["headings"].idx_clicked >= 0) and (trail is not None):
                idx_track, idx_frame = self.track_address_from_vec_idx(
                    self.visuals["headings"].idx_clicked
                )
                track_pos = self.tracks.tracks[idx_track]["pos"][idx_frame]
                vec = click_pos - track_pos
                vec = normalize_vecs(vec)
                self.tracks.tracks[idx_track]["vec"][idx_frame] = vec
                self.tracks[idx_track][idx_frame]["vec"] = vec
                self._parent.on_frame_change()
            elif (self.visuals["markers"].idx_clicked >= 0) and (trail is not None):
                idx_track, idx_frame = self.track_address_from_vec_idx(
                    self.visuals["markers"].idx_clicked
                )
                self.tracks.tracks[idx_track]["pos"][idx_frame] = click_pos
                self._parent.on_frame_change()
