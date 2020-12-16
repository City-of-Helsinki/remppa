# -*- coding: utf-8 -*-

import cv2
import imagehash
import json
import logging
import os
import numpy as np

from datetime import datetime
from threading import Thread
from time import time, sleep
from PIL import Image

from sort.sort import Sort

from processor.mask import Mask
from processor.warp import Warp
from crypt import encrypt_image
from object_detection.yolo import Yolov5


VALID_VEHICLE_CLASSES = ["car", "motorcycle", "bus", "truck"]
ENCRYPT = False
DEFAULT_SKIPRATE = 45
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


class CaptureProcessor:
    def __init__(
        self,
        cap,
        mask_filename,
        warp_filename,
        threshold,
        prefix="",
        output_path="crop_images",
    ):
        """CaptureProcessor starts a thread for processing ROIs defined in a mask file.
        The processor does the following tasks:

        - Crops the images to match masks
        - Warps ROI images to remove perspective distortion (if necessary)
        - Saves ROI images to file system (encrypted if necessary)
        - Detects vehicles in ROIs using Yolo object detection
        - Tracks vehicles using SORT algorithm
        - Saves metadata to a JSON file


        Args:
            cap (cv2.VideoCapture): OpenCV's VideoCapture object for either camera or video stream
            mask_filename (str): Filename of mask file in PNG format
            warp_filename (str): Filename of warp file in JSON format
            threshold (int): Threshold for perceptual hash to detect motion in ROI
            prefix (str, optional): Prefix for image and metadata files. Defaults to "".
            output_path (str, optional): Folder to save images and metadata. Defaults to "crop_images".
        """
        self.keep_processing = False
        self.cap = cap
        self.threshold = threshold
        self.prefix = prefix
        self.output_path = output_path
        self.mask_filename = mask_filename
        self.warp_filename = warp_filename
        self.image_cache = []
        self.keep_sending_after_phash_diff = 2.5  # seconds
        self.yolo = Yolov5()
        self.tracker = Sort(max_age=5, min_hits=3, iou_threshold=0.3)

    def start(self):
        """Start processing thread"""
        self.keep_processing = True
        self.mask = Mask(self.mask_filename)
        self.warp = Warp(self.warp_filename)

        self.yolo_thread = Thread(target=self._yolo_process, args=())
        self.yolo_thread.daemon = True
        self.yolo_thread.start()
        previous_roi_hash = [
            imagehash.phash(Image.fromarray(np.zeros((10, 10))))
        ] * self.mask.ROI_count()
        try:
            spf = 1 / float(self.cap.get(cv2.CAP_PROP_FPS))
        except Exception:
            # our camera does not provide FPS, low value to never wait
            spf = 0.01
        frame_no = -1

        keep_sending = 0
        frame_cache = []
        self.image_cache = []
        frame_date = datetime.now()
        while self.keep_processing:
            # prevent loop lock
            sleep(spf)
            if not self.cap.isOpened():
                sleep(0.5)
                continue
            ret, im = self.cap.read()

            if not ret:
                continue
            if im is None:
                continue
            try:
                if frame_no == self.cap.frame:
                    # we read the same frame twice.
                    continue
                frame_no = self.cap.frame
            except Exception:
                frame_no += 1
            try:
                frame_date = self.cap.frame_date
            except Exception:
                frame_date = datetime.now()

            if time() - keep_sending < self.keep_sending_after_phash_diff:
                # store frames for X seconds after movement
                frame_cache.append((frame_date, frame_no, im))
                im_last = im.copy()
                continue

            if len(frame_cache) > 0:
                # insert the whole block of frames at once
                # sanity check, cache can not be too big:
                # RAM can handle ~ 300 blocks/time to record
                if len(self.image_cache) < 300 / self.keep_sending_after_phash_diff:
                    self.image_cache.append(frame_cache)
                frame_cache = []
                # set phash based on last image in the block
                for i, roi_im in enumerate(self.mask.apply_ROIs(im_last)):
                    roi_im = self.warp.apply(roi_im, i)
                    roi_hash = imagehash.phash(Image.fromarray(roi_im))
                    previous_roi_hash[i] = roi_hash

            for i, roi_im in enumerate(self.mask.apply_ROIs(im)):
                roi_im = self.warp.apply(roi_im, i)
                roi_hash = imagehash.phash(Image.fromarray(roi_im))

                if previous_roi_hash[i] - roi_hash > self.threshold:
                    # some ROI contains change, keep caching images!
                    keep_sending = time()
                    frame_cache.append((frame_date, frame_no, im))
                    # break from ROI loop
                    break

    def stop(self):
        """Stop processing thread"""
        self.keep_processing = False

    def _yolo_process(self):
        """Run YOLO object detection and update tracker"""
        while self.keep_processing:
            # prevent loop lock
            sleep(0.01)

            if len(self.image_cache) == 0:
                continue
            started = time()
            image_list = self.image_cache.pop(0)
            frames_count = len(image_list)
            # skip frames if we're much behind
            # it could be even more sensitive, we used to get every 3rd frame before this
            # Heuristic model to increase skipping. go to 50% rate quite fast, and top at ~100 cache length
            try:
                skip_rate = int(-6 + 21 * np.log(len(self.image_cache) - 0.8))
            except ValueError:
                skip_rate = 0
            # Skip some frames anyway. we have enough FPS
            skip_rate = max(DEFAULT_SKIPRATE, skip_rate)
            frame_skip = self._discard_n(int(skip_rate), 100)
            timestamp = ""
            for list_index, (frame_date, frame_no, im) in enumerate(image_list):
                if frame_skip[list_index % len(frame_skip)] == 1:
                    # skip frames if queue starts to get too long
                    continue
                if not self.keep_processing:
                    break
                detections = None
                for i, roi_im in enumerate(self.mask.apply_ROIs(im)):
                    roi_im = self.warp.apply(roi_im, i)
                    timestamp = frame_date.strftime("%Y_%m_%d_%H_%M_%S_%f")[:-3]
                    frame_name = (
                        self.prefix + f"_ts_{timestamp}_roi_{i:02d}_f_{frame_no}"
                    )
                    metadata_name = frame_name + ".json"

                    if ENCRYPT:
                        frame_name += ".aes"
                        encrypt_image(
                            os.path.join(self.output_path, frame_name), roi_im
                        )
                        if DEBUG:
                            cv2.imwrite(
                                os.path.join(self.output_path, frame_name + ".jpg"),
                                roi_im,
                            )
                    else:
                        frame_name += ".jpg"
                        cv2.imwrite(
                            os.path.join(self.output_path, frame_name),
                            roi_im,
                            [int(cv2.IMWRITE_JPEG_QUALITY), 97],
                        )

                    if not detections:
                        start_yolo = time()
                        all_detections = self.yolo.detect(im)
                        end_yolo = time()
                        detections = [
                            d
                            for d in all_detections
                            if d["label"] in VALID_VEHICLE_CLASSES
                        ]

                        bboxes = np.array([det["bbox"] for det in detections])
                        confidences = np.array(
                            [det["confidence"] for det in detections]
                        )

                        start_tracker = time()
                        tracks = None
                        if bboxes.shape[0] == 0 or confidences.shape[0] == 0:
                            tracks = self.tracker.update()
                        else:
                            tracks = self.tracker.update(np.c_[bboxes, confidences])

                    roi_detections, roi_iods = self.mask.get_roi_detections(
                        detections, i
                    )

                    track_ids = []
                    if roi_detections:
                        track_ids = self._track_ids_for_detections(
                            im, roi_detections, tracks
                        )
                    end_tracker = time()
                    roi_metadata = {}
                    roi_metadata["detections"] = roi_detections
                    roi_metadata["iods"] = roi_iods
                    roi_metadata["track_ids"] = track_ids
                    roi_metadata["roi_offset"] = self.mask.get_roi_offset(i)
                    roi_metadata["roi_dims"] = [roi_im.shape[1], roi_im.shape[0]]

                    with open(
                        os.path.join(self.output_path, metadata_name),
                        "w",
                        encoding="utf-8",
                    ) as f:
                        json.dump(roi_metadata, f, ensure_ascii=False)
                    logging.info(
                        "TIMERS: YOLO: {}s, tracker: {}s,  skipper: {}%, cache: {}, tracks: {}".format(
                            round(end_yolo - start_yolo, 2),
                            round(end_tracker - start_tracker, 2),
                            sum(frame_skip),
                            len(self.image_cache),
                            str(track_ids),
                        )
                    )

            logging.info(
                "YOLO block analysis time. {}s {}FPS, blocks {}, last ts {}".format(
                    int(time() - started),
                    round(frames_count / (time() - started), 2),
                    len(self.image_cache),
                    timestamp,
                )
            )

    def _track_ids_for_detections(self, im, detections, tracks):
        """This function maps bounding boxes received from SORT tracking back to
        original object detections. Matches are determined using a suitable distance threshold.

        Args:
            im (numpy.ndarray): Input image whose dimensions are used to determine suitable threshold
            detections (List): List of dictionaries containing object detection data
            tracks (numpy.ndarray): Bounding boxes and tracking identifiers from SORT algorithm

        Returns:
            List: Tracking identifiers matching object detections
        """
        track_ids = [-1] * len(detections)
        bboxes = np.array([det["bbox"] for det in detections])

        # SORT does not return an index for detection so set threshold based on image size
        sort_match_limit = np.square((im.shape[0] + im.shape[1]) * 0.5 * 0.02)

        for i in range(tracks.shape[0]):
            ss = np.sum(np.square(bboxes - tracks[i, :4]), axis=1)
            min_row = np.argmin(ss, axis=0)

            if ss[min_row] < sort_match_limit:
                track_ids[min_row] = int(tracks[i, 4])
            else:
                track_ids[min_row] = -1

        return track_ids

    def _discard_n(self, n, length=30):
        """from 30 FPS hypothesis, discard N frames.

        Args:
            n (int): Number frames to skip (number of 1's in output array)
            length (int, optional): Length of output array. Defaults to 30.

        Returns:
            List: Array of zeros and ones
        """

        if n <= 0:
            return [0] * length
        if n >= length:
            return [1] * length
        if n < length / 2:
            lin_num = n + 1
            values = (1, 0)
            start_value = 0
        else:
            lin_num = (length - n) + 1
            values = (0, 1)
            start_value = 1
        include = np.linspace(0, length - 1, num=lin_num).astype("int").tolist()
        e = [values[0] if k in include else values[1] for k in reversed(range(length))]
        e[0] = start_value
        return e
