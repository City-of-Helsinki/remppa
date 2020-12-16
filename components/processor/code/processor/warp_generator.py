# -*- coding: utf-8 -*-

import cv2
import glob
import json
import logging
import os
import parse
import numpy as np

from crypt import read_encrypted_image

logging.basicConfig(level=logging.INFO)


def _create_warp_pnts(im, cb_cols, cb_rows, debug):
    """Detect chessboard pattern in an image and return detected
    and rectified points.

    Args:
        im (numpy.ndarray): Input image containing a chessboard
        cb_cols (int): Number of inner points in column direction of the chessboard pattern
        cb_rows (int): Number of inner points in row direction of the chessboard pattern
        debug (bool): Flag indicating whether detected points are drawn in image

    Returns:
        Tuple(List, List): Rectified and detected chessboard points
    """
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    rectified_cb_pnts = np.mgrid[0:cb_cols, 0:cb_rows].T.reshape(-1, 2)
    rectified_cb_pnts = rectified_cb_pnts.astype(np.float64)

    detected_cb_pnts_subpx = []
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    ret, detected_cb_pnts = cv2.findChessboardCorners(gray, (cb_cols, cb_rows), None)

    if not ret:
        logging.info("Could not find chessboard pattern in image.")
        assert ()

    detected_cb_pnts_subpx = cv2.cornerSubPix(
        gray,
        detected_cb_pnts,
        winSize=(11, 11),
        zeroZone=(-1, -1),
        criteria=criteria,
    )

    if debug:
        # Draw detected chessboard
        im = cv2.drawChessboardCorners(
            im, (cb_cols, cb_rows), detected_cb_pnts_subpx, ret
        )

    rectified_cb_pnts *= (
        detected_cb_pnts_subpx[cb_cols * (cb_rows - 1), 0, 1]
        - detected_cb_pnts_subpx[0, 0, 1]
    ) / (cb_rows - 1)
    rectified_cb_pnts[:, 0] += detected_cb_pnts_subpx[0, 0, 0]
    rectified_cb_pnts[:, 1] += detected_cb_pnts_subpx[0, 0, 1]

    return rectified_cb_pnts, detected_cb_pnts_subpx


def _write_warp_file(filename, roi_warp_dict):
    """Create a warp JSON file

    Args:
        filename (str): Name of JSON file
        roi_warp_dict (Dict): Point correspondences for ROIs
    """
    warps = []
    for roi_id, pnt_matches in roi_warp_dict.items():
        roi_warp = {}
        roi_warp["roi_id"] = roi_id
        roi_warp["src_points"] = pnt_matches[0].tolist()
        roi_warp["dst_points"] = pnt_matches[1].tolist()

        warps.append(roi_warp)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(json.dumps({"warps": warps}, indent=4, ensure_ascii=False))


def create_warps(cb_cols, cb_rows, in_folder, out_folder, debug):
    """Create warp JSON files based on images with chessboard patterns

    Args:
        cb_cols (int):  Number of inner points in column direction of the chessboard pattern
        cb_rows (int):  Number of inner points in row direction of the chessboard pattern
        in_folder (str): Folder containing images with chessboard pattern
        out_folder (str): Folder containing resulting warp files in JSON format
        debug (bool): Indicate whether a debug image should be created
    """
    roi_warp_dict = {}

    files = sorted(glob.glob(os.path.join(in_folder, "*")))
    for i, f in enumerate(files):
        im = None
        filepath, filename = os.path.split(f)
        _, file_extension = os.path.splitext(f)

        if file_extension == ".aes":
            im = read_encrypted_image(f)
        else:
            im = cv2.imread(f)

        if im is None:
            logging.info(f"Could not open image file: {f}")
            continue

        logging.info(f"Processing image: {filename}")

        try:
            parsed = parse.parse(
                "{stream}_ts_{ts}_roi_{roi_id}_f_{frame}" + file_extension, filename
            )

            roi_id = int(parsed["roi_id"])
            rectified_cb_pnts, detected_cb_pnts = _create_warp_pnts(
                im, cb_cols, cb_rows, debug
            )
            roi_warp_dict[roi_id] = (rectified_cb_pnts, detected_cb_pnts)
            warp_filename = os.path.join(out_folder, parsed["stream"] + ".json")
            _write_warp_file(warp_filename, roi_warp_dict)

            if debug:
                rectified_cb_pnts3 = np.hstack(
                    (rectified_cb_pnts, np.zeros((rectified_cb_pnts.shape[0], 1)))
                )

                homography, _ = cv2.findHomography(detected_cb_pnts, rectified_cb_pnts3)
                im_rectified = cv2.warpPerspective(
                    im, homography, (im.shape[1], im.shape[0])
                )
                im_side_by_side = np.hstack((im_rectified, im))
                im_side_by_side = cv2.resize(im_side_by_side, (0, 0), fx=0.25, fy=0.25)
                cv2.imwrite(
                    os.path.join(out_folder, f"rectified_{i:03d}.png"), im_side_by_side
                )
        except Exception as e:
            logging.error(e)


def _safe_cast(val, to_type, default):
    """Safely cast to given type. On failure default value is used.

    Args:
        val (Any): Value to cast
        to_type (Any): Type to try casting
        default (Any): Default value in case of an error

    Returns:
        Any: Casted value or default
    """
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default


if __name__ == "__main__":
    """Utility module for creating warp files for ROI images
    based on rectifying images with chessboard patterns in place
    of license plates.

    Args read from environment variables:
        CB_COLS: Number of inner points in column direction of the chessboard pattern
        CB_ROWS: Number of inner points in row direction of the chessboard pattern
        WARP_CB_PATH: Folder containing images with chessboard pattern
        WARP_PATH: Folder containing resulting warp files in JSON format
        DEBUG: Flag indicating whether to enable debug features
    """
    cb_cols = _safe_cast(os.getenv("CB_COLS"), int, 3)
    cb_rows = _safe_cast(os.getenv("CB_ROWS"), int, 5)
    in_folder = os.getenv("WARP_CB_PATH", "warp_cb_images")
    out_folder = os.getenv("WARP_PATH", "warps")
    debug = os.getenv("DEBUG", "").lower() == "true"

    create_warps(cb_cols, cb_rows, in_folder, out_folder, debug)

    logging.info("DONE")
