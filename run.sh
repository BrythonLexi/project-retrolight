#!/bin/sh
set -eu

cd /data/rundocker

./start-astron-server.sh &
ASTRON_PID=$!

sleep 2

./start-uberdog-server.sh &
UBERDOG_PID=$!

sleep 2

cd /data/rundocker/Districts
./districts.sh &
DISTRICTS_PID=$!

cleanup() {
    kill "$ASTRON_PID" "$UBERDOG_PID" "$DISTRICTS_PID" 2>/dev/null || true
}

check_processes() {
    kill -0 "$ASTRON_PID" 2>/dev/null || return 1
    kill -0 "$UBERDOG_PID" 2>/dev/null || return 2
    kill -0 "$DISTRICTS_PID" 2>/dev/null || return 3
    return 0
}

trap cleanup INT TERM EXIT

while check_processes; do
    sleep 1
done

status=$?
cleanup

case "$status" in
    1)
        echo "Astron exited unexpectedly"
        wait "$ASTRON_PID" 2>/dev/null || true
        ;;
    2)
        echo "UberDog exited unexpectedly"
        wait "$UBERDOG_PID" 2>/dev/null || true
        ;;
    3)
        echo "Districts exited unexpectedly"
        wait "$DISTRICTS_PID" 2>/dev/null || true
        ;;
esac

exit 2
