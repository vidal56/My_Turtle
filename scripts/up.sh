#!/usr/bin/env bash
# Sobe localization + pose + nav2. Robo NA DOCK, notebook NA TOMADA.
source "$(dirname "$0")/env.sh"
powerprofilesctl set performance 2>/dev/null
if [ "$(cat /sys/class/power_supply/BAT0/status)" = "Discharging" ]; then
  echo "ERRO: notebook na bateria. Ligue o carregador (CPU cai e o Nav2 falha)."; exit 1
fi
"$REPO/scripts/down.sh" >/dev/null
echo "[1/3] localization..."
for t in 1 2; do
  docker rm -f tb_loc >/dev/null 2>&1
  docker run -d --name tb_loc --network host -v "$REPO":/work ${DS:+-e ROS_DISCOVERY_SERVER=$DS} "$IMG" bash -c "ros2 launch turtlebot4_navigation localization.launch.py map:=$MAP namespace:=$NS" >/dev/null
  wait_log tb_loc createLaserObject 40 && break
  [ "$t" = 2 ] && { echo "FALHA: localization nao subiu"; exit 1; }
  echo "  repetindo localization..."
done
echo "[2/3] pose inicial (dock):"
"$REPO/scripts/pose.sh" $DOCK_POSE
echo "[3/3] nav2..."
for t in 1 2 3; do
  docker rm -f tb_nav2 >/dev/null 2>&1
  docker run -d --name tb_nav2 --network host -v "$REPO":/work ${DS:+-e ROS_DISCOVERY_SERVER=$DS} "$IMG" bash -c "ros2 launch turtlebot4_navigation nav2.launch.py namespace:=$NS params_file:=$PARAMS" >/dev/null
  wait_log tb_nav2 "Managed nodes are active" 90 && { echo "PRONTO. Logs: docker logs -f tb_nav2"; exit 0; }
  echo "  nav2 nao ativou (tentativa $t), repetindo..."
done
echo "FALHA: nav2"; exit 1
