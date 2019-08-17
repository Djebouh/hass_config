#!/bin/bash

outdir=~/tmp/webcam_images

lftp $FTP_SERVER -e "mirror -e -R $outdir /Photos/frompi ; quit"

find $outdir -type f -mtime +30 -exec rm -f {} \;
