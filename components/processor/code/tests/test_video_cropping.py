# -*- coding: utf-8 -*-
import cv2
import os
import numpy as np

from processor.mask import Mask
from processor.warp import Warp


def test_mask_roi_count():
    im = np.zeros((100, 100, 3), dtype=np.uint8)
    im[30:50, 30:50, :] = 128
    im[60:80, 70:80, :] = 128

    tmp_im_filename = "/tmp/test.png"
    cv2.imwrite(tmp_im_filename, im)
    m = Mask(tmp_im_filename)
    os.remove(tmp_im_filename)

    assert m.ROI_count() == 2


def test_warp():
    im = np.zeros((100, 100, 3), dtype=np.uint8)
    im[10:30, 10:30, :] = 128

    warp_filename = "/tmp/warp.json"
    warp_json_str = """{
    "warps": [
        {
        "roi_id": 0,
        "src_points": [
            [10, 10],
            [30, 10],
            [30, 30],
            [10, 30]
        ],
        "dst_points": [
            [5, 10],
            [30, 10],
            [30, 35],
            [10, 30]
        ]
        }
    ]
}
"""

    with open(warp_filename, "w", encoding="utf-8") as f:
        f.write(warp_json_str)

    w = Warp(warp_filename)
    im_warped = w.apply(im, roi_id=0)

    os.remove(warp_filename)

    im_mean = np.mean(im_warped)
    ref_mean = 6.4741
    epsilon = 0.1

    assert np.mean(im_mean) > ref_mean - epsilon
    assert np.mean(im_mean) < ref_mean + epsilon
