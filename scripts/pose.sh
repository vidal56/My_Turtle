#!/usr/bin/env bash
# uso: pose.sh [x] [y] [yaw_graus]   (padrao: dock = 0 0 -90)
source "$(dirname "$0")/env.sh"
X=${1:-0.0}; Y=${2:-0.0}; YAW=${3:--90}
read QZ QW < <(python3 -c "import math,sys;a=math.radians(float(sys.argv[1]))/2;print(round(math.sin(a),4),round(math.cos(a),4))" "$YAW")
POSE="{header: {frame_id: map}, pose: {pose: {position: {x: $X, y: $Y, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: $QZ, w: $QW}}, covariance: [0.25,0,0,0,0,0, 0,0.25,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0.0685]}}"
docker run --rm --network host ${DS:+-e ROS_DISCOVERY_SERVER=$DS} -e ROS_SUPER_CLIENT=True -e POSE="$POSE" -e NS="$NS" "$IMG" bash -c 'ros2 topic pub -t 10 -r 2 $NS/initialpose geometry_msgs/msg/PoseWithCovarianceStamped "$POSE" >/dev/null; timeout 6 ros2 run tf2_ros tf2_echo map base_link --ros-args -r /tf:=$NS/tf -r /tf_static:=$NS/tf_static 2>&1 | grep -E "Translation|degree" | head -2'
