# -*- coding: utf-8 -*-

import cv2
import json
import logging
import numpy as np


class Warp:
    def __init__(self, warp_filename):
        """Warp is an utility class to rectify images containing
        license plates with perspective distortion.

        Args:
            warp_filename (str): Filename of warp file in JSON format
        """
        logging.basicConfig(level=logging.INFO)

        try:
            with open(warp_filename, "r", encoding="utf-8") as f:
                self.warps = json.load(f)
                if not self.warps["warps"]:
                    self.warps = None
        except Exception as e:
            self.warps = None
            logging.info(
                f"Could not find or parse warp json file {warp_filename}: " + str(e)
            )

    def apply(self, im, roi_id):
        """Apply warping to image

        Args:
            im (numpy.ndarray): Image to be warped
            roi_id (int): Identifier of processed region in image

        Returns:
            numpy.ndarray: Warped image
        """
        if not self.warps:
            return im.copy()

        im_warp = None

        warp = next(
            filter(lambda roi: roi["roi_id"] == roi_id, self.warps["warps"]), None
        )

        if warp and len(warp["src_points"]) > 3 and len(warp["dst_points"]) > 3:
            try:
                h, _ = cv2.findHomography(
                    np.array(warp["src_points"]), np.array(warp["dst_points"])
                )

                im_warp = cv2.warpPerspective(
                    im, h, (im.shape[1], im.shape[0]), flags=cv2.INTER_CUBIC
                )
            except Exception as e:
                logging.info("Failed to calculate homography: " + e)

        if im_warp is None:
            im_warp = im.copy()

        return im_warp
