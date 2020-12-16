# -*- coding: utf-8 -*-
import re
import textdistance
from datetime import datetime

MIN_PLATE_LENGTH = 3
MAX_PLATE_LENGTH = 6
VALID_PLATE_RE = re.compile(r"[A-C-E-O-Q-V-X-Z][A-Z,Ä,Ö]{1,2}[1-9]\d{0,2}")


def get_valid_plates(detection):
    """Convert detected plate to possible Finnish plates

    Args:
        detection (str): Text found in register plate

    Returns:
        List: List of possible alterations of plate
    """
    if not detection:
        return []

    valid_set = set()
    candidates = []

    for attempt in (
        detection,
        get_alt_representation(detection),
    ):
        detlen = len(attempt)

        for num_chars in range(MIN_PLATE_LENGTH, MAX_PLATE_LENGTH + 1):
            candidates += [
                attempt[i : (i + num_chars)]
                for i in range(max(0, detlen - num_chars + 1))
            ]

        for c in candidates:
            try:
                valid_set.add(VALID_PLATE_RE.search(c.upper())[0])
            except TypeError:
                pass

    return sorted(list(valid_set), key=len, reverse=True)


def get_alt_representation(plate):
    """Get alternative representation for given plate because
    in Finnish license plates 0 looks like letter O and letter I in turn looks like 1,
    and 5 like S

        Args:
            plate (str): Text found in register plate

        Returns:
            str: Modified plate text
    """

    fixed_plate = plate

    # Hopefully fix some I to 1 but compromise plates like AA-11 for AAI-1
    if len(fixed_plate) > 3 and "I" in fixed_plate[3:]:
        fixed_plate = fixed_plate[:3] + fixed_plate[3:].replace("I", "1")

    # Hopefully fix some 0 to O and 5 to S but compromise plates like AA-00 for AAO-0
    if len(fixed_plate) > 3 and "0" in fixed_plate[:3]:
        fixed_plate = fixed_plate[:3].replace("0", "O") + fixed_plate[3:]
        fixed_plate = fixed_plate[:3].replace("5", "S") + fixed_plate[3:]

    return fixed_plate


def get_obfuscated_plate(plate):
    """Obfuscate all letters as A, and numbers as 1

    Args:
        plate (str): Text found in register plate

    Returns:
        str: Obfuscated plate text
    """

    return re.sub(r"[0-9]", "1", re.sub(r"[a-zA-Z]", "A", plate))


def rm_duplicates_1edit_away(plates, prev_plates):
    """Remove reading errors from plate reading matches, that are only 1 edit away

    Args:
        plates (List): List of possible hits from plate reader
        prev_plates (List): List of plates seen earlier

    Returns:
        List: plates with near duplicates removed
    """
    plates.sort(key=len, reverse=True)
    clusters_list = []

    for p in plates:
        found = False
        for c in clusters_list + prev_plates:
            # Note: Unknown plates start with non alpha character
            if c[0].isalpha() and textdistance.levenshtein.distance(p, c) <= 1:
                found = True
                break

        if not found:
            clusters_list.append(p)

    return clusters_list


def timestamp_to_date(timestamp):
    """Format epoch timestamp to a date format compatible with filenames.

    Args:
        timestamp (float): A timestamp

    Returns:
        str: Formatted date
    """
    # 2020_09_24_08_29_48_114 > datetime
    return datetime.strptime(timestamp, "%Y_%m_%d_%H_%M_%S_%f")
