# -*- coding: utf-8 -*-

import cv2
import logging
import numpy as np


class Mask:
    def __init__(self, mask_filename):
        """Utility class to generate masked ROI images from a bigger image.
        Masks are provided as blobs in a bitmap where white contiguous
        regions make up a ROI. Black color indicates background.

        Args:
            mask_filename (str): Filename of bitmap containing masked regions
        """
        logging.basicConfig(level=logging.INFO)
        self.ROIs = []

        try:
            self.im = cv2.imread(mask_filename)
            if np.ndim(self.im) > 2:
                self.im = cv2.cvtColor(self.im, cv2.COLOR_BGR2GRAY)

            _, self.im = cv2.threshold(
                self.im, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            self._process()
        except Exception as e:
            logging.error(f"Could not open mask file: {mask_filename} - {str(e)}")

    def _process(self):
        """Find blobs in the mask image and sort masks/ROIs so that indexing
        starts from top-left corner and continues to the right.
        """
        contours, hieararchy = cv2.findContours(
            self.im, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
        )

        if not contours:
            return

        for contour in contours:
            roi_mask = np.zeros_like(self.im)
            contourIdx = -1
            color = 255
            thickness = -1  # fill
            cv2.drawContours(roi_mask, [contour], contourIdx, color, thickness)
            roi_pixels = np.argwhere(roi_mask == color)

            extent = [
                np.min(roi_pixels[:, 0]),
                np.max(roi_pixels[:, 0]),
                np.min(roi_pixels[:, 1]),
                np.max(roi_pixels[:, 1]),
            ]
            roi_mask = np.dstack((roi_mask, roi_mask, roi_mask))

            roi = {}
            roi["center_pixel"] = (
                (extent[1] - extent[0]) / 2 + extent[0]
            ) * self.im.shape[1] + (
                extent[3] - extent[2]
            ) / 2  # id as bounding center
            roi["mask"] = roi_mask
            roi["extent"] = extent

            self.ROIs.append(roi)

        sorted(self.ROIs, key=lambda roi: roi["center_pixel"])

    def apply_ROIs(self, im_to_be_masked):
        """Apply masks and generate a ROI images from image given as argument

        Args:
            im_to_be_masked (numpy.ndarray): Input image to be masked

        Yields:
            numpy.ndarray: [description]
        """
        for roi in self.ROIs:
            extent = roi["extent"]
            im_masked_full = cv2.bitwise_and(im_to_be_masked, roi["mask"])
            im_masked_roi = im_masked_full[extent[0] : extent[1], extent[2] : extent[3]]

            yield im_masked_roi

    def get_roi_detections(self, global_detections, roi_id):
        """Retrieve object detections which intersect with the given ROI.
        Additionally intersection over detection (IOD) is calculated.

        Args:
            global_detections (List): List of dictionaries containing object detections
            roi_id (int): Identifier of processed region in image

        Returns:
            Tuple(List, List): Detections intersecting with ROI and respective IODs
        """
        if roi_id >= len(self.ROIs):
            return [], []

        roi = self.ROIs[roi_id]
        roi_detections = []
        roi_iods = []

        if global_detections:
            color = 255
            im_mask_bin = roi["mask"][:, :, 0]

            for d in global_detections:
                p1 = (int(d["bbox"][0] + 0.5), int(d["bbox"][1] + 0.5))
                p2 = (int(d["bbox"][2] + 0.5), int(d["bbox"][3] + 0.5))

                det_mask_bin = np.zeros_like(im_mask_bin)
                cv2.rectangle(det_mask_bin, p1, p2, color, -1)

                area_det = np.count_nonzero(det_mask_bin)

                roi_det_intersection = cv2.bitwise_and(det_mask_bin, im_mask_bin)
                area_intersection = np.count_nonzero(roi_det_intersection)

                iod = 0  # "intersection over detection"
                if area_det > 0:
                    iod = area_intersection / area_det
                if iod > 0:
                    roi_detections.append(d)
                    roi_iods.append(iod)

        return roi_detections, roi_iods

    def get_roi_offset(self, roi_id):
        """Retrieve pixel offset of given ROI's top-left corner

        Args:
            roi_id (int): Identifier of processed region in image

        Returns:
            Tuple(int, int): X and Y in pixel coordinates
        """
        if roi_id >= len(self.ROIs):
            return [], []

        return [
            int(self.ROIs[roi_id]["extent"][2]),
            int(self.ROIs[roi_id]["extent"][0]),
        ]

    def ROI_count(self):
        """Return number of masks/ROIs

        Returns:
            int: Number of masks/ROIs
        """
        return len(self.ROIs)
