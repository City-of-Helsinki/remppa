#!/bin/bash


this_folder=$( pwd )
. ~/Documents/virtualenvs/alpr/bin/activate
. <( cat database.env | grep ^[A-Z] | sed 's/^/export /' )
. <( cat .env | grep ^[A-Z] | sed 's/^/export /' )


test -f "$MASK_PATH"/cam0.png || {
  convert -size 1920x1080 xc:black \
      -fill white -stroke white \
      -draw "rectangle 320,400 920,1060" \
      -draw "rectangle 1020,400 1620,1060" \
      "$MASK_PATH"/cam0.png
}
mkdir -p "$POLL_FOLDER"

# start processor
store=$( readlink -f ~/Documents/video-store/ )/$( date +%F )
mkdir -p "$store"

cd "$this_folder"
cd ../components/processor/code
python3 -m controller.controller \
  --id "$UPLOAD_ID" \
  --url "$UPLOAD_URL" \
  --token "$UPLOAD_TOKEN" \
  --save_path "$store"  2>&1 | tee -a "$store"/processor.log

