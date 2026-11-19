#!/usr/bin/env bash
# Configuracao comum do My_Turtle (use: source scripts/env.sh)
export REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PI_IP="192.168.185.3"
export DS=";${PI_IP}:11811"
export NS="/robot1"
export IMG="tb4-humble-slam"
export LLM_IMG="tb4-humble-llm"
export MAP="/work/maps/mapa_sala_teste.yaml"
export PARAMS="/work/config/nav2_sala.yaml"
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
