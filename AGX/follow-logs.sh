#!/bin/bash


store=$( readlink -f ~/Documents/video-store/ )/$( date +%F )

mkdir -p $store
multitail "$store/processor.log" "$store/reader-00.log" "$store/reader-01.log"


