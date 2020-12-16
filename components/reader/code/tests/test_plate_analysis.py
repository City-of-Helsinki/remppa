# -*- coding: utf-8 -*-
import pytest
from datetime import datetime

from roi_plate_analyser import ROIPlateAnalyser


def frame_data(
    frame_id,
    mins,
    s,
    ms,
    roi_id,
    plate_text,
    det_found=True,
    track_id=-1,
    iod=0.5,
    label="car",
    bbox=[544.0, 191.0, 1099.0, 706.0],
):
    """Create debug frame metadata for testing

    Args:
        frame_id (int): Identifier for image frame
        mins (int): Minute of capture time
        s (int): Second of capture time
        ms (int): Milliseconds of capture time
        roi_id (int): Identifier of processed region in image
        plate_text (str): License plate text
        det_found (bool, optional): Indication whether object detection is present. Defaults to True.
        track_id (int, optional): Vehicle tracking identifier. Defaults to -1.
        iod (float, optional): ROI intersection over object detection. Defaults to 0.5.
        label (str, optional): Label of object detection. Defaults to "car".
        bbox (List): Object detection bounding box in pixels [x1, y1, x2, y2]
    """
    plate_results = []
    frame_id_str = str(frame_id)

    if plate_text:
        plate_results = [
            {
                "plate": plate_text,
                "confidence": 87.518509,
                "matches_template": 0,
                "plate_index": 0,
                "region": "",
                "region_confidence": 0,
                "processing_time_ms": 14.7,
                "requested_topn": 25,
                "coordinates": [
                    {"x": 499, "y": 268},
                    {"x": 596, "y": 266},
                    {"x": 596, "y": 287},
                    {"x": 500, "y": 289},
                ],
                "candidates": [
                    {
                        "plate": plate_text,
                        "confidence": 87.5,
                        "matches_template": 0,
                    }
                ],
            }
        ]

    if det_found:
        obj_det_data = {
            "detections": [
                {
                    "bbox": bbox,
                    "confidence": 0.81884765625,
                    "label": label,
                }
            ],
            "iods": [iod],
            "track_ids": [track_id],
            "roi_offset": [504, 314],
            "roi_dims": [1381, 541],
        }
    else:
        obj_det_data = {
            "detections": [],
            "iods": [],
            "track_ids": [],
            "roi_offset": [504, 314],
            "roi_dims": [1381, 541],
        }

    metadata = {
        "stream": "cam0",
        "timestamp": datetime(2020, 11, 24, 11, mins, s, ms),
        "frame_no": f"{frame_id_str}",
        "ROI": f"{roi_id:02d}",
        "path": f"/home/kilpi/crop_images/cam0_ts_2020_11_24_11_{mins:02d}_{s:02d}_{ms:03d}_roi_{roi_id:02d}_f_{frame_id_str}.jpg",
        "metadata": obj_det_data,
        "plates": {
            "version": 2,
            "data_type": "alpr_results",
            "epoch_time": 1606822225442,
            "img_width": 1381,
            "img_height": 541,
            "processing_time_ms": 72.6,
            "regions_of_interest": [{"x": 0, "y": 0, "width": 1381, "height": 541}],
            "results": plate_results,
            "file": f"/home/kilpi/crop_images/cam0_ts_2020_11_24_11_{mins:02d}_{s:02d}_{ms:03d}_roi_{roi_id:02d}_f_{frame_id_str}.jpg",
        },
    }

    return metadata


test_data = [
    [
        [
            [  # frame_id, mins, s, ms, roi_id, plate_text, det_found, track_id, iod, label
                frame_data(1, 1, 1, 0, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(2, 1, 1, 10, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(3, 1, 1, 20, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(4, 1, 1, 30, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(5, 1, 1, 50, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(6, 1, 1, 60, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(7, 1, 1, 70, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(8, 1, 1, 80, 0, "ABC123", True, 94, iod=0.5, label="car"),
            ],
            [
                frame_data(9, 1, 1, 00, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(10, 1, 1, 00, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(11, 1, 1, 10, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(12, 1, 1, 20, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(13, 1, 1, 30, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(14, 1, 1, 40, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(15, 1, 1, 50, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(16, 1, 1, 60, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(37, 1, 1, 40, 0, "AAA000", True, 94, iod=0.5, label="car"),
            ],
        ],
        ["ABC123"],
    ],
    [
        [
            [  # non valid plate, track id ok --> unknown
                frame_data(1, 1, 1, 0, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(2, 1, 1, 10, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(3, 1, 1, 20, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(4, 1, 1, 30, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(5, 1, 1, 50, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(6, 1, 1, 60, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(7, 1, 1, 70, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(8, 1, 1, 80, 0, "ABC", True, 94, iod=0.5, label="car"),
            ],
            [  # non valid plate, track id ok --> unknown
                frame_data(9, 1, 1, 00, 0, "ABD", True, 95, iod=0.5, label="truck"),
                frame_data(10, 1, 1, 00, 0, "ABD", True, 95, iod=0.5, label="truck"),
                frame_data(11, 1, 1, 10, 0, "ABD", True, 95, iod=0.5, label="truck"),
                frame_data(12, 1, 1, 20, 0, "ABD", True, 95, iod=0.5, label="truck"),
                frame_data(13, 1, 1, 30, 0, "ABD", True, 95, iod=0.5, label="truck"),
                frame_data(14, 1, 1, 40, 0, "ABD", True, 95, iod=0.5, label="truck"),
                frame_data(15, 1, 1, 50, 0, "ABD", True, 95, iod=0.5, label="truck"),
                frame_data(16, 1, 1, 60, 0, "ABD", True, 95, iod=0.5, label="truck"),
                frame_data(37, 1, 3, 40, 0, "AAA000", True, 94, iod=0.5, label="car"),
            ],
        ],
        ["[UNK_CAR_94]", "[UNK_TRUCK_95]"],
    ],
    [
        [
            [
                frame_data(1, 1, 1, 0, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(2, 1, 1, 10, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(3, 1, 1, 20, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(4, 1, 1, 30, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(5, 1, 1, 50, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(6, 1, 1, 60, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(7, 1, 1, 70, 0, "ABC", True, 94, iod=0.5, label="car"),
                frame_data(8, 1, 1, 80, 0, "ABC", True, 94, iod=0.5, label="car"),
            ],
            [  # missing tracking ids
                frame_data(9, 1, 1, 00, 0, "ABD", True, -1, iod=0.5, label="truck"),
                frame_data(10, 1, 1, 00, 0, "ABD", True, -1, iod=0.5, label="truck"),
                frame_data(11, 1, 1, 10, 0, "ABD", True, 95, iod=0.5, label="truck"),
                frame_data(12, 1, 1, 20, 0, "ABD", True, -1, iod=0.5, label="truck"),
                frame_data(13, 1, 1, 30, 0, "ABD", True, -1, iod=0.5, label="truck"),
                frame_data(14, 1, 1, 40, 0, "ABD", True, -1, iod=0.5, label="truck"),
                frame_data(15, 1, 1, 50, 0, "ABD", True, 95, iod=0.5, label="truck"),
                frame_data(16, 1, 1, 60, 0, "ABD", True, 95, iod=0.5, label="truck"),
                frame_data(37, 1, 1, 40, 0, "AAA000", True, 94, iod=0.5, label="car"),
            ],
        ],
        ["[UNK_CAR_94]"],
    ],
    [
        [
            [  # Too low iod
                frame_data(1, 1, 1, 0, 0, "ABC", True, 94, iod=0.05, label="car"),
                frame_data(2, 1, 1, 10, 0, "ABC", True, 94, iod=0.05, label="car"),
                frame_data(3, 1, 1, 20, 0, "ABC", True, 94, iod=0.05, label="car"),
                frame_data(4, 1, 1, 30, 0, "ABC", True, 94, iod=0.05, label="car"),
                frame_data(5, 1, 1, 50, 0, "ABC", True, 94, iod=0.05, label="car"),
                frame_data(6, 1, 1, 60, 0, "ABC", True, 94, iod=0.05, label="car"),
                frame_data(7, 1, 1, 70, 0, "ABC", True, 94, iod=0.05, label="car"),
                frame_data(8, 1, 1, 80, 0, "ABC", True, 94, iod=0.05, label="car"),
            ]
        ],
        [],
    ],
    [
        [
            [  # Some invalid, but repairable license plate detections
                frame_data(1, 1, 1, 0, 0, "ABC12", True, 94, iod=0.5, label="car"),
                frame_data(2, 1, 1, 10, 0, "LABC123", True, 94, iod=0.5, label="car"),
                frame_data(3, 1, 1, 20, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(4, 1, 1, 30, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(5, 1, 1, 50, 0, "ABC123I", True, 94, iod=0.5, label="car"),
                frame_data(6, 1, 1, 60, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(7, 1, 1, 70, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(8, 1, 1, 80, 0, "ABC123", True, 94, iod=0.5, label="car"),
                frame_data(9, 1, 1, 90, 0, "ABC123", True, 94, iod=0.5, label="car"),
            ]
        ],
        ["ABC123"],
    ],
    [
        [
            [  # Some variance in labels
                frame_data(1, 1, 1, 0, 0, "ABC123", True, 1, iod=0.5, label="car"),
                frame_data(2, 1, 1, 10, 0, "ABC123", True, 1, iod=0.5, label="car"),
                frame_data(3, 1, 1, 20, 0, "ABC123", True, 1, iod=0.5, label="car"),
                frame_data(4, 1, 1, 30, 0, "ABC123", True, 1, iod=0.5, label="truck"),
                frame_data(5, 1, 1, 50, 0, "ABC123", True, 1, iod=0.5, label="truck"),
                frame_data(6, 1, 1, 60, 0, "ABC123", True, 1, iod=0.5, label="car"),
                frame_data(7, 1, 1, 70, 0, "ABC123", True, 1, iod=0.5, label="car"),
                frame_data(8, 1, 1, 80, 0, "ABC123", True, 1, iod=0.5, label="car"),
                frame_data(11, 1, 2, 0, 0, "ABC111", True, 2, iod=0.5, label="truck"),
                frame_data(12, 1, 2, 10, 0, "ABC111", True, 2, iod=0.5, label="truck"),
                frame_data(13, 1, 2, 20, 0, "ABC111", True, 2, iod=0.5, label="truck"),
                frame_data(14, 1, 2, 30, 0, "ABC111", True, 2, iod=0.5, label="truck"),
                frame_data(15, 1, 2, 50, 0, "ABC111", True, 2, iod=0.5, label="truck"),
                frame_data(16, 1, 2, 60, 0, "ABC111", True, 2, iod=0.5, label="truck"),
                frame_data(17, 1, 2, 70, 0, "ABC111", True, 2, iod=0.5, label="truck"),
                frame_data(18, 1, 2, 80, 0, "ABC111", True, 3, iod=0.5, label="truck"),
                frame_data(19, 1, 2, 90, 0, "BBB111", True, 3, iod=0.5, label="truck"),
                frame_data(20, 1, 2, 99, 0, "BBB111", True, 3, iod=0.5, label="truck"),
            ],
            [
                frame_data(21, 1, 2, 0, 0, "ABC22", True, 4, iod=0.5, label="car"),
                frame_data(22, 1, 2, 10, 0, "ABC22", True, 4, iod=0.5, label="car"),
                frame_data(23, 1, 2, 20, 0, "ABC22", True, 4, iod=0.5, label="car"),
                frame_data(24, 1, 2, 30, 0, "ABC22", True, 4, iod=0.5, label="car"),
                frame_data(25, 1, 2, 50, 0, "ABC22", True, 4, iod=0.5, label="car"),
                frame_data(26, 1, 2, 60, 0, "ABC22", True, 4, iod=0.5, label="car"),
                frame_data(27, 1, 2, 70, 0, "ABC22", True, 4, iod=0.5, label="car"),
                frame_data(28, 1, 2, 80, 0, "ABC22", True, 4, iod=0.5, label="car"),
                # Redect, but added during next batch
                frame_data(31, 10, 3, 0, 0, "ABC123", True, 5, iod=0.5, label="car"),
                frame_data(32, 10, 3, 10, 0, "ABC123", True, 5, iod=0.5, label="car"),
                frame_data(33, 10, 3, 20, 0, "ABC123", True, 5, iod=0.5, label="truck"),
                frame_data(34, 10, 3, 30, 0, "ABC123", True, 5, iod=0.5, label="truck"),
                frame_data(35, 10, 3, 50, 0, "ABC123", True, 5, iod=0.5, label="car"),
                frame_data(36, 10, 3, 60, 0, "ABC123", True, 5, iod=0.5, label="car"),
                frame_data(37, 10, 3, 70, 0, "ABC123", True, 5, iod=0.5, label="car"),
                frame_data(38, 10, 3, 80, 0, "ABC123", True, 5, iod=0.5, label="car"),
            ],
            [
                frame_data(41, 10, 5, 0, 0, "BC125", True, 6, iod=0.5, label="car"),
                frame_data(42, 10, 5, 10, 0, "BC125", True, 6, iod=0.5, label="car"),
                frame_data(43, 10, 5, 20, 0, "BC125", True, 6, iod=0.5, label="car"),
                frame_data(44, 10, 5, 30, 0, "BC125", True, 6, iod=0.5, label="truck"),
                frame_data(45, 10, 5, 50, 0, "BC125", True, 6, iod=0.5, label="car"),
                frame_data(46, 10, 5, 60, 0, "BC125", True, 6, iod=0.5, label="car"),
                frame_data(47, 10, 5, 70, 0, "BC125", True, 6, iod=0.5, label="car"),
                frame_data(48, 10, 5, 80, 0, "BC125", True, 6, iod=0.5, label="car"),
            ],
        ],
        ["ABC123", "ABC111", "ABC22", "ABC123", "BC125"],
    ],
]


@pytest.mark.parametrize("roi_list,expected", test_data)
def test_plate_analysis(roi_list, expected):
    analyser = ROIPlateAnalyser(roi_id=0, debug=True)

    all_detected_plates = []

    for roi in roi_list:
        detected_plates = analyser.analyse_plates(roi)
        if detected_plates:
            all_detected_plates.extend(detected_plates)

    plate_texts = [plate["plate_text"] for plate in all_detected_plates]

    assert len(plate_texts) == len(expected)
    assert all(
        [
            test_p == exp_p
            for test_p, exp_p in zip(sorted(plate_texts), sorted(expected))
        ]
    )
