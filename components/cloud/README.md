# Cloud component

This is a toy example, and should not be used in a production environment.

- Copy the env.example to .env file, and modify.


The cloud component provides:

- A channel to set up working modes for the camera. The camera polls
  the cloud component for changes
- Place to upload thumbnails to confirm the camera works
- An API to upload emission data, if needs be


The API endpoints:

----

**GET:** /hello

Used to test the server


**Response:**

"Hello", 200

----

**POST:** /upload

Upload emission data or thumbnails to the server

**Parameters:**

- id: Identifier name of camera
- token: Secret token to allow uploads
- type: "data" for JSON upload, "small" or "crop" for JPGs

**Response:**

"", 200

----


**GET:** /view/{id}/{image}.jpg

Download thumbnail for web page to view

**Parameters:**

- id: Identifier name of camera
- image: "small" or "crop" for type of image

**Response:**

Image data, 200

----

**GET:** /view/{id}

**Parameters:**

- id: Identifier name of camera

**Response:**

HTML page, 200

----

**POST:** /view/{id}

**Parameters:**

- id: Identifier name of camera
- mode: Set camera to mode: pause, calibrate, record or detect
- exposure_modifier: Set a float value multiplier to modify autoexposure on camera.

**Response:**

HTML page, 200

----

**POST:** /state

**Parameters:**

- id: Identifier name of camera
- token: Secret token to allow uploads
- state: JSON data

State data example:
```
{
    "camera_working": true,
    "detector_lag": "0.0",
    "disk_free_gb": 641.13,
    "exposure": 209.51,
    "exposure_modifier": 1.0,
    "fps": 18.19,
    "frame_no": 329545,
    "frame_rec": 0,
    "load": "(1.69, 1.69, 1.69)",
    "memory_used_%": 16.4,
    "mode": "calibrate",
}
```

**Response:**

"", 200

----

**GET:** /ajax/state/{id}

**Parameters:**

- id: Identifier name of camera

**Response:**

JSON data, 200

----
