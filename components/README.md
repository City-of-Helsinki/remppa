# Software Overview

The software consists of four modules:

- Database & Database Import
- Processor
- Reader
- Cloud

Below are short descriptions of module functionalities and instructions for the Docker based development environment. Please see [Running on AGX](../AGX/README.md) on how to the run code on the actual device.

## .env file

File contents example:

```
DEBUG=True
HASH_SALT=bBV8cb29wcecz
DATABASE_IMPORT=/database-import/import.csv
YOLO5_WEIGHTS=/tmp/yolov5s.pt
LOG_PLAINTEXT_PLATE=False
```

- HASH_SALT is used to create unique hashes of each license plate
- DATABASE_IMPORT points to CSV file with plates, and their emissions
- YOLO5_WEIGHTS, points to file which is used as the weights. Weights
  can be yolov5s.pt for fast but inaccurate results, yolov5m.pt for
  better results but slower performance. yolov5l.pt exists, but is
  not encouraged to be used.
- LOG_PLAINTEXT_PLATE when set True, print the plaintext license
  plate in the log. This setting should not be used in production.

## Database

- PostgreSQL database
- Demo DB for storing hashed license plates, emissions and vehicle types
- Placeholder code for reporting:
  - Events are saved in a queue.
  - Allows some fusing of multiple recognititions
  - Sent at regular intervals, with a failsafe for internet connection break.
- Initialization:
  - Setup DB environment variables in database.env (e.g. change password)
  - Start database: `make start-db`
  - Provide data in CSV format, currently row format is: `PLA-TE;car-type;gas-type;co2`
  - Specify location of file in DATABASE_IMPORT environment variable
  - Import data: `make import`
- DB must exist before running detections

## Processor

- Monitor a ROI in the camera feed.
- A diff is calculated over time, and when threshold exceeded,
  ROI saved to cache folder with time stamp
- Perform object detection to detect vehicles in ROIs
- Perform tracking to keep track of vehicles between frames
- Write object detection and tracking metadata to same folder as images

## Reader

- OpenALPR recognizes plates from the ROI images.
- If recognized, data matched with emission data in database
- unrecognized still counts as an average-vehicle
- The same vehicle probably is seen in several frames, some
  of which are recognized and some not. A time threshold separates
  separate car events.

## Cloud

- Web component for controlling and debugging license plate detection
- Only used with the AGX Xavier environment, not with the other docker
  containers.

## Development environment

Software can be tested during development via Docker containers:

- Add MP4 video to process and test to videos/ - folder.
- Add mask PNG file with ROIs marked with white color to masks/ - folder.
- Add warp JSON file with point correspondences (or empty array) to warps/ - folder.
  (Not an absolutely necessary step)
- `make start-db` (if not already running)
- `make test`(run unit tests)
- `make test-processor` (to create ROI images and metadata)
- `make test-reader` (detect license plates)
  - Note: running test-reader will delete ROI images. You need to re-run
    test-processor to run test-reader again.

## Python Code Formatting

- [Black](https://black.readthedocs.io/) library is used for code formatting
- Black can be used by installing virtual environment (requirements.txt in this folder)
- Formatting can be done through Makefile target start-formatter or by using some IDE integration
