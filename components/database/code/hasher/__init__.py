import hashlib
import base64
import os

HASH_SALT = os.getenv("HASH_SALT", "").encode("utf-8")


def create_hash(p):
    """Hash a license plate
    Args:
        p (str): License plate
    Returns:
        str: Hashed string
    """
    return base64.b64encode(hashlib.md5(HASH_SALT + p.encode("utf-8")).digest()).decode(
        "utf-8"
    )
