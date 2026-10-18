#!/bin/sh
set -eu

if [ ! -f /data/run.sh ]; then
    cp -a /opt/open-toontown/. /data/
fi

exec /data/run.sh
