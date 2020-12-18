FROM ubuntu:18.04
MAINTAINER ville.rantanen@reaktor.com

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get -y install \
        curl \
        build-essential \
        cmake \
        git \
        libcurl3-dev \
        libleptonica-dev \
        liblog4cplus-dev \
        libopencv-dev \
        libtesseract-dev \
        locales \
        python3-dev \
    && apt-get clean && \
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


RUN git clone https://github.com/openalpr/openalpr.git
RUN cd openalpr/src && mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -DCMAKE_INSTALL_SYSCONFDIR:PATH=/etc .. && \
    make -j $(( $( nproc ) -1 )) && \
    make install && \
    cd ../bindings/python && python3 setup.py install

ADD code/requirements.txt /
RUN pip3 install -r /requirements.txt && rm -rf /root/.cache

RUN useradd --create-home kilpi
USER kilpi
ADD code/ /code
ADD code/openalpr.conf /openalpr.conf
WORKDIR /code
CMD ["python3","plate_reader.py"]
