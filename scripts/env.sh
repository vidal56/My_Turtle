#!/usr/bin/env bash
# Configuracao comum do My_Turtle. Uso: ROBOT=2 ./scripts/up.sh  (padrao: ROBOT=1)
export REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ROBOT="${ROBOT:-1}"
export NS="/robot${ROBOT}"
case "$ROBOT" in
  1) export PI_IP="192.168.185.3"
     export MAP="/work/maps/mapa_sala_teste.yaml"
     export PARAMS="/work/config/nav2_sala.yaml"
     export DOCK_POSE="0 0 -90" ;;
  2) export PI_IP="192.168.68.54"
     export MAP="/work/maps/lab_completo.yaml"
     export PARAMS="/work/config/nav2_lab.yaml"
     export DOCK_POSE="0 0 0" ;;
  *) echo "ROBOT=$ROBOT sem configuracao em scripts/env.sh"; return 1 2>/dev/null || exit 1 ;;
esac
# Discovery Server: N ';' antes do IP, onde N = Server ID (= numero do robo)
SEMI="$(printf ';%.0s' $(seq 1 "$ROBOT"))"
export DS="${SEMI}${PI_IP}:11811"
export IMG="tb4-humble-slam"
export LLM_IMG="tb4-humble-llm"
export LOGDIR="$REPO/logs"
mkdir -p "$LOGDIR"

# wait_log <container> <padrao> <timeout_s>  ->  0 ok, 1 timeout, 2 bringup abortado
wait_log() {
  local c="$1" p="$2" t="$3" i=0 out
  while [ "$i" -lt "$t" ]; do
    out="$(docker logs "$c" 2>&1)"
    echo "$out" | grep -q "$p" && return 0
    echo "$out" | grep -q "Aborting bringup" && return 2
    sleep 1; i=$((i+1))
  done
  return 1
}
[ "${LOCAL:-0}" = 1 ] && export DS=""
