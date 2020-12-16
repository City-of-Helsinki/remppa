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
- Nvidia Jetson AGX Xavier
- ecam-130


Components folder contains the software components, that can be tested by
using Docker. The actual run environment scripts are in the AGX/ folder

Code contains some test material:
- [License plate for reader](components/reader/code/tests/test_files/plate1.jpg)
- [Test video](components/processor/videos/demo.mp4)
- [ROI mask](components/processor/masks/demo.png)


This project is licensed as GNU AFFERO GENERAL PUBLIC LICENSE v3

Copyright City of Helsinki 2020
