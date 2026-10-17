#!/bin/sh
set -eu

cd /app/RunDocker/Districts

./0-thya.sh &
./1-lillica.sh &
./2-krey.sh &
./3-dottie.sh &
./4-gwen.sh &
./5-loopy.sh &
./6-alex.sh &
./7-cinnamon.sh &
./8-aurora.sh &

wait