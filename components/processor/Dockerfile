FROM ubuntu:18.04

# Install system packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    bzip2 \
    ca-certificates \
    g++ \
    git \
    graphviz \
    libgl1-mesa-glx \
    libhdf5-dev \
    locales \
    openmpi-bin \
    python3.6-dev \
    python3-setuptools \
    locales \
    ffmpeg \
    wget \
    curl \
    nano && apt-get clean && \
    curl https://bootstrap.pypa.io/get-pip.py | python3

# Set timezone
ENV TZ=Europe/Helsinki
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# Set the locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN useradd --create-home kilpi

RUN git clone https://github.com/ultralytics/yolov5.git && \
    cd yolov5 && \
    git checkout `git rev-list -1 --before="Oct 15 2020" master`
COPY yolov5_utils/ yolov5
RUN cd /yolov5 && \
    sed -i -e 's,^torch>=.*,torch==1.6.0,' -e 's,^torchvision>=.*,torchvision==0.7.0,' requirements.txt && \
    pip3 install .

ADD code/requirements.txt /
RUN pip3 install --no-cache-dir -r /requirements.txt

ADD code/ /code

USER kilpi
ENV PYTHONPATH "${PYTHONPATH}:/code"
WORKDIR /code
ENTRYPOINT ["python3"]

CMD ["-m", "processor.detector"]
