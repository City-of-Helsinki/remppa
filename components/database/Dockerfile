FROM python:3.8-alpine
MAINTAINER ville.rantanen@reaktor.com

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
RUN pip3 install psycopg2 && rm -rf /root/.cache

COPY code/ /code/
WORKDIR /code
