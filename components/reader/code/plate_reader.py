#!/usr/bin/env python3


import datetime
import json
import logging
import os
import parse
import sys
import time

from crypt import read_encrypted_image
from DB import Database
from hasher import create_hash
from ocr_wrapper import alpr as ocr_reader
from roi_plate_analyser import ROIPlateAnalyser, UNKNOWN_VEHICLE_PREFIX
from utils import timestamp_to_date, get_obfuscated_plate

MAX_BATCH_SIZE = 200
ENCRYPT = False


class PlateReader:
    def __init__(self, roi_id):
        """PlateReader looks for unprocessed image files, detects vehicles' license plates
        and caches associated emissions to database for reporting.

        Args:
            roi_id (int): Identifier of processed region in image

        Args read from environment variables
            POLL_FOLDER: Folder to look for images and metadata
            DEBUG: Flag indicating whether debug logs and features are enabled
        """
        logging.basicConfig(level=logging.INFO)
        self.roi_id = roi_id
        self.poll_folder = os.getenv("POLL_FOLDER")
        self.DB = Database()
        self.OCR = ocr_reader

        self.raw_plate_history = []
        self.debug = os.getenv("DEBUG", "").lower() == "true"
        self.reveal_plate = os.getenv("LOG_PLAINTEXT_PLATE", "").lower() == "true"

        self.analyser = ROIPlateAnalyser(roi_id, self.debug)

    def start(self):
        """Start polling for unprocessed frames"""
        logging.info(f"Starting polling for ROI {self.roi_id}")

        while True:
            started = time.time()
            files = self._get_files()

            self._process_files(files)
            if files:
                logging.info(
                    "Loop process time {}s, {} files".format(
                        (time.time() - started), len(files)
                    )
                )
            if self.debug:
                sys.exit(1)
            time.sleep(1)

    def _get_files(self):
        """Return batch of image filenames with associated metadata
        from filename and separate JSON file

        Returns:
            List: List of dictionaries containing information about images to process
                  and related metadata
        """
        if ENCRYPT:
            suffix = "aes"
        else:
            suffix = "jpg"
        files = []

        for f in sorted(os.listdir(self.poll_folder)):
            if f.endswith("json"):  # check for metadata since it's written after image
                try:
                    parsed = parse.parse(
                        "{stream}_ts_{ts}_roi_{roi}_f_{frame}." + "json", f
                    )
                    if int(parsed["roi"]) != self.roi_id:
                        continue
                    files.append(
                        {
                            "stream": parsed["stream"],
                            "timestamp": timestamp_to_date(parsed["ts"]),
                            "frame_no": parsed["frame"],
                            "ROI": parsed["roi"],
                            "path": os.path.join(
                                self.poll_folder, f.replace("json", suffix)
                            ),
                            "metadata": self._read_metadata(
                                os.path.join(self.poll_folder, f)
                            ),
                        }
                    )
                except Exception as e:
                    logging.error("ERROR READING FILES: {}".format(e))
                    pass
            if len(files) >= MAX_BATCH_SIZE:
                break
        if self.debug:
            return files[0:100]
        # return only few at a time
        return files

    def _get_plate(self, path):
        """Read image from given path and perform OCR

        Args:
            path (str): Path to image file

        Returns:
            Dict: License plate recognition results
        """
        if ENCRYPT:
            img = read_encrypted_image(path)
            plates = self.OCR.read_array(bytes(bytearray(img)))
        else:
            plates = self.OCR.read_file(path)
        plates["file"] = path
        return plates

    def _read_metadata(self, path):
        """Read image frame metadata from JSON file.
        Metadata contains e.g. object detection results, ROI offset etc.

        Args:
            path (str): Path to JSON file containing image metadata

        Returns:
            Dict or None: Return image metadata as dictionary or None if unsuccessful
        """
        data = None
        with open(path, mode="r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    def _process_files(self, files):
        """Process set of files and remove after them after processing

        Args:
            files (List): List of frame metadata
        """
        if len(files) == 0:
            return

        self.raw_plate_history = []
        logging.info("LAG: {}".format(datetime.datetime.now() - files[0]["timestamp"]))
        for file in files:
            # Yolo saw an object here
            if len(file["metadata"]["detections"]) > 0:
                plate = self._get_plate(file["path"])
                try:
                    for temp in plate["results"]:
                        logging.info(
                            "ALPR like: {}".format(get_obfuscated_plate(temp["plate"]))
                        )
                except Exception:
                    pass
                file["plates"] = plate
                self.raw_plate_history.append(file)

            # Delete files when data has been read
            try:
                os.remove(file["path"])
            except FileNotFoundError:
                pass
            try:
                os.remove(file["path"].replace(".jpg", ".json"))
            except FileNotFoundError:
                pass

        # analyse known plates
        roi_plates = self.analyser.analyse_plates(self.raw_plate_history)

        for detected_plate in roi_plates:
            self._find_emissions_and_cache(detected_plate)
            plate_text = detected_plate["plate_text"]
            plate_hashed = create_hash(plate_text)
            if self.reveal_plate:
                logging.info(f"ROI: {self.roi_id}, {plate_text}")
            else:
                logging.info(f"ROI: {self.roi_id}, {plate_hashed}")
            # Placeholder:
            # - hash plate
            # - get emission info for the hashed plate
            # - insert emission to local database to be sent out later.
            # emissions = self.DB.get_vehicle(plate_hashed)
            # if emissions:
            #     self.DB.write_cache(detected_plate["timestamp"], emissions)

    def _find_emissions_and_cache(self, detected_plate):
        """Retrieve emissions from database and write to cache for sending.
        If license plate is known and found then actual emissions are read,
        otherwise average for the vehicle type is used.

        Args:
            detected_plate (str): License plate text or string identifier for an unknown vehicle

        TODO:
            Write average vehicle to cache

        Returns:
            bool: True if emission caching was successful
        """
        plate_text = detected_plate["plate_text"]
        if plate_text.startswith(UNKNOWN_VEHICLE_PREFIX):
            # TODO: retrieve average emissions based on detected_plate["label"]
            return True
        else:
            vehicle = self.DB.get_vehicle(create_hash(plate_text))

            if vehicle:
                self.DB.write_cache(str(detected_plate["timestamp"]), vehicle)
                return True

        return False


if __name__ == "__main__":
    roi_id = int(os.getenv("ROI", "0"))

    plate_reader = PlateReader(roi_id)
    plate_reader.start()
