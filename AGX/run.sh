#!/bin/bash

./stop.sh

store=$( readlink -f ~/Documents/video-store/ )/$( date +%F )

./run-processor.sh > /dev/null &
sleep 1
./run-reader.sh 00 > /dev/null &
./run-reader.sh 01 > /dev/null &
sleep 1

./follow-logs.sh


