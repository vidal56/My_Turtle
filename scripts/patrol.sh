#!/usr/bin/env bash
# uso: patrol.sh [voltas]   (termina docando)
source "$(dirname "$0")/env.sh"
docker run --rm -it --network host -v "$REPO":/work ${DS:+-e ROS_DISCOVERY_SERVER=$DS} "$IMG" bash -c "python3 /work/patrol/${PATROL:-patrol_robo.py} --loops ${1:-1} ${EXTRA} --ros-args -r __ns:=$NS"
