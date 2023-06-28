#!/usr/bin/env bash

VIRTUAL_ENV_DIR=venv

PORT_FILE=portaudio
if [[ ! -f "$PORT_FILE" ]]; then
  brew remove portaudio
  brew install portaudio
  touch portaudio
fi

if [ -z "${VIRTUAL_ENV}" ]; then
    if [ -d "$VIRTUAL_ENV_DIR" ]; then
        echo "test"
        echo "$VIRTUAL_ENV_DIR/bin/activate"
    else
        python3 -m virtualenv $VIRTUAL_ENV_DIR
        source $VIRTUAL_ENV_DIR/bin/activate
        pip install -r requirements.txt
    fi
fi

KEY_FILE=$(pwd)/key.json
if [[ -f "$KEY_FILE" ]]; then
    GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/key.json
    export GOOGLE_APPLICATION_CREDENTIALS
else
    echo "Key file not found"
    exit 1
fi

python3 main.py
