#!/bin/sh
set -eu

cd /app/rundocker

./start-astron-server.sh &
ASTRON_PID=$!

sleep 2

./start-uberdog-server.sh &
UBERDOG_PID=$!

sleep 2

cd /app/RunDocker/Districts
./districts.sh &
DISTRICTS_PID=$!

trap 'kill "$ASTRON_PID" "$UBERDOG_PID" "$DISTRICTS_PID" 2>/dev/null || true' INT TERM

wait -n "$ASTRON_PID" "$UBERDOG_PID" "$DISTRICTS_PID"
