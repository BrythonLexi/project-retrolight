#!/bin/sh
set -eu

if [ ! -f /data/run.sh ]; then
    cp -a /opt/project-retrolight/. /data/
fi

exec /data/run.sh
