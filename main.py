"""Punto de entrada del proyecto: lanza la ventana del juego (App.py).

La prueba de lógica de las estructuras en consola se movió a
test_estructuras.py para no perderla, pero el lab exige que el juego
se pueda ver y jugar gráficamente, no solo por consola.
"""

from App import Game


if __name__ == "__main__":
    Game().run()
