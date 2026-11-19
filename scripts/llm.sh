#!/usr/bin/env bash
# uso: llm.sh [safe]   (safe = so valida, o robo nao anda)
source "$(dirname "$0")/env.sh"
BRAKE=false; [ "${1:-}" = "safe" ] && BRAKE=true
if ! curl -s -m 2 http://127.0.0.1:8080/v1/models >/dev/null; then
  echo "subindo llama-server..."
  nohup "$HOME/llama.cpp/build/bin/llama-server" -hf bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M -c 2048 --host 127.0.0.1 --port 8080 > "$LOGDIR/llama.log" 2>&1 &
  for i in $(seq 1 60); do curl -s -m 2 http://127.0.0.1:8080/v1/models >/dev/null && break; sleep 1; done
fi
docker image inspect "$LLM_IMG" >/dev/null 2>&1 || docker build -f "$REPO/docker/Dockerfile.llm" -t "$LLM_IMG" "$REPO/docker"
docker run --rm -it --network host -v "$REPO":/work ${DS:+-e ROS_DISCOVERY_SERVER=$DS} "$LLM_IMG" bash -c "cd /work/llm && python3 natural_language_nav_sala.py --ros-args -r __ns:=$NS -p base_url:=http://127.0.0.1:8080/v1 -p model_name:=qwen -p parking_brake:=$BRAKE"
