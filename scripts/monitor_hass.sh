#!/bin/bash

log_file=~homeassistant/.homeassistant/home-assistant.log

current=`date +%s`
last_activity=`stat -c "%Y" $log_file`

if [ $(($current-$last_activity)) -gt 600 ]; then 
     echo "home assistant is not active";
     sudo systemctl restart home-assistant@homeassistant.service
else 
     echo "home assistant is active"; 
fi

exit 0
