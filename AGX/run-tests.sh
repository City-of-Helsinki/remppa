#!/bin/bash


this_folder=$( pwd )
. ~/Documents/virtualenvs/alpr/bin/activate
. <( cat database.env | grep ^[A-Z] | sed 's/^/export /' )
. <( cat .env | grep ^[A-Z] | sed 's/^/export /' )


# start tests
set -x
cd "$this_folder"
cd ../components/processor/code
export PYTHONPATH=$( pwd )
export YOLO5_WEIGHTS=/tmp/yolov5s.pt
pytest -p no:cacheprovider .


cd "$this_folder"
cd ../components/reader/code
export PYTHONPATH=$( pwd )
pytest -p no:cacheprovider .

