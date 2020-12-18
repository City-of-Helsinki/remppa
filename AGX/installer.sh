#!/bin/bash

cat <<EOF

This script includes some installation procedures on the AGX Xavier.
It can not be run automated. Use it as a reference.

Press any key to print all the steps.

EOF

read
echo '==============================================================='
cat "$0"
exit 1

# NOTE:
#   This script assumes /mnt/m2 is mounted, and has plenty of
#   disk space.

## CUDA should be installed by jetpack or AGX base image!
## Run as the user running services. There are a lot of `sudo` commands!

this_folder=$( pwd )

# It's good to max out power for AGX to build fast
sudo nvpmodel -m 0

## the Basics, some are for developing...

sudo apt-get install -y \
    python3-dev \
    curl \
    encfs \
    imagemagick \
    mc \
    multitail \
    pv \
    python3-venv \
    rsync \
    virtualenv \


curl -L https://bootstrap.pypa.io/get-pip.py | sudo python3
. ~/.profile

## Database: postgresql

wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
sudo apt-get update
sudo apt-get install -y \
    postgresql \
    postgresql-contrib \
    libpq-dev \


. <( cat database.env | grep ^[A-Z] | sed 's/^/export /' )

sudo -u postgres createuser $POSTGRES_USER
sudo -u postgres createdb $POSTGRES_DB
sudo -u postgres psql -c '\x' \
  -c "alter user $POSTGRES_USER with encrypted password '$POSTGRES_PASSWORD';"


## Virtual env for python

test -d ~/Documents/virtualenvs/alpr || {
    mkdir -p ~/Documents/virtualenvs/
    virtualenv -ppython3 ~/Documents/virtualenvs/alpr
}
. ~/Documents/virtualenvs/alpr/bin/activate


## Processor: opencv deps

sudo apt-get install -y \
    cmake \
    build-essential \
    cmake \
    gfortran \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libeigen3-dev \
    libgl1 \
    libglew-dev \
    libglvnd-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgtk2.0-dev \
    libgtk-3-dev \
    libjpeg-dev \
    libpng-dev \
    libpostproc-dev \
    libswscale-dev \
    libtbb-dev \
    libtiff5-dev \
    libtiff-dev \
    libv4l-dev \
    libx264-dev \
    libxvidcore-dev \
    pkg-config \
    python3-dev \
    python3-numpy \
    python3-pytest \
    python3-py \
    qt5-default \
    unzip \
    virtualenv \
    zlib1g-dev \

sudo apt-get clean

## pip packages
pip3 install \
    numpy==1.19.2 \
    scipy==1.5.2 \
    psycopg2==2.8.6 \
    pyAesCrypt==0.4.3 \
    requests==2.24.0 \
    filterpy==1.4.5 \
    imagehash==4.1.0 \
    lap==0.4.0 \
    parse==1.18.0 \
    psutil==5.7.3 \
    pytest==6.1.2 \
    scikit-image==0.17.2 \
    textdistance==4.2.0 \
    Cython==0.29.21 \
    matplotlib==3.3.2 \
    Pillow==7.2.0 \
    PyYAML==5.3.1 \
    scipy==1.5.2 \


## Reader: openalpr deps
sudo apt-get install -y \
    libcurl4-openssl-dev \
    liblog4cplus-1.1-9 \
    liblog4cplus-dev \
    build-essential


## OpenCV:  Run the following segment as root !!
fallocate -l 8G /mnt/m2/swapfile
chmod 600 /mnt/m2/swapfile
mkswap /mnt/m2/swapfile
swapon /mnt/m2/swapfile
echo '/mnt/m2/swapfile swap swap defaults 0 0' >> /etc/fstab
echo 'vm.swappiness = 10' >> /etc/sysctl.conf
sysctl -p

# Get patch for opencv
mkdir -p /mnt/m2/build
cd /mnt/m2/build
git clone https://github.com/jetsonhacks/buildOpenCVXavier
WHEREAMI=$( readlink -f buildOpenCVXavier )

OPENCV_VERSION=4.4.0
ARCH_BIN=7.2
INSTALL_DIR=/usr/local
DOWNLOAD_OPENCV_EXTRAS=NO
OPENCV_SOURCE_DIR=/mnt/m2/build/opencv
CMAKE_INSTALL_PREFIX=$INSTALL_DIR
JETSON_BOARD="Xavier"
JETSON_L4T_STRING=$(head -n 1 /etc/nv_tegra_release)
JETSON_L4T_RELEASE=$(echo $JETSON_L4T_STRING | cut -f 1 -d ',' | sed 's/\# R//g' | cut -d ' ' -f1)
JETSON_L4T_REVISION=$(echo $JETSON_L4T_STRING | cut -f 2 -d ',' | sed 's/\ REVISION: //g' )
JETSON_L4T="$JETSON_L4T_RELEASE.$JETSON_L4T_REVISION"
JETSON_JETPACK="4.2"
JETSON_CUDA=$(cat /usr/local/cuda/version.txt | sed 's/\CUDA Version //g')
cd /usr/local/cuda/include
sudo patch -N cuda_gl_interop.h $WHEREAMI'/patches/OpenGLHeader.patch'

sudo mkdir -p $OPENCV_SOURCE_DIR
sudo chmod 777 $OPENCV_SOURCE_DIR
cd $OPENCV_SOURCE_DIR
git clone https://github.com/opencv/opencv.git
git clone https://github.com/opencv/opencv_contrib.git

cd opencv
git checkout -b v${OPENCV_VERSION} ${OPENCV_VERSION}
cd ../opencv_contrib
git checkout -b v${OPENCV_VERSION} ${OPENCV_VERSION}
cd ../opencv
mkdir -p build
cd build

time cmake \
      -D CMAKE_BUILD_TYPE=RELEASE \
      -D CMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX} \
      -D WITH_CUDA=ON \
      -D CUDA_ARCH_BIN=${ARCH_BIN} \
      -D CUDA_ARCH_PTX="" \
      -D ENABLE_FAST_MATH=ON \
      -D CUDA_FAST_MATH=ON \
      -D WITH_CUBLAS=ON \
      -D WITH_LIBV4L=ON \
      -D WITH_GSTREAMER=ON \
      -D WITH_GSTREAMER_0_10=OFF \
      -D WITH_QT=ON \
      -D WITH_OPENGL=ON \
      -D PYTHON_EXECUTABLE=$( which python3 ) \
      -D BUILD_OPENCV_PYTHON2=OFF \
      -D BUILD_OPENCV_PYTHON3=ON \
      -D WITH_TBB=ON \
      -D CUDA_NVCC_FLAGS="--expt-relaxed-constexpr" \
      -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules \
      ../


# You could use more cores, but likely it's gonna run out of RAM
# This will take a long time.
make -j1

make install
ldconfig
source_so=$( find /usr/local/lib -name 'cv2.*.so' | sort -V | tail -n 1 )
target_so=~/Documents/virtualenvs/alpr/lib/python3.6/site-packages/cv2.so
ln -sfT "$source_so" "$target_so"

python3 -c "import cv2; print(cv2.__version__)"


## Reader: ALPR
# Switch back to normal user.

cd /mnt/m2/build/

# Follow installation for leptonica:
# http://www.leptonica.org/download.html
# Tested with version 1.80.0

# Install tesseract:
# https://github.com/tesseract-ocr/tesseract/
# Tested with github master: Version 5.0.0-alpha.
# Should work with stable 4.1.1

git clone https://github.com/openalpr/openalpr.git
cd openalpr/src && mkdir build && cd build && \
    cmake \
        -D CMAKE_INSTALL_PREFIX:PATH=/usr \
        -D CMAKE_INSTALL_SYSCONFDIR:PATH=/etc \
        -D COMPILE_GPU=1 \
        -D WITH_GPU_DETECTOR=ON \
        .. && \
    make -j $(( $( nproc ) -1 )) && \
    sudo make install && \
    cd ../bindings/python && pip3 install .



## Processor: YOLOv5

# Use other virtualenv for building
deactivate

cd /usr/local/cuda/lib64
sudo ln -s libcurand.so.10.0 libcurand.so.10
cd /mnt/m2/build/
test -d ~/Documents/virtualenvs/build-torch || {
    mkdir -p ~/Documents/virtualenvs/
    virtualenv -ppython3 ~/Documents/virtualenvs/build-torch
}
. ~/Documents/virtualenvs/build-torch/bin/activate
git clone --recursive --branch v1.6.0 http://github.com/pytorch/pytorch
git clone --recursive --branch v0.7.0 https://github.com/pytorch/vision
export USE_NCCL=0
export USE_DISTRIBUTED=0
export USE_QNNPACK=0
export USE_PYTORCH_QNNPACK=0
export TORCH_CUDA_ARCH_LIST="5.3;6.2;7.2"
export PYTORCH_BUILD_VERSION=1.6.0
export PYTORCH_BUILD_NUMBER=1
cd pytorch
python setup.py bdist_wheel

# Go back to our target virtual env
deactivate
. ~/Documents/virtualenvs/alpr/bin/activate
#
pip3 install dist/torch-1.6.0-cp36-cp36m-linux_aarch64.whl
cd /mnt/m2/build/
cd vision
pip3 install .


cd /mnt/m2/build/
git clone https://github.com/ultralytics/yolov5.git
cd yolov5
git checkout $( git rev-list -1 --before="Sep 30 2020" master )
cat <<EOF > setup.py
import pathlib
import pkg_resources
from setuptools import setup, find_packages


with pathlib.Path("requirements.txt").open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement in pkg_resources.parse_requirements(requirements_txt)
    ]

setup(
    name="yolov5",
    install_requires=install_requires,
    packages=find_packages(include=["models", "utils", "utils.*"]),
)
EOF
# do not install the requirements, we'll use manual versions already installed
rm requirements.txt
pip3 install .
pip3 install \
    'tensorboard==2.3.0' \
    'tqdm==4.51.0' \



# hopefully finished fine!
