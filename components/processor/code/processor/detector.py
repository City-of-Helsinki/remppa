# -*- coding: utf-8 -*-

import cv2
import glob
import logging
import os

from threading import Thread
from time import sleep

from processor.capture_processor import CaptureProcessor

logging.basicConfig(level=logging.INFO)

DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def process_videos_to_images(video_path, mask_path, warp_path, output_path, threshold):
    """Process videos in MP4 format and create ROI images with object detection and tracking metadata.

    Args:
        video_path (str): Folder to look for processed video files
        mask_path (str): Folder to look for mask files. Must have same name as stream or video but in PNG format
        warp_path (str): Folder to look for warp files. Must have same name as stream or video but in JSON format
        output_path (str): Folder to output resulting cropped images and related metadata
        threshold (int): Threshold for perceptual hash to detect motion in ROI
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    while True:
        video_files = glob.glob(os.path.join(video_path, "*.mp4"))
        for video in video_files:
            logging.info("Processing file: " + video)
            cap = cv2.VideoCapture(video)
            _, video_filename = os.path.split(video)
            prefix, _ = os.path.splitext(video_filename)

            mask_filename = os.path.join(mask_path, prefix + ".png")
            if not mask_filename:
                logging.info("Could not find mask file: " + mask_filename)
                continue

            warp_filename = os.path.join(warp_path, prefix + ".json")

            processor = CaptureProcessor(
                cap, mask_filename, warp_filename, threshold, prefix, output_path
            )
            thread = Thread(target=processor.start, args=())
            thread.daemon = True
            thread.start()
            while True:
                sleep(5)
                logging.info(
                    "sent to yolo: {}%. blocks still to yolo {}".format(
                        int(
                            100
                            * cap.get(cv2.CAP_PROP_POS_FRAMES)
                            / cap.get(cv2.CAP_PROP_FRAME_COUNT)
                        ),
                        len(processor.image_cache),
                    )
                )
                if len(processor.image_cache) == 0 and cap.get(
                    cv2.CAP_PROP_POS_FRAMES
                ) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
                    processor.stop()
                    sleep(1)
                    break

            cap.release()

        if DEBUG:
            break


def main(camera=None):
    """Entry point for creating cropped ROI images with
    related object detections and tracking data from camera stream or video files.

    Args:
        camera (cv2.VideoCapture, optional): VideoCapture object of camera if camera is used. Defaults to None.

    Args read from environment variables:
        VIDEO_PATH: Folder to look for processed video files
        MASK_PATH: Folder to look for mask files. Must have same name as stream or video but in PNG format
        WARP_PATH: Folder to look for warp files. Must have same name as stream or video but in JSON format
        OUTPUT_PATH: Folder to output resulting cropped images and related metadata
        THRESHOLD: Threshold for perceptual hash to detect motion in ROI

    Returns:
        CaptureProcessor or None: Return camera processor object for camera. For videos and on error return None.
    """
    video_path = os.getenv("VIDEO_PATH", "videos")
    mask_path = os.getenv("MASK_PATH", "masks")
    warp_path = os.getenv("WARP_PATH", "warps")
    output_path = os.getenv("OUTPUT_PATH", "crop_images")
    threshold = int(os.getenv("THRESHOLD", 2))

    logging.info(f"video path: {video_path}")
    logging.info(f"mask path: {mask_path}")
    logging.info(f"warp path: {warp_path}")
    logging.info(f"output path: {output_path}")
    logging.info(f"threshold: {str(threshold)}")

    if camera:
        prefix = "cam0"
        mask_filename = os.path.join(mask_path, prefix + ".png")
        if not os.path.exists(mask_filename):
            logging.error("Could not find mask file: " + mask_filename)
            return None

        warp_filename = os.path.join(warp_path, prefix + ".json")
        return CaptureProcessor(
            camera, mask_filename, warp_filename, threshold, prefix, output_path
        )
    else:
        process_videos_to_images(
            video_path, mask_path, warp_path, output_path, threshold
        )


if __name__ == "__main__":
    main()
