import numpy as np


class PickingAssistant(object):
    _colors = np.arange(2**32 - 2**24, 2**32, dtype=np.uint32).view(np.uint8).reshape(-1, 4)
    # _colors = np.arange(0, 2**24, dtype=np.uint32).view(np.uint8).reshape(-1,
    # 4) + [0, 0, 0, 255]
    _blocks = []
    _names = {}
    _background_id = 0

    @staticmethod
    def gen_unique_colors(name, length, init=True):
        if init:
            PickingAssistant._init_background()
        if name in PickingAssistant._names:
            PickingAssistant._realloc_blocks(name)
        PickingAssistant._alloc_block(name, length)

        return PickingAssistant.unique_colors(name)

    @staticmethod
    def _init_background():
        if PickingAssistant._background_id not in PickingAssistant._names:
            PickingAssistant.gen_unique_colors(PickingAssistant._background_id, 1, init=False)

    @staticmethod
    def unique_colors(name, throw=True):
        PickingAssistant._init_background()
        if name not in PickingAssistant._names:
            if throw:
                assert name in PickingAssistant._names
            else:
                return []
        ba, bb, *_ = PickingAssistant._names[name]
        return PickingAssistant._colors[ba:bb, :]

    @staticmethod
    def _realloc_blocks(skip):
        names = PickingAssistant._names.copy()
        PickingAssistant._names.clear()
        PickingAssistant._blocks = []
        for name, (ba, bb, ca, cb) in names.items():
            if name != skip:
                PickingAssistant._alloc_block(name, bb - ba)

    @staticmethod
    def _alloc_block(name, length):
        ba = 0
        if len(PickingAssistant._blocks) > 0:
            ba = PickingAssistant._blocks[-1][1]
        bb = ba + length
        ida = PickingAssistant._colors[ba, :].view(np.uint32)[0]  # & 0x00FFFFFF
        idb = PickingAssistant._colors[bb, :].view(np.uint32)[0]  # & 0x00FFFFFF
        PickingAssistant._blocks.append((ba, bb, ida, idb))
        PickingAssistant._names[name] = PickingAssistant._blocks[-1]
        assert bb - ba == length

    @staticmethod
    def _ids_to_color(ids):
        return ids.view(np.uint8).reshape(-1, 4)

    @staticmethod
    def _color_to_ids(color):
        return color.view(np.uint32).reshape(-1)

    @staticmethod
    def img_to_idx(img):
        PickingAssistant._init_background()

        # Try pixel directly under click
        idxs = img.ravel().view(np.uint32)  # & 0x00FFFFFF
        idx = idxs[len(idxs) // 2]

        # If center pixel was 0 then look for most common nonzero pixel in img
        if idx == PickingAssistant._background_id:
            idxs, counts = np.unique(idxs, return_counts=True)
            idxs = idxs[np.argsort(counts)]
            idx = idxs[-1] or (len(idxs) > 1 and idxs[-2])

        for name, (ba, bb, ida, idb) in PickingAssistant._names.items():
            if idx >= ida and idx < idb:
                return name, idx - ida

        return None, None
