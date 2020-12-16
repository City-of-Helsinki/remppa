import os
import cv2
from utils import get_valid_plates


def visualize_frame(frame, folder):
    """Show plate results printed on an image. Resulting image is saved to disk.

    Args:
        frame (Dict): Plate data with ALPR results
        folder (str): Folder where image is saved to.
    Returns:
        None

    """

    if not os.path.exists(folder):
        os.mkdir(folder)

    plates = []
    for result in frame["plates"]["results"]:
        plates.append(
            {
                "match": result["plate"],
                "confidence": result["confidence"],
                "coordinates": result["coordinates"],
                "valid_plates": get_valid_plates(result["plate"]),
            }
        )

    base = os.path.basename(frame["path"])
    image = cv2.imread(frame["path"])
    for plate in plates:
        if len(plate["valid_plates"]) > 0:
            valid = plate["valid_plates"][0]
        else:
            valid = ""
        text = "{}({}) {}".format(valid, plate["match"], int(plate["confidence"]))
        shade_text(
            image,
            text,
            (
                plate["coordinates"][3]["x"],
                2 * plate["coordinates"][3]["y"] - plate["coordinates"][0]["y"],
            ),
        )

    cv2.imwrite(os.path.join(folder, frame["ROI"] + base), image)


def shade_text(image, text, org):
    """Add a text with shadow to an image. Image object is modified in place.

    Args:
        image (np.array): Image data
        text (str): Text to add on image.
        org (tuple): x,y coordinates of text upper left corner
    Returns:
        None

    """
    # org = (org[0], org[1])
    font_scale = 0.7
    font = cv2.FONT_HERSHEY_SIMPLEX

    (text_width, text_height) = cv2.getTextSize(
        text, font, fontScale=font_scale, thickness=1
    )[0]

    box_coords = ((org[0], org[1]), (org[0] + text_width + 2, org[1] - text_height - 2))
    rectangle_bgr = (32, 32, 32)
    cv2.rectangle(image, box_coords[0], box_coords[1], rectangle_bgr, cv2.FILLED)
    cv2.putText(
        image, text, org, font, fontScale=font_scale, color=(235, 255, 255), thickness=1
    )
