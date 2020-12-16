import openalpr
import os

algorithm = openalpr.Alpr(
    "eu", os.getenv("OPENALPR_CONFIG"), "/usr/share/openalpr/runtime_data/"
)
algorithm.set_default_region("fi")
algorithm.set_detect_region(True)


def read_file(path):
    """Read plates from an image file

    Args:
        path (str): Path to an image file

    Returns:
        dict: Results from ALPR, with detected plates
    """
    return algorithm.recognize_file(path)


def read_array(array):
    """Read plates from a numpy array image

    Args:
        array (np.array): image data

    Returns:
        dict: Results from ALPR, with detected plates
    """
    return algorithm.recognize_array(array)
