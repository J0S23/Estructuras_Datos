"""Lugares para esconderse.

Coordenadas de 0 a 1 sobre el mapa, como las zonas de data/tareas.py: el punto
es el centro del pie del escondite, donde el jugador se para para entrar.
Salieron del mapa del Colegio comprobando que no chocan con paredes, que se
llega caminando y que no se montan sobre una zona; pruebas/prueba_aliens.py lo
vuelve a revisar.

Escondido, ningún alien te ve. Pero tu latido se sigue oyendo (más bajito, ver
FACTOR_RUIDO_ESCONDIDO en jugador.py): si un alien lo oye viene a revisar el
escondite y empieza el minijuego de calmar los latidos (minijuego_latidos.py).
"""

ESCONDITES = [
    {"clave": "casillero_noroeste", "nombre": "Casillero", "rx": 0.36, "ry": 0.30},
    {"clave": "casillero_noreste", "nombre": "Casillero", "rx": 0.64, "ry": 0.30},
    {"clave": "armario_oeste", "nombre": "Armario", "rx": 0.16, "ry": 0.50},
    {"clave": "armario_este", "nombre": "Armario", "rx": 0.925, "ry": 0.50},
    {"clave": "casillero_sur", "nombre": "Casillero", "rx": 0.50, "ry": 0.69},
]

# Tamaño del área de entrada (en píxeles del mundo ya escalado).
ANCHO_ENTRADA, ALTO_ENTRADA = 70, 40
