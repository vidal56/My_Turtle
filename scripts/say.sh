#!/usr/bin/env bash
# uso: say.sh "vá para o fundo da sala"
source "$(dirname "$0")/env.sh"
TEXT="${*:?uso: say.sh \"frase\"}"
docker run --rm --network host ${DS:+-e ROS_DISCOVERY_SERVER=$DS} -e ROS_SUPER_CLIENT=True -e TEXT="$TEXT" -e NS="$NS" "$IMG" bash -c 'ros2 topic pub -t 3 -r 2 $NS/user_input std_msgs/msg/String "{data: \"$TEXT\"}"' | grep -E "publishing #1"
