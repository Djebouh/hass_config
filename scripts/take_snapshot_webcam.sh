#!/bin/bash

outdir=~/tmp/webcam_images

if [[ ! -d "$outdir" ]]; then
  mkdir -p "$outdir"
fi

ffmpeg -t 10 -rtsp_transport tcp -i rtsp://xiaofang/unicast -frames:v 3 -r 0.2 -f image2 -strftime 1 "$outdir"/%Y-%m-%d_%H-%M-%S.jpg

