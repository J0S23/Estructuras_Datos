"""Escondites: tamaño de la entrada.

Dónde está cada escondite lo dice el mapa (Hitboxes/<mapa>_objetos.json, con
el editor de mapa). El punto es el centro del pie del escondite, donde el
jugador se para para entrar.

Escondido, ningún alien te ve. Pero tu latido se sigue oyendo (más bajito, ver
FACTOR_RUIDO_ESCONDIDO en jugador.py): si un alien lo oye viene a revisar el
escondite y empieza el minijuego de calmar los latidos (minijuego_latidos.py).
"""

# Tamaño del área de entrada (en píxeles del mundo ya escalado).
ANCHO_ENTRADA, ALTO_ENTRADA = 70, 40
