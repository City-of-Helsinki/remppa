# -*- coding: utf-8 -*-

import collections
import datetime
import logging
import textdistance
import numpy as np
from utils import get_valid_plates, rm_duplicates_1edit_away

MIN_PLATE_W_IN_PX = 60
BLOCK_SIZE = 150
BLOCK_SCAN_PERIOD_IN_SECS = 5
BLOCK_SCAN_PERIOD_EXTRA_BUFFER_IN_SECS = 5
REDETECTION_DELAY_IN_SECS = 60
UNKNOWN_VEHICLE_PREFIX = "[UNK"
UNKNOWN_VEHICLE_POSTFIX = "]"
MIN_IOD = 0.15
DT_1970_01_01 = datetime.datetime.utcfromtimestamp(0)
MIN_PLATE_FREQUENCY_IN_BLOCK = 8


class ROIPlateAnalyser:
    def __init__(self, roi_id, debug):
        """This class interprets metadata retrieved from a region of interest in successive
        video frames and returns the most probable license plate detections.
        Tracked vehicles without license plate recognitions are returned with 'unknown' identifier,
        tracking id and vehicle type.

        Args:
            roi_id (int): Identifier of processed region in image
            debug (bool): Flag indicating whether debug logs and features are enabled
        """
        logging.basicConfig(level=logging.INFO)

        self.roi_id = roi_id
        self.debug = debug
        self.block = collections.deque(BLOCK_SIZE * [{}], BLOCK_SIZE)
        self.detection_history = {}

    def analyse_plates(self, roi):
        """Analyse a set of frame metadata specific to a ROI to detect
        distinct license plates and vehicle types. Some clustering
        and averaging is performed to improve detection accuracy.
        Detections from previous calls are available in ring buffer (block).

        Args:
            roi (List): Frame metadata related to set of unprocessed image files

        Returns:
            List: Detected plates dictionaries found in frame metadata
        """
        plates_to_report = []
        if not roi:
            return plates_to_report

        block_roi_start = roi[0]["timestamp"]

        if self.debug:
            roi_timespan = roi[-1]["timestamp"] - block_roi_start
            secs_per_frame = roi_timespan / float(len(roi))

            logging.info(f"ROI timespan: {roi_timespan}")
            logging.info(f"block timespan: {secs_per_frame * len(self.block)}")
            logging.info(f"s/frame: {secs_per_frame}")

        for frame_id, frame in enumerate(roi):
            time_from_block_roi_start = (
                frame["timestamp"] - block_roi_start
            ).total_seconds()

            detected_plate = self._first_valid_plate(frame, self.roi_id, self.block)
            if detected_plate:
                self.block.append(detected_plate)

            if time_from_block_roi_start >= BLOCK_SCAN_PERIOD_IN_SECS or frame_id == (
                len(roi) - 1
            ):
                block_roi = self._plates_from_last_n_secs(
                    self.block,
                    frame["timestamp"],
                    last_n_secs=(
                        time_from_block_roi_start
                        + BLOCK_SCAN_PERIOD_EXTRA_BUFFER_IN_SECS
                    ),
                )

                block_roi_start = frame["timestamp"]

                # Get results
                results = self._cluster_block_plates(
                    reversed(block_roi),  # reverse to start with biggest plates
                    prev_plates=list(self.detection_history.keys()),
                )

                for detected_plate in results:
                    plate_text = detected_plate["plate_text"]

                    if plate_text not in self.detection_history:
                        self.detection_history[plate_text] = detected_plate
                        plates_to_report.append(detected_plate)
                    elif (
                        detected_plate["timestamp"]
                        - self.detection_history[plate_text]["timestamp"]
                    ).total_seconds() > 0:
                        self.detection_history[plate_text] = detected_plate

                self.detection_history = self._groom_det_history(
                    self.detection_history,
                    frame["timestamp"],
                    REDETECTION_DELAY_IN_SECS,
                )

        return plates_to_report

    def _cluster_block_plates(self, block, prev_plates):
        """Cluster plate texts with one edit distance together and
        select candidate with most votes. Unknown plates are not clustered.
        This function is to be used with only relatively small block
        which is expected to contain only few vehicles.

        Args:
            block (List): List of detected plate dictionaries
            prev_plates (List): List of plate text strings

        Returns:
            List: List of detected plate dictionaries clustered by plate similarity
        """
        distinct_plates = {}
        tracks_for_distinct_plates = {}
        tracks_for_clusters = {}
        labels_for_distinct_plates = {}
        labels_for_clusters = {}

        for plate in block:
            plate_copy = plate.copy()

            if "plate_text" in plate:
                plate_text = plate["plate_text"]
                if plate_text not in distinct_plates:
                    plate_copy["freq"] = 1
                    distinct_plates[plate_text] = plate_copy
                    tracks_for_distinct_plates[plate_text] = [plate["track_id"]]
                    labels_for_distinct_plates[plate_text] = [plate["label"]]
                else:
                    distinct_plates[plate_text]["freq"] += 1
                    tracks_for_distinct_plates[plate_text].append(plate["track_id"])
                    labels_for_distinct_plates[plate_text].append(plate["label"])

        clusters_dict = {}
        plates_list = list(distinct_plates.keys())
        clusters_list = rm_duplicates_1edit_away(plates_list, prev_plates)

        # Append plates under each cluster to an array in clusters_dict
        for c in clusters_list:
            for plate_text, plate_dict in distinct_plates.items():
                if textdistance.levenshtein.distance(plate_text, c) <= 1:
                    p = {
                        "plate_text": plate_text,
                        "plate_dict": plate_dict,
                    }
                    if c not in clusters_dict:
                        clusters_dict[c] = [p]
                    else:
                        clusters_dict[c].append(p)

        # Sort each cluster by plate's frequency
        for c, plates_arr in clusters_dict.items():
            plates_arr = sorted(
                plates_arr,
                key=lambda p: p["plate_dict"]["freq"],
                reverse=True,
            )
            clusters_dict[c] = plates_arr

            for plate in plates_arr:
                plate_text = plate["plate_text"]
                if c not in tracks_for_clusters:
                    tracks_for_clusters[c] = tracks_for_distinct_plates[plate_text]
                else:
                    tracks_for_clusters[c].extend(
                        tracks_for_distinct_plates[plate_text]
                    )

                if c not in labels_for_clusters:
                    labels_for_clusters[c] = labels_for_distinct_plates[plate_text]
                else:
                    labels_for_clusters[c].extend(
                        labels_for_distinct_plates[plate_text]
                    )

        for plate_text, track_ids in tracks_for_clusters.items():
            pos_track_ids = [track_id for track_id in track_ids if track_id > 0]
            if pos_track_ids:
                track_id = max(pos_track_ids, key=pos_track_ids.count)
                distinct_plates[plate_text]["track_id"] = track_id

        for plate_text, labels in labels_for_clusters.items():
            labels = [label for label in labels if len(label) > 0]
            if labels:
                label = max(labels, key=labels.count)
                distinct_plates[plate_text]["label"] = label

        # Select plates with at least min threshold of votes
        candidate_plates = []
        for c, arr_plates in clusters_dict.items():
            if arr_plates[0]["plate_dict"]["freq"] >= MIN_PLATE_FREQUENCY_IN_BLOCK:
                candidate_plates.append(arr_plates[0]["plate_text"])

        candidate_plates = rm_duplicates_1edit_away(candidate_plates, prev_plates)

        return [distinct_plates[plate] for plate in candidate_plates]

    def _plates_from_last_n_secs(self, block, cur_ts, last_n_secs):
        """Get a temporal region of interest from ring buffer containing
        n seconds of license plate detections.

        Args:
            block (Deque): Ring buffer of frame metadata
            cur_ts (datetime): Datetime from which n seconds are calcuated backwards
            last_n_secs (int): Number of seconds to retrieve history

        Returns:
            List: List of detected plates as dictionaries
        """
        return [
            detected_plate
            for detected_plate in block
            if (cur_ts - detected_plate.get("timestamp", DT_1970_01_01)).total_seconds()
            <= last_n_secs
        ]

    def _groom_det_history(self, history, cur_ts, clear_after_secs):
        """Remove old detections from detection history to allow same plate
        to be detected later on and to avoid history data structure from
        growing endlessly

        Args:
            history (List): List of detected plate dictionaries with plate text as key
            cur_ts (datetime): Timestamp to be used as reference of current time
            clear_after_secs (int): Number of seconds from cur_ts to clear

        Returns:
            List: Groomed history list
        """
        return {
            plate_text: detected_plate
            for (plate_text, detected_plate) in history.items()
            if (cur_ts - detected_plate.get("timestamp", DT_1970_01_01)).total_seconds()
            <= clear_after_secs
        }

    def _first_valid_plate(self, frame, roi_id, block):
        """Get first valid plate from block whose coordinates match with a detection in the image.
        From valid plates the longest one is preferred.

        Contents of frame metadata:
            frame = {
                "stream": str,
                "timestamp": datetime
                "frame_no": int
                "ROI": int
                "path": str
                "metadata": Dict
                "plates": Dict
            }

        Args:
            frame (Dict): Dictionary containing camera frame related metadata, such as detections.
            roi_id (int): Identifier of processed region in image
            block (Deque): Ring buffer of frame metadata

        Returns:
            Dict or None: Detected plate with plate text, detected plate with unknown plate text
                          or None if nothing is found
        """
        track_id = -1
        label = ""

        detected_plate = {}
        detected_plate["plate_text"] = ""
        detected_plate["confidence"] = 0
        detected_plate["timestamp"] = frame["timestamp"]
        detected_plate["roi_id"] = roi_id
        detected_plate["track_id"] = -1
        detected_plate["label"] = ""

        for alpr_result in frame["plates"]["results"]:
            if not self._plate_det_wide_enough(alpr_result):
                continue

            valid_plates = get_valid_plates(alpr_result["plate"])
            valid_plates.sort(key=len, reverse=True)
            track_id, label = self._match_det_track_and_label(
                frame["metadata"], alpr_result
            )

            if valid_plates:
                detected_plate["confidence"] = alpr_result["confidence"]
                detected_plate["track_id"] = track_id
                detected_plate["label"] = label
                detected_plate["plate_text"] = valid_plates[0]
                return detected_plate

        # Check for unknown vehicle
        track_id, label = self._match_unk_track_and_label(frame["metadata"])
        unk_label = f"{UNKNOWN_VEHICLE_PREFIX}_{label.upper()}_{track_id}{UNKNOWN_VEHICLE_POSTFIX}"
        if (
            track_id >= 0
            and not self._det_track_in_block(track_id, block)
            and not self._unk_in_block_w_diff_lbl(unk_label, track_id, block)
        ):
            detected_plate["plate_text"] = unk_label
            detected_plate["track_id"] = track_id
            detected_plate["label"] = label

            return detected_plate

        return None

    def _plate_det_wide_enough(self, alpr_result):
        """Determine whether license plate given as parameter contains
        a detection that is considered to be widen enough to be considered
        reliable.

        Args:
            alpr_result (Dict): Results from automatic license plate recognition

        Returns:
            bool: True if plate is wide enough
        """
        plate_w = (
            alpr_result["coordinates"][1]["x"] - alpr_result["coordinates"][0]["x"]
        )

        return plate_w > MIN_PLATE_W_IN_PX

    def _match_det_track_and_label(self, metadata, alpr_result):
        """Find possible object detection track id and label that matches given
        license plate recognition. Bounding box resulting from object detection
        must have enough overlap with ROI in order to be considered a match.

        Args:
            metadata (Dict): Object detection metadata
            alpr_result (Dict): License plate recognition metadata

        Returns:
            Tuple(int, str): Track identifier and label.
                             Identiefier is negative and label empty if there's no match
        """
        track_id = -1
        label = ""

        try:
            detections = metadata["detections"]  # vehicle object detections
            iods = metadata["iods"]
            track_ids = metadata["track_ids"]
            roi_offset = metadata["roi_offset"]
            coords = alpr_result["coordinates"]

            for detection, iod, track_id in zip(detections, iods, track_ids):
                if (
                    self._plate_inside_det(coords, detection, roi_offset)
                    and iod > MIN_IOD
                ):
                    track_id = track_id
                    label = detection["label"]

                    return track_id, label

        except Exception as e:
            logging.warning(e)

        return track_id, label

    def _plate_inside_det(self, plate_coords, detection, roi_offset):
        """Determine whether a license plate is inside an object detection

        Args:
            plate_coords (List): Plate corner points (CCW), starting from top-left
            detection (Dict): Object detection
            roi_offset (List): x and y pixel offset of current ROI

        Returns:
            bool: True if license plate is inside given object detection bounding box
        """
        roi_offset_x = roi_offset[0]
        roi_offset_y = roi_offset[1]

        for pnt in plate_coords:
            x0 = detection["bbox"][0] - roi_offset_x
            y0 = detection["bbox"][1] - roi_offset_y
            x1 = detection["bbox"][2] - roi_offset_x
            y1 = detection["bbox"][3] - roi_offset_y

            if pnt["x"] > x0 and pnt["x"] < x1 and pnt["y"] > y0 and pnt["y"] < y1:
                return True

        return False

    def _match_unk_track_and_label(self, metadata):
        """Find possible object detection track id and label for an unknown license plate.
        Object detection with highest overlap with ROI is considered.

        Args:
            metadata (Dict): Object detection metadata

        Returns:
            Tuple(int, str): Track identifier and label.
                             Identiefier is negative and label empty if there's no match
        """
        track_id = -1
        label = ""

        try:
            if metadata["iods"]:
                max_id = np.argmax(metadata["iods"])

                bbox = metadata["detections"][max_id]["bbox"]
                bbox_w = bbox[2] - bbox[0]
                roi_w = metadata["roi_dims"][0]

                if metadata["iods"][max_id] > MIN_IOD and bbox_w > (0.25 * roi_w):
                    track_id = metadata["track_ids"][max_id]
                    label = metadata["detections"][max_id]["label"]

        except Exception as e:
            logging.warning(e)

        return track_id, label

    def _det_track_in_block(self, track_id, block):
        """Determine whether a plate (with detection) exists
        with given track id within a block

        Args:
            track_id (int): Tracking identifier of a vehicle
            block (Deque): Ring buffer of frame metadata

        Returns:
            bool: True if a given track id (with a detection) exists in block
        """
        for plate in block:
            if (
                plate
                and not plate["plate_text"].startswith(UNKNOWN_VEHICLE_PREFIX)
                and plate["track_id"] == track_id
            ):
                return True

        return False

    def _unk_in_block_w_diff_lbl(self, plate_text, track_id, block):
        """Determine whether a plate without detected text exists in given block

        Args:
            plate_text (str): String identifier for unknown vehicle
            track_id (int): Tracking identifier of a vehicle
            block (Deque): Ring buffer of frame metadata

        Returns:
            bool: True if a given track id (without a detection) exists in block
        """
        for plate in block:
            if (
                plate
                and plate["plate_text"].endswith(
                    f"_{track_id}{UNKNOWN_VEHICLE_POSTFIX}"
                )
                and plate["plate_text"] != plate_text
            ):
                return True

        return False
