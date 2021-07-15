#!/usr/bin/env bash

if [[ -f "$(pwd)/OUT/hotwaters_lowres.mp4" ]]
then
	echo "The lowres video file exists: you've already downloaded the assets."
	exit 0
fi

OUT_URL="https://www.dropbox.com/sh/gxt2n4n558kgsmw/AABMGfyH78gh0bpFq_e5oa3ha?dl=1"

curl -L $OUT_URL > OUT.zip
unzip $(pwd)/OUT.zip -d $(pwd)/OUT
rm OUT.zip
