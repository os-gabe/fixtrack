import os
import time

import cv2
import numpy as np
from matplotlib import pyplot as plt
from vispy import scene, util

from fixtrack.backend.track_io import TrackIO
from fixtrack.backend.video_reader import VideoReader
from fixtrack.frontend.pickable_line import PickableLine
from fixtrack.frontend.pickable_markers import PickableMarkers
from fixtrack.frontend.visual_wrapper import VisualCollection, VisualWrapper
from fixtrack.common.utils import color_from_index, normalize_vecs


class CanvasBase(scene.SceneCanvas):
    def __init__(self, parent, **kwargs):
        scene.SceneCanvas.__init__(self, keys="interactive", **kwargs)
        self.unfreeze()
        self.view = self.central_widget.add_view()
        self.visuals = {}
        self._parent = parent
        self.freeze()

    @staticmethod
    def _picking_vis_setup(vis, restore=False):
        if restore:
            vis.picking_vis_restore()
            vis.set_data()
        else:
            vis.picking_vis_set()
            vis.set_data_false()

    @staticmethod
    def picking_vis_setup(vis_dict, restore=False):
        for name, visual in vis_dict.items():
            if isinstance(visual, dict):
                CanvasBase.picking_vis_setup(visual, restore)
            elif isinstance(visual, list):
                vd = {i: v for i, v in enumerate(visual)}
                CanvasBase.picking_vis_setup(vd, restore)
            elif isinstance(visual, VisualCollection):
                CanvasBase._picking_vis_setup(visual, restore)
            elif isinstance(visual, VisualWrapper):
                CanvasBase._picking_vis_setup(visual, restore)

    @staticmethod
    def _hide_visual(vis):
        # Don't hide visual if it is pickable
        pickable = True
        if getattr(vis, "pickable", None) is not None:
            pickable = vis.pickable

        v = vis.visible
        if not pickable:
            vis.visible = False

        return v

    @staticmethod
    def _hide_visuals(vis_dict):
        state = {}
        for name, visual in vis_dict.items():
            if isinstance(visual, dict):
                state[name] = CanvasBase._hide_visuals(visual)
            elif isinstance(visual, list):
                vd = {i: v for i, v in enumerate(visual)}
                state[name] = CanvasBase._hide_visuals(vd)
            elif isinstance(visual, VisualCollection):
                state[name] = CanvasBase._hide_visuals(visual.visuals)
            elif hasattr(visual, "visible"):
                state[name] = CanvasBase._hide_visual(visual)
            else:
                assert False, "Object must have visible attribute" + str(type(visual))
        return state

    @staticmethod
    def _restore_visuals(vis_dict, state):
        for name, visual in vis_dict.items():
            if isinstance(visual, dict):
                CanvasBase._restore_visuals(visual, state[name])
            elif isinstance(visual, list):
                vd = {i: v for i, v in enumerate(visual)}
                CanvasBase._restore_visuals(vd, state[name])
            elif isinstance(visual, VisualCollection):
                CanvasBase._restore_visuals(visual.visuals, state[name])
            elif hasattr(visual, "visible"):
                visual.visible = state[name]
            else:
                assert False, "Object must have visible attribute" + str(type(visual))

    def render_picking(self, event):
        self.picking_vis_setup(self.visuals, restore=False)
        pos = self.transforms.canvas_transform.map(event.pos)
        rad = 5
        img = self.render(
            (pos[0] - rad, pos[1] - rad, rad * 2 + 1, rad * 2 + 1), bgcolor=(0, 0, 0, 0)
        )
        self.picking_vis_setup(self.visuals, restore=True)
        return img

    def print_screen(self, fname=None, size=None):
        if fname is None:
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            idx = 0
            fname = os.path.join("screenshots", "img_%05d.png" % (idx))
            while os.path.isfile(fname):
                idx += 1
                fname = os.path.join("screenshots", "img_%05d.png" % (idx))
        img = self.render()
        r, c, *_ = img.shape
        if size is not None:
            d = max(r, c)
            s = size / d
            r, c = int(s * r), int(s * c)
            img = cv2.resize(img, (c, r))
        print("Saving image (%d,%d): %s" % (r, c, fname))
        plt.imsave(fname, img)


class VideoCanvas(CanvasBase):
    def __init__(
        self,
        parent,
        fname_video=None,
        fname_track=None,
        estimate_heading=False,
        filter_heading=False,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.unfreeze()
        self.tracks = TrackIO.load(fname_track)
        self.video = VideoReader(fname_video)

        if estimate_heading:
            self.tracks.estimate_heading()

        if filter_heading:
            self.tracks.filter_heading(self.video.fps, f_cut_hz=5.0)

        self.frame_num = 0

        assert self.tracks.num_frames == self.video.num_frames, "Track length != video length"

        self.view.camera = scene.PanZoomCamera(aspect=1, up="-z")
        self.view.camera.rect = (0, 0, self.video.width, self.video.height)

        self._parent = parent

        # Add video visual
        self.visuals["img"] = VisualWrapper(scene.visuals.Image(parent=self.view.scene))
        self.visuals["img"].transform = scene.STTransform(translate=[0.0, 0.0, -1.0])

        self.visuals["headings"] = PickableLine(
            parent=self.view.scene,
            data=np.zeros((0, 3)),
            pickable=True,
            selectable=False,
            hoverable=True,
            vis_args={
                "width": 10,
                "color_hover": [0, 0, 0, 0.85],
                "color_select": [1, 0, 0, 0.65]
            },
            cmap_func=lambda data: self.track_cmap_func(data, alpha=0.65, repeats=2)
        )

        self.visuals["markers"] = PickableMarkers(
            parent=self.view.scene,
            data=np.zeros((0, 3)),
            pickable=True,
            selectable=False,
            hoverable=True,
            vis_args={
                "size": 25,
                "color_hover": [0, 0, 0, 0.4],
                "color_select": [0, 0, 0, 0.5],
            },
            select_scale=1.5,
            cmap_func=lambda data: self.track_cmap_func(data, alpha=1, repeats=1)
        )
        self.visuals["markers"].sig_point_clicked.connect(self.slot_marker_clicked)

        segs = np.repeat(np.arange(0, self.tracks.num_frames), 2)[1:-1]
        pos = [track["pos"][segs] for track in self.tracks]
        pos = np.vstack(pos)
        self.visuals["traces"] = VisualWrapper(
            scene.visuals.Line(
                pos,
                connect="segments",
                color=self.cmap_trace_func(pos),
                width=10,
                parent=self.view.scene
            ),
            segs=segs,
            width=10,
            connect="segments",
        )

        self.ts = time.time()

        self.freeze()

    def slot_set_track_vis(self, idx, vis):
        self.tracks[idx].visible = vis
        self.update_trace_data()

    def update_trace_data(self):
        pos = np.vstack(
            [track["pos"][self.visuals["traces"]._state.segs] for track in self.tracks]
        )
        self.visuals["traces"].visual.set_data(
            pos=pos,
            width=self.visuals["traces"]._state.width,
            connect=self.visuals["traces"]._state.connect,
            color=self.cmap_trace_func(pos)
        )

    def trace_idxs(self, idx_frame):
        ti = self.trace_idxs + idx_frame
        ti = ti[(ti >= 0) & (ti < self.tracks.num_frames)]
        tis = []
        for idx_track in range(self.tracks.num_tracks):
            # Skip frames without a detection
            m = self.tracks[idx_track]["det"][ti]
            tis.append(ti[m])
        return tis

    def slot_marker_clicked(
        self, id_clicked, idx_sel, idx_sel_prev, idx_clicked, idx_hover, modifiers
    ):
        self._parent.track_edit_bar.track_widgets[idx_clicked].selected.animateClick()

    def track_cmap_func(self, data, alpha=0.5, repeats=1):
        colors = color_from_index(
            range(self.tracks.num_tracks)
        )  # cm.Paired(np.linspace(0.0, 1.0, self.tracks.num_tracks))
        colors[:, 3] = alpha

        if repeats > 1:
            colors = np.repeat(colors, repeats, axis=0)

        for idx_tk in range(self.tracks.num_tracks):
            if len(colors) > 0:
                for r in range(repeats):
                    colors[repeats * idx_tk +
                           r][3] = self.tracks.tracks[idx_tk]["det"][self.frame_num]
        return colors

    def cmap_trace_func(self, data, alpha=0.5):
        colors = color_from_index(range(self.tracks.num_tracks))
        colors[:, 3] = alpha
        assert (len(colors) % self.tracks.num_tracks) == 0
        chunk_len = len(data) // self.tracks.num_tracks
        colors = np.vstack([np.tile(color, (chunk_len, 1)) for color in colors])

        segs = np.repeat(np.arange(0, self.tracks.num_frames), 2)[1:-1]
        det = [track["det"][segs] for track in self.tracks]
        det = np.hstack(det)
        colors[:, 3] *= det
        colors[1:, 3] *= det[:-1]
        colors[:-1, 3] *= det[1:]
        for track_idx, track in enumerate(self.tracks):
            frame_idx = track_idx * chunk_len
            colors[frame_idx:frame_idx + chunk_len][:, 3] *= track.visible
        return colors

    def toggle_cam(self):
        if isinstance(self.view.camera, scene.PanZoomCamera):
            self.view.camera = "arcball"
        else:
            self.view.camera = "panzoom"

    def get_heading_segments(self, frame_num, vec_len):
        positions = [tk["pos"][frame_num] for tk in self.tracks.tracks]
        positions = np.vstack(positions)
        headings = [tk["vec"][frame_num] for tk in self.tracks.tracks]
        headings = np.vstack(headings)
        heading_segs = np.zeros((2 * len(headings), 3))
        heading_segs[0::2] = positions
        heading_segs[1::2] = positions + headings * vec_len

        return positions, heading_segs

    def on_frame_change(self, frame_num=None):
        if frame_num is not None:
            self.frame_num = frame_num

        img = self.video.get_frame(self.frame_num)

        self.visuals["img"].set_data(img)

        self.update()

        vec_len = 50

        positions, heading_segs = self.get_heading_segments(self.frame_num, vec_len)

        self.visuals["markers"].set_data(positions)
        self.visuals["headings"].set_data(heading_segs)

    def on_mouse_press(self, event):
        img = self.render_picking(event)
        for v in self.visuals.values():
            if hasattr(v, "on_mouse_press"):
                v.on_mouse_press(event, img)

        if self.visuals["headings"].idx_clicked >= 0:
            if event.button == 1:
                self.view.camera.interactive = False

    def on_mouse_release(self, event):
        img = self.render_picking(event)
        for v in self.visuals.values():
            if hasattr(v, "on_mouse_release"):
                v.on_mouse_release(event, img)

        self.view.camera.interactive = True

    def on_mouse_move(self, event):
        img = self.render_picking(event)
        for v in self.visuals.values():
            if hasattr(v, "on_mouse_move"):
                v.on_mouse_move(event, img)

        click_pos = self.view.camera.transform.imap(event.pos)[:3]
        if not isinstance(self.view.camera, scene.PanZoomCamera):
            return

        trail = event.trail()
        if util.keys.SHIFT in event.modifiers:
            if (self.visuals["headings"].idx_clicked >= 0) and (trail is not None):
                idx_track = self.visuals["headings"].idx_clicked
                idx_frame = self.frame_num
                track_pos = self.tracks.tracks[idx_track]["pos"][idx_frame]
                vec = click_pos - track_pos
                print(click_pos, track_pos)
                vec = normalize_vecs(vec)
                self.tracks.tracks[idx_track]["vec"][idx_frame] = vec
                _, heading_segs = self.get_heading_segments(idx_frame, 50)
                self.visuals["headings"].set_data(heading_segs)

    def on_key_press(self, event):
        # Forward the Qt event to the parent
        self._parent.keyPressEvent(event._native)

    def on_key_release(self, event):
        # Forward the Qt event to the parent
        self._parent.keyReleaseEvent(event._native)
