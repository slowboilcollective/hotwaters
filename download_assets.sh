#!/usr/bin/env bash

if [[ -d "$(pwd)/assets/cache_fluid_e7cf141b" ]]
then
	echo "Some of the files already exist: it seems you've already downloaded the assets."
	exit 0
fi

ASSETS_URL="https://www.dropbox.com/sh/9atjdsylsgxe7oa/AAAjAOgwYNevrSYhED_3qtida?dl=1"
curl -L $ASSETS_URL > assets.zip
unzip $(pwd)/assets.zip -d $(pwd)/assets
rm assets.zip
