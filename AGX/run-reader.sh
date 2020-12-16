#!/bin/bash

set -x
this_folder=$( pwd )
. ~/Documents/virtualenvs/alpr/bin/activate
. <( cat database.env | grep ^[A-Z] | sed 's/^/export /' )
. <( cat .env | grep ^[A-Z] | sed 's/^/export /' )


export OPENALPR_CONFIG="$this_folder"/openalpr.conf
store=$( readlink -f ~/Documents/video-store/ )/$( date +%F )
mkdir -p "$store"
cd ../components/reader/code
ROI="$1" python3 plate_reader.py 2>&1 | tee -a "$store"/reader-"$1".log
