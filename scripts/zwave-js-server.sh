#!/bin/bash

cd /home/homeassistant/zwave-js-server/
ts-node "src/bin/server.ts" --config "/home/homeassistant/zwave-js-server/key.json" /dev/zwaveusbstick
# ts-node "src/bin/server.ts" /dev/zwaveusbstick