"""Punto de entrada de NEXUS.

    python main.py

Un solo juego: el mapa con los personajes y las estructuras de datos corriendo
juntos. Todo el loop vive en `juego/app.py`; esto solo lo arranca.

Para probar sin abrir ventana:

    python pruebas/prueba_partida.py     una ronda completa, con capturas
    python pruebas/prueba_estructuras.py los árboles por consola
"""

import os
import sys

# Las imágenes, sonidos y mapas se buscan desde la carpeta del proyecto: así
# el juego arranca bien aunque se corra desde otra carpeta.
RAIZ = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)

from juego.app import Game


if __name__ == "__main__":
    Game().run()
