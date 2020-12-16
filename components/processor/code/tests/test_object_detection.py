# -*- coding: utf-8 -*-
import cv2
import os
import pytest
from object_detection.yolo import Yolov5


FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_files",
)

testdata_obj_detection = [
    [os.path.join(FIXTURE_DIR, "car1.jpg"), "car"],
]


@pytest.mark.parametrize("filename,expected", testdata_obj_detection)
def test_obj_detection(filename, expected):
    im = cv2.imread(os.path.join(FIXTURE_DIR, filename))

    yolo = Yolov5()
    detections = yolo.detect(im)

    assert detections
    assert detections[0]["label"].lower() == expected.lower()
