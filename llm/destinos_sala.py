# Pontos da sala (mapa_sala_teste), os mesmos do patrol_robo.py.
# Formato: [x, y, angulo]. Angulo em graus: 0=NORTH, 90=WEST, 180=SOUTH, 270=EAST.
DESTINATIONS = {
    'frente': [0.37, 1.52, 90],
    'fundo': [-0.14, 4.76, 180],
    'meio': [-2.24, 4.32, 270],
    'porta': [-2.52, 0.23, 0],
    'doca': [0.0, 0.6, 270],  # ponto de aproximacao da dock
}


def contexto_str():
    itens = ', '.join(f"'{k}': {v}" for k, v in DESTINATIONS.items())
    return 'destinations = {' + itens + ' }'
