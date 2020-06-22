import os
import time

import cv2
import numpy as np
from matplotlib import cm
from matplotlib import pyplot as plt
from vispy import scene

from fixtrack.backend.track_reader import TrackReader
from fixtrack.backend.video_reader import VideoReader
from fixtrack.frontend.visual_wrapper import VisualCollection, VisualWrapper
from fixtrack.frontend.pickable_line import PickableLine
from fixtrack.frontend.pickable_markers import PickableMarkers
# from fixtrack.frontend.track import Track


class CanvasBase(scene.SceneCanvas):
    def __init__(self, parent, **kwargs):
        scene.SceneCanvas.__init__(self, keys="interactive", **kwargs)
        self.unfreeze()
        self.view = self.central_widget.add_view()
        # self.view.camera = "arcball"  # scene.PanZoomCamera(aspect=1, up="-z")
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
    def __init__(self, parent, video=None, track=None, estimate_heading=False, **kwargs):
        super().__init__(parent, **kwargs)

        self.unfreeze()
        self.track = TrackReader(track, estimate_heading=estimate_heading)
        self.video = VideoReader(video)

        assert self.track.num_frames == self.video.num_frames, "Track length != video length"

        self.view.camera = scene.PanZoomCamera(aspect=1, up="-z")
        self.view.camera.rect = (0, 0, self.video.width, self.video.height)

        self.cam_track = 0

        self._parent = parent

        # Add video visual
        self.visuals["img"] = scene.visuals.Image(parent=self.view.scene)
        self.visuals["img"].transform = scene.STTransform(translate=[0.0, 0.0, -1.0])

        self.frame_num = 0
        self.base_alpha = 0.25
        self.trace_len = 45
        self.trace_alpha = np.linspace(self.base_alpha, 1.0, self.trace_len)
        self.track_colors = self.track_cmap_func(
            np.linspace(0.0, 1.0, self.track.num_tracks), alpha=1.0, div=1
        )

        self.frame_colors = [
            np.tile(tc, (self.track.num_frames, 1)) for tc in self.track_colors
        ]

        self.visuals["heading"] = PickableLine(
            parent=self.view.scene,
            data=np.zeros((0, 3)),
            pickable=True,
            selectable=False,
            hoverable=True,
            vis_args={
                "width": 10,
                "color_hover": [0, 0, 0, 0.5],
                "color_select": [1, 0, 0, 0.5]
            },
            cmap_func=lambda data: self.track_cmap_func(data, alpha=0.5, div=2)
        )
        for idx_tk, tk in enumerate(self.track.tracks):
            # self.visuals[f"track_edit{idx_tk}"] = Track(
            #     parent=self.view.scene,
            #     enabled=True,
            #     visible=True,
            #     line_args={
            #         "width": 10,
            #         # "color_hover": [0, 0, 0, 0.5],
            #         # "color_select": [1, 0, 0, 0.5]
            #     },
            #     marker_args={
            #         "size": 25,
            #         # "color_hover": [0, 0, 0, 0.4],
            #         # "color_select": [0, 0, 0, 0.5]
            #     },
            #     data=np.zeros((0, 3)),
            #     zoffset=0.0,
            # )
            # TODO - Combine these individual visuals into collections for better performance
            self.visuals[f"track_{idx_tk}"] = scene.visuals.Line(
                tk["pos"],
                color=self.track_colors[idx_tk],
                # method="agg",
                width=10,
                parent=self.view.scene
            )

            # TODO - Pass in list of labels so we can just one visual
            self.visuals[f"track_label{idx_tk}"] = scene.visuals.Text(
                text=f"{idx_tk+1}",
                color=self.track_colors[idx_tk],
                bold=False,
                italic=False,
                face='OpenSans',
                font_size=64,
                pos=[0.0, 0.0, 0.0],
                rotation=0.0,
                anchor_x='center',
                anchor_y='top',
                method='cpu',
                font_manager=None,
                parent=self.view.scene,
            )
        self.track_colors[:, 3] = self.base_alpha

        self.visuals["markers"] = PickableMarkers(
            parent=self.view.scene,
            data=np.zeros((0, 3)),
            pickable=True,
            selectable=True,
            hoverable=True,
            vis_args={
                "size": 25,
                "color_hover": [0, 0, 0, 0.4],
                "color_select": [0, 0, 0, 0.5]
            },
            select_scale=1.5,
            cmap_func=lambda data: self.track_cmap_func(data, alpha=1, div=1)
        )
        self.visuals["markers"].sig_point_clicked.connect(self.slot_marker_clicked)
        self.visuals["shadows"] = PickableMarkers(
            parent=self.view.scene,
            data=np.zeros((0, 3)),
            pickable=True,
            selectable=True,
            hoverable=True,
            vis_args={
                "size": 25,
                "color_hover": [0, 0, 0, 0.4],
                "color_select": [0, 0, 0, 0.5]
            },
            select_scale=1.5,
            cmap_func=lambda data: self.track_cmap_func(data, alpha=0.35, div=1)
        )
        self.visuals["shadows"].sig_point_clicked.connect(self.slot_marker_clicked)
        self.visuals["dropers"] = PickableLine(
            parent=self.view.scene,
            data=np.zeros((0, 3)),
            pickable=True,
            selectable=True,
            hoverable=True,
            vis_args={
                "width": 10,
                "color_hover": [0, 0, 0, 0.4],
                "color_select": [0, 0, 0, 0.5]
            },
            select_scale=1.5,
            cmap_func=lambda data: self.track_cmap_func(data, alpha=0.5, div=2)
        )
        self.visuals["dropers"].sig_point_clicked.connect(self.slot_marker_clicked)

        self.visuals["axes"] = scene.visuals.XYZAxis(parent=self.view.scene)

        self.ts = time.time()

        self.freeze()

    def slot_marker_clicked(
        self, id_clicked, idx_sel, idx_sel_prev, idx_clicked, idx_hover, modifiers
    ):
        self.cam_track = idx_clicked + 1
        self.visuals["markers"].deselect()
        self.visuals["shadows"].deselect()
        self.visuals["dropers"].deselect()

        self.visuals["markers"].set_selected(idx_clicked)
        # self.visuals["shadows"].set_selected(idx_clicked)
        # self.visuals["dropers"].set_selected(idx_clicked)

    def track_cmap_func(self, data, alpha=0.5, div=1):
        face_color = cm.Paired(np.linspace(0.0, 1.0, len(data) // div))
        face_color[:, 3] = alpha
        face_color = np.repeat(face_color, div, axis=0)
        return face_color

    def toggle_cam(self):
        if isinstance(self.view.camera, scene.PanZoomCamera):
            self.view.camera = "arcball"
        else:
            self.view.camera = "panzoom"

    def get_heading_segments(self, frame_num, vec_len):
        positions = [tk["pos"][frame_num] for tk in self.track.tracks]
        positions = np.vstack(positions)
        headings = [tk["vec"][frame_num] for tk in self.track.tracks]
        headings = np.vstack(headings)
        heading_segs = np.zeros((2 * len(headings), 3))
        heading_segs[0::2] = positions
        heading_segs[1::2] = positions + headings * vec_len
        return positions, heading_segs

    def set_img(self, frame_num=None):
        if frame_num is not None:
            self.frame_num = frame_num
        img = self.video.get_frame(self.frame_num)

        # self.frame_num += 1
        # if self.frame_num >= self.video.num_frames:
        #     self.frame_num = 0

        self.visuals["img"].set_data(img)

        # Get the track positions and heading vectors
        vec_len = 50
        # positions = [tk["pos"][frame_num] for tk in self.track.tracks]
        # positions = np.vstack(positions)
        # headings = [tk["vec"][frame_num] for tk in self.track.tracks]
        # headings = np.vstack(headings)
        # heading_segs = np.zeros((2 * len(headings), 3))
        # heading_segs[0::2] = positions
        # heading_segs[1::2] = positions + headings * vec_len
        positions, heading_segs = self.get_heading_segments(frame_num, vec_len)

        offset = 50
        positions[:, 2] = offset
        drop_data = np.empty((2 * len(positions), 3))
        drop_data[0::2, :] = positions
        drop_data[1::2, :] = offset

        self.visuals["markers"].set_data(positions)  # , face_color=face_color, size=25)

        if self.cam_track > 0:
            self.view.camera.center = positions[self.cam_track - 1, :2].flatten().tolist()
            # TODO: Implement heading lock
            # self.view.camera.transform.rotate(headings[self.cam_track - 1], [0, 0, 1])

        for idx_tk, tk in enumerate(self.track.tracks):
            num_frames = len(self.track.tracks[0])
            # frame_colors = np.tile(self.track_colors[idx_tk], (num_frames, 1))
            self.frame_colors[idx_tk][:, 3] = self.base_alpha
            # self.frame_colors[idx_tk][~tk["det"], 3] = 0
            # TODO - don't need to recalculate these every time
            fidxs = np.arange(frame_num + 1, frame_num + self.trace_len)
            ridxs = np.arange(frame_num - 1, frame_num - self.trace_len, -1)

            fidxs = fidxs[(fidxs >= 0) & (fidxs < num_frames)]
            ridxs = ridxs[(ridxs >= 0) & (ridxs < num_frames)]

            self.frame_colors[idx_tk][fidxs,
                                      3] = np.linspace(self.base_alpha, 1.0, len(fidxs))[::-1]
            self.frame_colors[idx_tk][ridxs,
                                      3] = np.linspace(self.base_alpha, 1.0, len(ridxs))[::-1]

            self.visuals[f"track_{idx_tk}"].set_data(
                tk["pos"], color=self.frame_colors[idx_tk], width=10
            )
            # self.visuals[f"track_edit{idx_tk}"].set_data(tk["pos"])

        if not isinstance(self.view.camera, scene.PanZoomCamera):
            cam_pos = self.view.camera.transform.matrix[3, :3]
            for idx_tk, tk in enumerate(self.track.tracks):
                fish_pos = positions[idx_tk]
                fish_dist = np.linalg.norm(fish_pos - cam_pos)
                self.visuals[f"track_label{idx_tk}"].pos = fish_pos
                self.visuals[f"track_label{idx_tk}"].font_size = np.clip(
                    fish_dist * 100, 2000, 20000
                )
        else:
            for idx_tk, tk in enumerate(self.track.tracks):
                fish_pos = positions[idx_tk]
                self.visuals[f"track_label{idx_tk}"].pos = fish_pos
                self.visuals[f"track_label{idx_tk}"].font_size = 100
            self.view.camera.view_changed()

        # face_color[:, 3] = 0.35
        positions[:, 2] = 0
        drop_data[1::2] = positions
        self.visuals["shadows"].set_data(positions)  # , face_color=face_color, size=25)

        # face_color[:, 3] = 0.45
        # face_color = np.repeat(face_color, 2, axis=0)
        self.visuals["dropers"].set_data(drop_data)  # , color=face_color, width=10)
        self.visuals["heading"].set_data(heading_segs)  # , width=10, color=face_color)

    def on_mouse_press(self, event):
        # pos = self.view.camera.transform.imap(event.pos)[:3]
        # self.mouse_pos.append(pos)
        img = self.render_picking(event)
        for v in self.visuals.values():
            if hasattr(v, "on_mouse_press"):
                v.on_mouse_press(event, img)
        # self.visuals["heading"].on_mouse_press(event, img)
        # self.visuals["markers"].on_mouse_press(event, img)
        # self.visuals["shaddows"].on_mouse_press(event, img)
        # self.visuals["droppers"].on_mouse_press(event, img)
        ##################################
        if self.visuals["heading"].idx_clicked >= 0:
            if event.button == 1:
                self.view.camera.interactive = False

    def on_mouse_release(self, event):
        # pos = self.view.camera.transform.imap(event.pos)[:3]
        # self.mouse_pos.append(pos)
        img = self.render_picking(event)
        for v in self.visuals.values():
            if hasattr(v, "on_mouse_release"):
                v.on_mouse_release(event, img)

        self.view.camera.interactive = True

    def on_mouse_move(self, event):
        # pos = self.view.camera.transform.imap(event.pos)[:3]
        # self.mouse_pos.append(pos)
        img = self.render_picking(event)
        # self.visuals["heading"].on_mouse_move(event, img)
        for v in self.visuals.values():
            if hasattr(v, "on_mouse_move"):
                v.on_mouse_move(event, img)

        click_pos = self.view.camera.transform.imap(event.pos)[:3]
        if not isinstance(self.view.camera, scene.PanZoomCamera):
            return

        trail = event.trail()

        if (self.visuals["heading"].idx_clicked >= 0) and (trail is not None):
            idx_track = self.visuals["heading"].idx_clicked
            idx_frame = self.frame_num
            track_pos = self.track.tracks[idx_track]["pos"][idx_frame]
            # track_vec = self.track.tracks[idx_track]["vec"][idx_frame]
            vec = click_pos - track_pos
            print(click_pos, track_pos)
            vec = vec / (np.linalg.norm(vec) + 1.0e-20)
            # mag = np.linalg.norm(track_vec)
            self.track.tracks[idx_track]["vec"][idx_frame] = vec
            _, heading_segs = self.get_heading_segments(idx_frame, 50)
            self.visuals["heading"].set_data(heading_segs)
            # self.update()
            # self.visuals["heading"].set_data(heading_segs)

            # # heading = self.track.tracks[idx_track]["vec"][idx_frame]
            # # headings = np.vstack(headings)
            # heading_segs = np.zeros((2 * len(headings), 3))
            # heading_segs[0::2] = positions
            # heading_segs[1::2] = positions + headings * vec_len

    def on_key_press(self, event):
        # Forward the Qt event to the parent
        self._parent.keyPressEvent(event._native)

    def on_key_release(self, event):
        # Forward the Qt event to the parent
        self._parent.keyReleaseEvent(event._native)
