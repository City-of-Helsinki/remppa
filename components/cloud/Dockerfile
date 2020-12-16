FROM alpine:3.12
RUN apk add --update \
    tzdata \
    python3 \
    python3-dev \
    build-base \
    curl
RUN curl https://bootstrap.pypa.io/get-pip.py | python3
COPY code/requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt
COPY code /code
WORKDIR /code
CMD python3 start_app.py
