import cv2
import numpy as np
import requests
import time
import json
import os
import argparse
from threading import Thread
import logging
import psutil
import shutil

from camera.camera import Camera
from processor.detector import main as detector

logging.basicConfig(level=logging.INFO)


class Communicator:
    """Communicator polls the new mode of the system from a cloud service,
    and starts processing locally.

    Args:
         url (str): URL to cloud service api.
         id (str): Identifier of this camera system.
         token (str): Secret token to allow uploading to cloud service.
         save_record (str): Path to folder where recordings go to.
         default_mode (str): Initial mode for the processing, e.g. "pause".

    """

    def __init__(self, url, id, token, save_record, default_mode):

        self.cam = Camera()
        self.detector = detector(self.cam)
        self.detector_thread = None
        self.save_record = save_record
        self.default_mode = default_mode
        self.running = False
        self.state = {
            "server": {"mode": default_mode},
            "client": {"mode": default_mode},
        }
        self.mode_change = False
        self.last_mode_check = 0
        self.save_path = "/dev/shm/"
        self.disk_space = {}

        self.url = url
        self.id = id
        self.token = token
        self.mask_image = (np.ones((100, 100)), 0, [])

    def _mask_update(self, force=False):
        """Reload ROI mask

        Args:
            force (bool): Force reload, otherwise do not reload until 10 minutes passed.

        Returns:
            None:

        """
        if not force:
            if time.time() - self.mask_image[1] < 600:
                # update mask only every 10 minutes
                return

        self.mask_path = os.getenv("MASK_PATH", "")
        if os.path.exists(os.path.join(self.mask_path, "cam0.png")):
            mask_image = cv2.imread(
                os.path.join(self.mask_path, "cam0.png"), cv2.IMREAD_GRAYSCALE
            )

        else:
            mask_image = self.mask_image
        # mask_image = np.clip(mask_image.astype('float')/255, 0.75, 1.0)
        t, i = self.cam.read()
        if t:
            w, h = self._get_small_size(i)
            mask_image = cv2.resize(mask_image, (w, h))
            contours, _ = cv2.findContours(
                mask_image.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )
            self.mask_image = (mask_image, time.time(), contours)

    def _get_small(self, i):
        """Create a thumbnail of camera view

        Args:
            i (np.array): The image.

        Returns:
            str: Path to saved thumbnail

        """
        i = i.copy()
        fname = os.path.join(self.save_path, "small.jpg")
        w, h = self._get_small_size(i)
        y1, y2, x1, x2 = self._get_crop_corners(i)
        i = cv2.rectangle(i, (x1, y1), (x2, y2), (64, 86, 255), thickness=4)

        resized = cv2.resize(i, (w, h))
        try:
            resized = cv2.drawContours(
                resized.copy(), self.mask_image[2], -1, (64, 255, 83), 3
            )
            # resized = (resized.astype('float') * self.mask_image[0]).astype('uint8')
        except Exception as e:
            logging.warning(e)

        cv2.imwrite(fname, self._timestamp(resized))
        return fname

    def _get_small_size(self, i):
        """Get the size for thumbnail

        Args:
            i (np.array): The image.

        Returns:
            (int,int): Width and Height

        """
        h = 480
        w = int(i.shape[1] * h / i.shape[0])
        return w, h

    def _get_cropped(self, i):
        """Get the cropped center image for focus adjust

        Args:
            i (np.array): The image.

        Returns:
            str: Path to saved cropped image

        """
        i = i.copy()
        fname = os.path.join(self.save_path, "crop.jpg")
        y1, y2, x1, x2 = self._get_crop_corners(i)

        cv2.imwrite(fname, self._timestamp(i[y1:y2, x1:x2, ::]))
        return fname

    def _get_crop_corners(self, i):
        """Get the bounding box for center crop

        Args:
            i (np.array): The image.

        Returns:
            (int,int,int,int): Top, Bottom, Left and Right coordinates

        """
        h = 480
        w = int(i.shape[1] * h / i.shape[0])
        midx = int(i.shape[1] / 2)
        midy = int(i.shape[0] / 2)
        x1 = int(midx - w / 2)
        x2 = x1 + w
        y1 = int(midy - h / 2)
        y2 = y1 + h
        return y1, y2, x1, x2

    def _check_diskspace(self):
        """Calculate and update how fast we run out of diskspace"""
        if self.save_record:
            try:
                diskused = shutil.disk_usage(self.save_record)
                self.disk_space["now"] = {
                    "free": diskused.free,
                    "freeGb": round(diskused.free / 2 ** 30, 2),
                    "time": time.time(),
                }
            except (FileNotFoundError, ZeroDivisionError) as e:
                logging.warning(e)

    def _refresh_mode(self):
        """Update cloud service for our current state, and get new wanted state"""
        if time.time() - self.last_mode_check < 5:
            return
        self.last_mode_check = time.time()
        if self.url is None:
            return
        try:
            logging.info(self.cam.disk_space)

            try:
                detector_lag = str(
                    round(
                        len(self.detector.image_cache)
                        * self.detector.keep_sending_after_phash_diff,
                        1,
                    )
                )
            except Exception as e:
                detector_lag = "NA"
                logging.warning(e)

            self._check_diskspace()

            client_state = {
                "mode": self.state["server"]["mode"],
                "exposure": round(self.cam.exposure, 2),
                "exposure_modifier": self.cam.exposure_modifier,
                "frame_no": self.cam.frame,
                "frame_rec": self.cam.recorded_frame,
                "disk_free_gb": self.disk_space.get("now", {}).get("freeGb", "NA"),
                "fps": round(self.cam.fps, 2),
                "camera_working": self.cam.working,
                "load": str(psutil.getloadavg()),
                "memory_used_%": psutil.virtual_memory().percent,
                "detector_lag": detector_lag,
            }
            values = {
                "token": self.token,
                "id": self.id,
                "state": json.dumps(client_state),
            }
            r = requests.post(self.url + "/state", data=values)
            new_state = r.json()
            self.mode_change = (
                self.state["server"]["mode"] != new_state["server"]["mode"]
            )
            if self.mode_change:
                logging.info(
                    "Running mode changed to: {}".format(new_state["server"]["mode"])
                )
            new_state["client"]["mode"] = new_state["server"]["mode"]

            try:
                self.cam.exposure_modifier = float(
                    new_state["server"]["exposure_modifier"]
                )
            except KeyError:
                pass
            self.state = new_state
        except Exception as e:
            logging.error(e)

    def _run(self):
        """Keep running the controller"""
        pause_time = 0.5
        while self.running:
            time.sleep(pause_time)
            try:
                self._refresh_mode()
                if self.mode_change:
                    # reset evertrhing
                    logging.info(self.state)
                    self._mask_update(True)
                    self.cam.release()
                    self.cam.save_path = None
                    self.cam.recorded_frame = 0
                    self.cam.autoexposure_interval = 10
                    self._detector_stop()
                    time.sleep(1)
                    self.mode_change = False

                if self.state["client"]["mode"] == "pause":
                    pause_time = 0.5
                    continue

                if self.state["client"]["mode"] == "calibrate":
                    pause_time = 0.5
                    self.cam.autoexposure_interval = 2
                    self._mask_update(True)

                if self.state["client"]["mode"] == "record":
                    pause_time = 5
                    # Note. for recording, save_path must be set _before_
                    # the cam is started
                    self.cam.save_path = self.save_record

                if self.state["client"]["mode"] in ("calibrate", "record", "detect"):
                    if self.cam.working:
                        t, i = self.cam.read()
                        self._send(self._get_small(i), "small")
                        self._send(self._get_cropped(i), "crop")
                        logging.info("Images sent {}".format(time.strftime("%X")))

                if self.state["client"]["mode"] == "detect":
                    pause_time = 10
                    if self.cam.working:
                        self._detector_run()

                # If not pause, make sure camera is on
                self.cam.start()

            except Exception as e:
                logging.error(e)

    def _send(self, fname, image_type):
        """Send file to cloud service

        Args:
            fname (str): Path to file.
            image_type (str): Type of the image (small or crop).

            Returns:
                (requests.Response): Response of the post
        """
        files = {"file": (os.path.basename(fname), open(fname, "rb"))}
        values = {"token": self.token, "id": self.id, "type": image_type}
        r = requests.post(self.url + "/upload", files=files, data=values)
        return r

    def start(self):
        """Start the controller process"""
        # some stuff doesnt work in threads??
        # self.thread = Thread(target=self.run, args=())
        # self.thread.daemon = True
        # self.thread.start()
        self.running = True
        self._run()

    def stop(self):
        """Stop the controller process"""
        self.running = False

    def _detector_run(self):
        """Start the camera detector"""
        if self.detector.keep_processing:
            return
        self.detector_thread = Thread(target=self.detector.start, args=())
        self.detector_thread.daemon = True
        self.detector_thread.start()

    def _detector_stop(self):
        """Stop the camera detector"""
        self.detector.stop()

    def _timestamp(self, i):
        """Place timestamp to an image

        Args:
            i (np.array): Image data.

        Returns:
            (np.array): Image data with timestamp
        """
        font = cv2.FONT_HERSHEY_SIMPLEX
        org = (10, 30)
        fontScale = 1
        color = (255, 255, 255)
        thickness = 2
        i = cv2.putText(
            i,
            time.strftime("%X"),
            org,
            font,
            fontScale,
            (0, 0, 0),
            2 * thickness,
            cv2.LINE_AA,
        )
        return cv2.putText(
            i, time.strftime("%X"), org, font, fontScale, color, thickness, cv2.LINE_AA
        )


def get_options():
    """Read command line options

    Returns:
        (Namespace): Options
    """
    parser = argparse.ArgumentParser("Store images to disk &/ cloud.")
    parser.add_argument(
        "--url", type=str, default=None, help="URL base of cloud component", dest="url"
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Upload token for cloud infra",
        dest="token",
    )
    parser.add_argument(
        "--id",
        type=str,
        default=None,
        help="Name of this instance for cloud infra",
        dest="id",
    )
    parser.add_argument(
        "--mode",
        type=str,
        help="Default action when starting the service",
        dest="mode",
        default="pause",
    )
    parser.add_argument(
        "--save_path",
        type=str,
        default=None,
        help="path to save files.",
        dest="save_path",
    )

    if os.getenv("RUNNING_IN_DOCKER", "false").lower().strip() == "true":
        # get docker/other ENV as arguments
        commandline = []
        switches = ("--url", "--token", "--id", "--mode", "--save_path")
        keys = ("UPLOAD_URL", "UPLOAD_TOKEN", "UPLOAD_ID", "INITIAL_MODE", "SAVE_PATH")
        for switch, key in zip(switches, keys):
            if os.getenv(key, False):
                commandline.extend([switch, os.getenv(key)])

        args = parser.parse_args(commandline)
    else:
        args = parser.parse_args()
    return args


if __name__ == "__main__":
    opts = get_options()
    # width, height = 4192, 3120
    logging.info(opts)

    try:
        comm = Communicator(opts.url, opts.id, opts.token, opts.save_path, opts.mode)
        if opts.url:
            time.sleep(1)
            comm.start()

        while True:
            time.sleep(10)

    except KeyboardInterrupt:
        logging.info("Exiting")
        comm.stop()
        time.sleep(1)
