"""Punto de entrada de Alcalde Digital.

    python main.py

Un solo juego: el mapa con los personajes y las estructuras de datos corriendo
juntos. Todo el loop vive en `App.py`; esto solo lo arranca.

Para probar sin abrir ventana:

    python pruebas/prueba_partida.py     una ronda completa, con capturas
    python pruebas/prueba_estructuras.py los árboles por consola
"""

from App import Game


if __name__ == "__main__":
    Game().run()
