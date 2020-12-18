# Running on NVIDIA AGX Xavier hardware

## Hardware

- NVidia AGX Xavier 32GB
- e-consystems e-cam130 with controller board
- 1TB M2 NVME disk for storage

## Steps to install and run

### Requirements

You need to have a working AGX Xavier, with the camera operational, and
CUDA drivers installed. The tested route included:

- Install the operating system from the camera provider's SD card bundled
  with the camera
- Use the SDKManager from NVIDIA to get CUDA packages for the same
  Jetpack version installed in the camera providers OS image.
- Make sure you have the **/dev/video0** device, for example with:

```
$ v4l2-ctl --list-devices
vi-output, ar1335 30-003c (platform:15c10000.vi:0):
        /dev/video0
```

### Installation of libraries

- Create an .env file based on env.example.
  - Note the OPENALPR_CONFIG should point to the file in this
    folder.
- Check database.env (change password if necessary)
- Use the `installer.sh` script as a guide to install all requirements

### Run the code

Run services with the following commands:

- run.sh: main script to start
- stop.sh: stop processes
- run-tests.sh: run test cases. Make sure services are stopped when running
  the test cases.
- Following scripts are used internally:
  - run-processor.sh: runs the camera, processor and controller services
  - run-reader.sh: runs ALPR service for one ROI. Run several for several ROIs.
  - follow-logs.sh: View all the logs live

## Cloud component

When the system above is running, install the cloud service to a
server with reachable IP address. It could be a virtual server in public
internet, or a local LAN server.

Cloud service is a required component:

- It is the way to set the system to run and pause states.
- It also provides a way to look at a thumbnail from the camera,
  allowing positioning and focusing.

### Installation

- Create [cloud .env](../components/cloud/.env) based on the env.example
  in the same folder.
- Take the UPLOAD_KEY from the .env file from this folder, and insert in [cloud .env](../components/cloud/.env).
- Start up the service: `./run-and-follow.sh`
- It's a good idea to proxy the service through an Nginx server, for nicer
  URLs.
- Test that the server is up by visiting URL: `$UPLOAD_URL/hello`, or like:
  https://my.server/remppa/hello.
- Go to the URL: `$UPLOAD_URL/view/$UPLOAD_ID`,
  e.g.: https://my.server/remppa/view/name-of-the-device .
  You should see a JSON string describing the state of the camera.
- Modify the operation mode:
  - Pause: do nothing, wait for orders
  - Calibrate:
    - Show thumbnail and cropped image. Focus and point the camera correctly if needed.
    - Use the thumbnail to create the ROI mask! Place the mask file in AGX
      $MASK_PATH  folder, with filename `cam0.png`
    - Once ROI mask is in place, change mode to Pause, and back to Calibrate
      to reload the mask. ROI displayed with green lines, crop area in orange.
    - Autoexposure works in faster iteration when in calibration mode.
  - Detect: Enter production mode. Start reading plates, and storing
    emissions (if emission database available).
  - Record: Use recording for development purposes. It stores stills in
    the ~/Documents/video-store/ folder

