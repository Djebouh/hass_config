#!/bin/bash

outdir=~/tmp/webcam_images

if [[ ! -d "$outdir" ]]; then
  mkdir -p "$outdir"
fi

ffmpeg -t 20 -rtsp_transport tcp -i rtsp://xiaofang/unicast -frames:v 5 -vf fps=1/5 -c:v mjpeg -an -f image2 -strftime 1 "$outdir"/%Y-%m-%d_%H-%M-%S.jpg

