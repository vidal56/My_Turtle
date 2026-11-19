# My_Turtle

Patrulha autonoma e navegacao por linguagem natural em um TurtleBot 4 fisico (ROS 2 Humble, namespace `/robot1`), com Nav2 + AMCL sobre um mapa salvo da sala.

## Estrutura

    docker/    Dockerfiles (slam/nav2/viz) + Dockerfile.llm (openai embutido)
    config/    nav2_sala.yaml (nav2.yaml padrao com transform_tolerance ajustado)
    maps/      mapa_sala_teste.pgm/.yaml
    patrol/    patrol_robo.py (undock -> waypoints -> aproximacao -> dock)
    llm/       no de linguagem natural, destinos, validador e prompt
    scripts/   env.sh, check.sh, up.sh, pose.sh, patrol.sh, llm.sh, say.sh, down.sh

## Pre-requisitos

- Notebook com Docker e a imagem `tb4-humble-slam` (ver `docker/`), **na tomada e em perfil `performance`** (em `power-saver` o Nav2 perde TF e os goals falham).
- TurtleBot 4 com Discovery Server na Pi (`192.168.185.3:11811`); ajuste IP/namespace em `scripts/env.sh`.
- Para o LLM: llama.cpp compilado em `~/llama.cpp` (modelo Qwen2.5-Coder-1.5B-Instruct Q4_K_M, baixado via `-hf` na primeira execucao).

## Uso (robo NA DOCK)

    ./scripts/check.sh        # Pi, Create 3, bateria/perfil, imagem, llama-server
    ./scripts/up.sh           # localization + pose inicial + nav2 (repete se abortar)
    ./scripts/patrol.sh [N]   # N voltas e dock
    ./scripts/llm.sh          # llama-server + no de linguagem natural (use "safe" para so validar)
    ./scripts/say.sh "vá para o fundo da sala"
    ./scripts/down.sh

Sem o robo, o fluxo do LLM pode ser testado so validando:

    LOCAL=1 ./scripts/llm.sh safe
    LOCAL=1 ./scripts/say.sh "volte para a dock"

## Comandos de linguagem natural

Destinos em `llm/destinos_sala.py`: `frente`, `fundo`, `meio`, `porta`, `doca`. O codigo gerado pelo modelo passa por `llm/validador.py` (so aceita chamadas permitidas do `navigator`) antes de ser executado.

## Notas

- As coordenadas e o mapa sao da sala de teste; para outro ambiente, refaca o mapa e os pontos.
- No modo real, envie um comando por vez e espere o `Goal succeeded!`.
