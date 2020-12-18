# Software Overview

The software consists of four modules:

- Database & Database Import
- Processor
- Reader
- Cloud

Below are short descriptions of module functionalities and
instructions for the Docker based development environment.
Please see [Running on AGX](../AGX/README.md) on how to the
run code on the actual device.

Software is running on Python 3.6 on AGX, but should work with newer
Python too (tested with Python 3.8).

The recommended development environment is with Docker:

- Running requires at least 4GB RAM in the Docker environment!
- You can use any IDE to edit the code, but often it's best to leave
  the running for Docker (some of the libraries may be hard to obtain
  otherwise)
- Developing directly on the AGX is of course the easiest.


## .env file

You must create your own .env file. Start by copying the example:
`cp env.example .env` and then edit the .env.

File contents example:

```
DEBUG=True
HASH_SALT=bBV8cb29wcecz
DATABASE_IMPORT=/database-import/import.csv
YOLO5_WEIGHTS=/tmp/yolov5s.pt
LOG_PLAINTEXT_PLATE=False
ROI=0
```

- HASH_SALT is used to create unique hashes of each license plate
- DATABASE_IMPORT points to CSV file with plates, and their emissions
- YOLO5_WEIGHTS, points to file which is used as the weights. If it doesn't
  exist, it's downloaded. Weights can be yolov5s.pt for fast but
  inaccurate results, yolov5m.pt for better results but slower
  performance. There is the large yolov5l.pt, but is not encouraged to
  be used.
- LOG_PLAINTEXT_PLATE when set True, print the plaintext license
  plate in the log. This setting should not be used in production.
- ROI: The Region of interest index to follow with plate reader. Increase if
  you have more than one ROI, and you want to read from another ROI.

## Database

- PostgreSQL database is used to store:
  - Hashed license plates, emissions and vehicle types
  - A cache of emission data, to be sent to a cloud API
- Initialization:
  - Setup DB environment variables in database.env (e.g. change password)
  - Start database: `make start-db`
  - Provide data in semicolon separated format, currently row format is:
   **PLA-TE;car-type;gas-type;co2**
  - Specify location of the file in DATABASE_IMPORT environment variable
    in .env file
  - Import data: `make import`
- DB must exist before running detections:
  - Validating plates against the database is not implemented, as not
    real data was received during the development.
- Placeholder code for reporting:
  - Events are saved in a cache DB.
  - Send cache at regular intervals, with a failsafe for internet
    connection break.
  - Endpoint where to send is not included in this project.

## Processor

In the Docker container:

- Monitor a ROI in a video feed.
- Movement is detected in the ROI, and when threshold exceeded,
  ROI image saved to cache folder with time stamp
- Perform object detection to detect vehicles in ROIs
- Perform tracking to keep track of vehicles between frames
- Write object detection and tracking metadata to same folder as images

In the AGX Xavier hardware environemnt, in addition, the processor:

- Opens the camera device to stream images for ROI monitor
- Polls the cloud component for instructions
- Sends status reports to the cloud component

## Reader

- OpenALPR recognizes plates from the ROI images.
- The same vehicle probably is seen in several frames, some
  of which are recognized and some not. A time threshold separates
  separate car events.
- If recognized, data matched with emission data in database
- unrecognized still counts as an average-vehicle
  (average calculation not implemented)


## Cloud

- Web component for controlling license plate detection
- Only used with the AGX Xavier environment, not with the other docker
  containers.
- It shows thumbnails sent by the Processor so that positioning and
  focusing of the camera can be performed.
- A simple GUI allows stopping and running of the plate detection
- The web component has a placeholder code for accepting emission data
  to be saved from the system.
- See the [README](cloud/README.md) for more information

## Development environment

Software can be tested during development via Docker containers:

- create the .env file with `cp env.example .env` and modify to your liking.
- Demo video and masks exist, but you can also add your own videos:
  - Add MP4 video to process and test to [videos](processor/videos/) folder.
  - Add mask PNG file with ROIs marked with white color to [masks](processor/masks/) folder.
  - Add warp JSON file with point correspondences (or empty array) to [warps](processor/warps/) folder.
    (Not an absolutely necessary step, if camera image is not distorted much)
- `make build` (to prebuild all images)
- `make start-db` (start database)
- `make import` (import a small test database)
- `make test` (run unit tests)
- `make test-processor` (to create ROI images and metadata)
  - processor/crop_images/ should now be populated with JPG and JSON file pairs
- `make test-reader` (detect license plates)
  - Note: running test-reader will delete ROI images. You need to re-run
    test-processor to run test-reader again.
  - At the end of the reader run, you should see a line like:
    **INFO:root:ROI: 0, PLA-TE**,
    where PLA-TE is the license plate the reader found. That means the
    plate was found.


## Python Code Formatting

- [Black](https://black.readthedocs.io/) library is used for code formatting
- Black can be used by installing virtual environment (requirements.txt in this folder)
- Formatting can be done through Makefile target start-formatter or by using some IDE integration
