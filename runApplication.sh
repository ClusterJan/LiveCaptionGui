#!/usr/bin/env bash


tmux new -d -s my-session-name \; split-window -v ;\
tmux send-keys -t my-session-name.1 "tail -f live-translation/captions.txt" ENTER
tmux send-keys -t my-session-name.2 "cd live-translation && poetry shell " ENTER
tmux send-keys -t my-session-name.2 "translate -f it-IT -t en-US" ENTER

# Use this to connect whenever you want
tmux a -t my-session-name