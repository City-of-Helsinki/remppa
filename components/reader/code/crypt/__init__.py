import pyAesCrypt
import io
from os import stat, getenv
import cv2

bufferSize = 64 * 1024
password = getenv("ENCRYPT_PASSWORD")


def encrypt_image(path, img):
    is_success, buffer = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 97])
    io_buf = io.BytesIO(buffer)
    with open(path, "wb") as fp:
        pyAesCrypt.encryptStream(io_buf, fp, password, bufferSize)


def read_encrypted_image(path):
    io_buf = io.BytesIO()
    encFileSize = stat(path).st_size
    with open(path, "rb") as fp:
        pyAesCrypt.decryptStream(fp, io_buf, password, bufferSize, encFileSize)
    return io_buf.getbuffer()
