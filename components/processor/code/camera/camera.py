import cv2
import time
from datetime import datetime
import os
import subprocess
import numpy as np
from threading import Thread
import shutil
import logging

logging.basicConfig(level=logging.INFO)


class Camera:
    """Camera polling service.
    Serves the latest image, and keeps exposure in check.,

     Args:
         camera (int): Identifier for v4l2 camera. If left empty,
                       uses predefined gstreamer options known to work
                       on AGX Xavier with e-con130 camera.

    """

    def __init__(self, camera=None):
        self.src = camera
        self.v4l2id = None
        self.cap = None
        self.exposure = 50.0
        self.running = False
        self.image = None
        self.thread = None
        self.pthread = None
        self.save_path = None
        self.save_set = datetime.now().strftime("%H%M")
        self.frame = 0
        self.frame_date = ""
        self.recorded_frame = 0
        self.enough_disk = False
        self.disk_space = {}
        self.working = False
        self.fps = 0
        self._init_camera()

        # auto exposure
        self.adjuster = None
        self.binn = 32
        self.min_exposure = 1.0
        self.max_exposure = 3000.0
        self.exposure_modifier = 1.0
        self.autoexposure_interval = 5
        self.autoexposure_debug = False
        self._set_adjuster()

    def _init_camera(self):
        """Initialize camera (gstreamer options)

        Returns:
            None:

        """
        if self.src is None:

            width, height = 1920, 1080

            gstreamer = " ! ".join(
                [
                    "v4l2src device=/dev/video0",
                    "video/x-raw,width={},height={},format=(string)UYVY",
                    "videoconvert",
                    "appsink",
                ]
            ).format(width, height)
            logging.info(gstreamer)
            self.src = gstreamer
            self.v4l2id = 0

    def _set_adjuster(self):
        """Sets a function used to adjust exposure

        Returns:
            None:
        """
        binn = self.binn
        ypoints = [1.5, 1.1, 1, 1 / 1.5]
        xpoints = [0, 5, 8, 31]
        adjuster = np.interp(list(range(binn)), xpoints, ypoints)

        self.adjuster = adjuster

    def autoexposure(self):
        """Adjust exposure slightly. Run continuously to reach correct exposure."""
        if self.v4l2id is None:

            # no way of controlling exposure
            return

        new_value = self.exposure
        image = cv2.cvtColor(
            cv2.resize(self.image, dsize=(300, 300)), cv2.COLOR_BGR2GRAY
        )
        image = np.uint8(np.float32(image[100:200, 100:200]) / self.exposure_modifier)
        # Read only the center of image!
        freq, bins = np.histogram(image, bins=self.binn, range=[0, 255])
        freq = freq / sum(freq)
        #
        multiplier = np.sum(self.adjuster * freq)
        new_value *= multiplier
        # work within sensible values
        new_value = min(self.max_exposure, new_value)
        new_value = max(self.min_exposure, new_value)
        is_same = (
            int(self.exposure) * 0.97 <= int(new_value) <= int(self.exposure) * 1.03
        )
        if self.autoexposure_debug:
            max_non_zero = np.max([i for i, x in enumerate(freq) if x > 0.01])
            logging.info(
                """
    Freqs   {freqs}
    freq[0] {freq0}
    freq[1] {freq1}
    maxfreq {maxfreq}
    maxnon0 {maxn}
    expo mult {emult}
    multiplier {mult}
    new_value {new_value}
    old_value {old_value}
    is_same   {is_same}
    """.format(
                    freqs=[round(x, 2) for x in freq],
                    freq0=round(freq[0], 4),
                    freq1=round(freq[-1], 4),
                    maxfreq=np.argmax(freq),
                    maxn=max_non_zero,
                    emult=self.exposure_modifier,
                    mult=np.sum(self.adjuster * freq),
                    new_value=new_value,
                    old_value=self.exposure,
                    is_same=is_same,
                )
            )

        if is_same:
            # do not commit change if change too small
            return
        self.exposure = new_value
        self._set_exposure()

    def _set_exposure(self):
        """Set exposure using command line tool.
        The current driver does not accept values from openCV
        """
        if self.v4l2id is not None:
            p = subprocess.Popen(
                "v4l2-ctl -d /dev/video{} -c exposure_time_absolute={}".format(
                    self.v4l2id, int(self.exposure)
                ),
                shell=True,
            )
            stdout, stderr = p.communicate()

    def check_diskspace(self):
        """Calculate how fast we run out of diskspace"""
        if self.save_path:
            try:
                diskused = shutil.disk_usage(self.save_path)
                self.enough_disk = diskused.free / diskused.total > 0.05

                if "first" not in self.disk_space:
                    self.disk_space["first"] = {
                        "free": diskused.free,
                        "time": time.time(),
                    }
                    return

                self.disk_space["now"] = {
                    "free": diskused.free,
                    "freeGb": round(diskused.free / 2 ** 30, 2),
                    "time": time.time(),
                }

                dfree = (
                    self.disk_space["now"]["free"] - self.disk_space["first"]["free"]
                )
                dtime = (
                    self.disk_space["now"]["time"] - self.disk_space["first"]["time"]
                )
                speed = -(dfree) / (dtime)
                if speed == 0:
                    tleft = 0
                else:
                    tleft = (self.disk_space["now"]["free"]) / speed

                self.disk_space["speed"] = {
                    "dfree": dfree,
                    "dtime": dtime,
                    "speedM/s": round(speed / 2 ** 20, 2),
                    "time_left_H": round(tleft / 3600, 2),
                }

            except (FileNotFoundError, ZeroDivisionError) as e:
                logging.warning(e)

    def isOpened(self):
        """Check if camera is in use

        Returns:
            bool: True if camera is in use
        """

        return self.working

    def read(self):
        """Get latest image from camera. Mimick cv2.VideoCapture behavior

        Returns:
            bool: True if image acquisition works
            np.array: Image data
        """
        try:
            return self.working, self.image.copy()
        except:
            return False, None

    def release(self):
        """Stop reading camera. Mimick cv2.VideoCapture behavior"""
        self.running = False

    def _run(self):
        """Enter capturing loop"""
        self._set_exposure()
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_GSTREAMER)
        self.frame = 0
        self.recorded_frame = 0
        while self.running:
            t, i = self.cap.read()
            self.working = t
            if t:
                self.image = i
                self.frame += 1
                self.frame_date = datetime.now()
            time.sleep(0.05)
            # simulate 20FPS, camera driver might crash if polling too rapid

        self.cap.release()
        self.working = False

    def _run_periodicals(self):
        """Other-than-image-acquisition tasks in a separate loop"""
        cam_started = time.time()
        self.save_set = datetime.now().strftime("%H%M%S")
        if self.save_path:
            set_folder = os.path.join(self.save_path, str(self.save_set))
            if not os.path.isdir(set_folder):
                os.mkdir(set_folder)
        saved_frame = 0
        started = 0
        while self.running:
            if self.working:
                if time.time() - started > self.autoexposure_interval:
                    started = time.time()
                    self.autoexposure()
                    self.check_diskspace()
                    self.fps = self.frame / (time.time() - cam_started)
                    logging.info("FPS: {}".format(int(self.fps)))

                if self.save_path:
                    # If save_path is set, save every frame
                    try:
                        if saved_frame != self.frame:
                            saved_frame = self.frame
                            self._save_image(self.image, saved_frame)
                    except FileNotFoundError as e:
                        logging.warning(e)

            time.sleep(0.01)

    def _save_image(self, image, frame):
        """Save image to disk

        Args:
            image (np.array): Image data
            frame (int): Frame number

        Returns:
            None
        """
        if not self.enough_disk:
            logging.error("Not enough disk space")
            return
        set_folder = os.path.join(self.save_path, str(self.save_set))
        if not os.path.isdir(set_folder):
            os.mkdir(set_folder)
        filepath = os.path.join(
            set_folder,
            "cam{}-ts-{}-f-{}.jpg".format(
                self.v4l2id, self.frame_date.strftime("%y-%m-%d-%H-%M-%S.%f"), frame
            ),
        )
        cv2.imwrite(
            filepath,
            cv2.resize(image, (853, 480)),
            [cv2.IMWRITE_JPEG_QUALITY, 95],
        )
        self.recorded_frame = filepath

    def start(self):
        """Start camera service"""
        if self.running:
            return
        self.running = True
        self.thread = Thread(target=self._run, args=())
        self.thread.daemon = True
        self.thread.start()
        self.pthread = Thread(target=self._run_periodicals, args=())
        self.pthread.daemon = True
        self.pthread.start()
