"""Comprueba que ningún jugador se robe las teclas de otro.

    python pruebas/prueba_controles.py

El bug que motivó esta prueba: mientras el jugador 1 tenía un panel abierto
—una tarea o el árbol de habilidades— el jugador 2 no podía abrir nada. El
reparto de teclas recorría a los jugadores en orden y la rama del que estaba
ocupado terminaba en un `return` que se ejecutaba siempre, incluso cuando la
tecla no era suya, así que nunca se llegaba a mirar al siguiente. Al revés no
pasaba, porque el jugador 1 se revisa primero.

La prueba cruza todos los estados con todos los jugadores: para cada jugador
que tiene algo abierto, comprueba que los demás sigan pudiendo interactuar,
abrir su árbol y mover su cursor.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

pygame.init()

import App
from jugador import TECLAS_POR_PUESTO

CONFIRMAR = [pygame.K_e, pygame.K_RETURN, pygame.K_o, pygame.K_y]

fallos = []


def avanzar(juego):
    for _ in range(90):
        if juego.transitions.is_idle():
            break
        juego.transitions.update(juego, 33)


def partida(cantidad):
    """Arranca una partida con `cantidad` jugadores, ya en el mapa."""
    juego = App.Game()
    juego._activar_opcion_menu("jugar")
    avanzar(juego)
    juego.current_screen = "cantidad"
    while juego.cantidad_seleccionada != cantidad - 2:
        juego._manejar_tecla(pygame.K_DOWN)
    juego._manejar_tecla(pygame.K_RETURN)
    avanzar(juego)
    juego.current_screen = "roles"
    for puesto in range(cantidad):
        juego.seleccion_roles[puesto]["cursor"] = puesto
        juego._manejar_tecla(CONFIRMAR[puesto])
    avanzar(juego)
    juego.current_screen = "partida"
    return juego


def poner_en_zona(juego, jugador):
    """Lleva al jugador a una zona que pueda usar. Devuelve si encontró alguna."""
    for zona in juego.zonas:
        if zona["roles"] and jugador.rol not in zona["roles"]:
            continue
        jugador.personaje.hitbox.center = zona["rect"].center
        jugador.personaje.sync_sprite_from_hitbox()
        return True
    return False


def revisar(condicion, mensaje):
    print(f"    {'ok  ' if condicion else 'FALLA'} {mensaje}")
    if not condicion:
        fallos.append(mensaje)


for cantidad in (2, 3, 4):
    print(f"\n=== {cantidad} jugadores ===")
    for ocupado in range(cantidad):
        juego = partida(cantidad)
        bloqueador = juego.jugadores[ocupado]

        # El jugador `ocupado` abre su árbol de habilidades.
        juego._tecla_en_partida(TECLAS_POR_PUESTO[ocupado]["habilidades"][0])
        if not bloqueador.ocupado:
            continue

        print(f"  con el jugador {ocupado + 1} teniendo su árbol abierto:")
        for otro in range(cantidad):
            if otro == ocupado:
                continue
            jugador = juego.jugadores[otro]

            # ...el otro puede abrir SU árbol
            juego._tecla_en_partida(TECLAS_POR_PUESTO[otro]["habilidades"][0])
            revisar(jugador.ocupado, f"el jugador {otro + 1} abre su árbol")
            juego._tecla_en_partida(TECLAS_POR_PUESTO[otro]["habilidades"][0])

            # ...y puede interactuar con una zona suya
            if poner_en_zona(juego, jugador):
                juego._tecla_en_partida(TECLAS_POR_PUESTO[otro]["interactuar"][0])
                revisar(jugador.ocupado, f"el jugador {otro + 1} interactúa con una zona")
                for _ in range(8):
                    if not jugador.ocupado:
                        break
                    juego._tecla_en_partida(TECLAS_POR_PUESTO[otro]["interactuar"][0])

        # El que estaba ocupado sigue respondiendo a lo suyo.
        antes = bloqueador.cursor
        juego._tecla_en_partida(TECLAS_POR_PUESTO[ocupado]["abajo"][0])
        revisar(bloqueador.cursor != antes or juego._total_opciones(bloqueador) <= 1,
                f"el jugador {ocupado + 1} sigue moviendo su propio cursor")

print()
if fallos:
    print(f"{len(fallos)} FALLOS")
    sys.exit(1)
print("TODO OK: nadie se roba las teclas de nadie")
