#!/usr/bin/env bash

git pull
# source venv/bin/activate

cd live-translation
poetry shell
translation -f it-IT -t en-US
