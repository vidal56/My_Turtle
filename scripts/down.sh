#!/usr/bin/env bash
docker rm -f tb_loc tb_nav2 >/dev/null 2>&1
echo "localization e nav2 parados (llama-server: pkill -f llama-server)"
