#!/usr/bin/env bash
source "$(dirname "$0")/env.sh"
ping -c 1 -W 1 "$PI_IP" >/dev/null && echo "Pi: OK" || echo "Pi: SEM RESPOSTA"
ping -c 1 -W 1 192.168.186.3 >/dev/null && echo "Create3: OK" || echo "Create3: SEM RESPOSTA"
echo "bateria: $(cat /sys/class/power_supply/BAT0/status) $(cat /sys/class/power_supply/BAT0/capacity)%"
echo "perfil: $(powerprofilesctl get)"
docker image inspect "$IMG" >/dev/null 2>&1 && echo "imagem $IMG: OK" || echo "imagem $IMG: FALTA"
curl -s -m 2 http://127.0.0.1:8080/v1/models >/dev/null && echo "llama-server: no ar" || echo "llama-server: desligado"
