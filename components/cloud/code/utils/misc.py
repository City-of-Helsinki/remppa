import re


def get_float(d, default=None):
    """Get a float value, or a default if not conversible
    Args:
        d (Any): Value to be converted
        default (Any): Default if value can not be converted
    Returns:
        float or Any
    """
    try:
        return float(d)
    except:
        return default


def safe_name(s):
    """Make a string safe for a file name
    Args:
        s (str): Proposed file name
    Returns:
        str: file name safe for e.g. ext3/ext4 file systems
    """
    return safe_string(s, "-_.")


def safe_string(s, valid, no_repeat=False):
    """Return a safe string:
        - Replace non alphanumeric characters with _ .
        - If character found in String `valid` do not replace.
    Args:
        s (str): Proposed file name
        valid (str): String of valid characters
        no_repeat (bool): Remove repeated _ characters from output
        Returns:
            str: Safe string
    """
    safe = "".join([c if c.isalnum() or c in valid else "_" for c in s])
    if no_repeat:
        safe = re.sub(r"_+", "_", safe)
    return safe
