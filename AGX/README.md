AGX local actions

Hardware:

- NVidia AGX Xavier 32GB
- e-consystems e-cam130 with controller board
- 1TB M2 NVME disk for storage

Steps to install and run


- Install the operating system from e-cam130 SD card
- Find and install CUDA packages for the same jetpack, from Nvidia installers
- Create .env based on env.example
- Check database.env
- Use the `installer.sh` script as a guide to install all requirements
- Run services with the following commands:
  - run.sh: main script to start
  - stop.sh: stop processes
  - run-tests.sh: run test cases
  - Following scripts are used internally:
    - run-processor.sh: runs the camera, processor and controller services
    - run-reader.sh: runs ALPR service for one ROI. Run several for several ROIs
    - follow-logs.sh: View all the logs live

When the system above is running, install the cloud service to a
server with reachable IP address. Cloud service is required: It is the
way to set the system to run and pause states. It also provides a way
to look at a thumbnail from the camera, allowing positioning.

- Create components/cloud/.env based on env.example in the same folder.
- Take the UPLOAD_KEY from the .env file from earlier, and insert in components/cloud/.env.
- Start up the service: `./run-and-follow.sh`
- It's a good idea to proxy the service through an Nginx server, for nicer
  URLs.
- Test that the server is up by visiting URL: $UPLOAD_URL/hello
- Go to the public URL, $UPLOAD_URL/view/$UPLOAD_ID
  example: https://my.server/remppa/view/test
  You should see a JSON string describing the state of the camera.
- Modify the operation mode:
  - Pause:  do nothing, wait for orders
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

