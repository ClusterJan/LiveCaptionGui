#!/usr/bin/env bash

git pull
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/keys.json

./runApplication.sh
