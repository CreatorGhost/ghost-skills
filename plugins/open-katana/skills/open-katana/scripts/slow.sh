#!/bin/bash
# Slow-motion frame grid of one stretch of any video: how you SEE motion (the reference's, then your own render's).
# usage: slow.sh VIDEO START_SECONDS OUT.jpg [FPS=30] [GRID=4x6] [CROP=w:h:x:y]   (frames = cols*rows, read left to right)
V="$1"; S="$2"; O="$3"; FPS="${4:-30}"; GRID="${5:-4x6}"; CROP="${6:-}"
vf="fps=$FPS"; [ -n "$CROP" ] && vf="$vf,crop=$CROP"
ffmpeg -v error -y -ss "$S" -i "$V" -frames:v 1 -vf "$vf,scale=600:-2:flags=lanczos,tile=$GRID" "$O" && echo "$O"
