# Plate recognizer on AGX Xavier

Automated License Plate Reader with emissions data

Aim of the software:
- View forward facing car lanes with a camera
- Pick up vehicles in the image stream
- Read license plates from car
- Match the license plate in a database of registered emissions for each car
- Report emissions to a server.
- Plate matching happens at the edge, which means no personal information is
  sent anywhere or revealed.
- Images are not sent out, or saved for long periods of time, to prevent
  personal information leaks.

Hardware:
- NVIDIA Jetson AGX Xavier
- e-con Systems e-CAM130A_CUXVR - Multiple Camera Board for NVIDIA Jetson AGX Xavier

## Developer information

The [Components](components/) folder contains the software
components and more information on the testing and development of the
modules.

The actual run environment installation and running scripts are in the
[AGX](AGX/) folder.

The Code contains some test material to get started:
- [License plate for reader](components/reader/code/tests/test_files/plate1.jpg)
- [Test video](components/processor/videos/demo.mp4)
- [ROI mask](components/processor/masks/demo.png)



This project is licensed as GNU AFFERO GENERAL PUBLIC LICENSE v3

Copyright City of Helsinki 2020
