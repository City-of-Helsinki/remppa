# -*- coding: utf-8 -*-

import logging
import os
import torch
import numpy as np

from models.experimental import attempt_load
from utils.datasets import letterbox
from utils.general import (
    non_max_suppression,
    scale_coords,
)
from utils.torch_utils import select_device


class Yolov5:
    def __init__(self):
        """Object detection based on YOLOv5 algorithm.

        See details:
        https://github.com/ultralytics/yolov5
        """
        logging.basicConfig(level=logging.INFO)

        # Initialize
        if torch.cuda.is_available():
            self.device = select_device("0")
        else:
            self.device = select_device("cpu")

        # Load model
        logging.info(
            "Loading model: {}".format(os.getenv("YOLO5_WEIGHTS", "/tmp/yolov5l.pt"))
        )
        self.model = attempt_load(
            os.getenv("YOLO5_WEIGHTS", "/tmp/yolov5l.pt"), map_location=self.device
        )
        if torch.cuda.is_available():
            self.model.half()

        self.im_size = 640

        # Get names and colors
        self.names = (
            self.model.module.names
            if hasattr(self.model, "module")
            else self.model.names
        )

        im_pt = torch.zeros(
            (1, 3, self.im_size, self.im_size), device=self.device
        )  # init image
        _ = self.model(im_pt.half() if torch.cuda.is_available() else im_pt)

    def detect(self, im0):
        """Perform object detection for given image

        Args:
            im0 (numpy.ndarray): Input image from which objects are detected

        Returns:
            List: Object detection results as a list of dictionaries containing
                  bounding boxes, confidence and label
        """
        with torch.no_grad():

            im = letterbox(im0, new_shape=(self.im_size, self.im_size))[0]
            im = im[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB
            im = np.ascontiguousarray(im)

            # Run inference
            im_pt = torch.from_numpy(im).to(self.device)
            im_pt = im_pt.half() if torch.cuda.is_available() else im_pt.float()
            im_pt /= 255.0  # 0 - 255 to 0.0 - 1.0
            if im_pt.ndimension() == 3:
                im_pt = im_pt.unsqueeze(0)

            # Inference
            pred = self.model(im_pt)[0]

            # Apply NMS
            pred = non_max_suppression(
                pred,
                conf_thres=0.4,
                iou_thres=0.5,
                merge=False,
                classes=None,
                agnostic=True,
            )

            detections = []

            # Process detections
            raw_predictions = pred[0]

            if raw_predictions is not None:
                for i in range(raw_predictions.shape[0]):
                    detection = {}

                    # Rescale boxes from img_size to im0 size
                    detection["bbox"] = (
                        scale_coords(
                            im_pt.shape[2:], raw_predictions[i : i + 1, :4], im0.shape
                        )
                        .to("cpu")
                        .round()[0]
                        .numpy()
                        .tolist()
                    )
                    detection["confidence"] = (
                        raw_predictions[i, -2].to("cpu").numpy().tolist()
                    )
                    detection["label"] = self.names[int(raw_predictions[i, -1])]
                    detections.append(detection)

            return detections
