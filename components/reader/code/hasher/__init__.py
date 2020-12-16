import hashlib
import base64
import os

HASH_SALT = os.getenv("HASH_SALT", "").encode("utf-8")


def create_hash(p):
    return base64.b64encode(hashlib.md5(HASH_SALT + p.encode("utf-8")).digest()).decode(
        "utf-8"
    )
