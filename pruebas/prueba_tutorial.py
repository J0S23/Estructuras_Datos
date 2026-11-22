"""El tutorial del principio, que se aprende haciendo (juego/tutorial.py,
screens/tutorial.py).

    python pruebas/prueba_tutorial.py

1. J1 hace cada paso de verdad: caminar, sigilo, meterse al casillero marcado,
   salir y leer la nota marcada, sacar el celular, abrir el árbol; cada uno se
   completa solo (con "¡Bien!": `hechos` sube) y las dos tarjetas de leer se
   pasan con la tecla de habilidad. El casillero y la nota se marcan en el
   mapa (y la flecha amarilla no sale mientras).
2. J2 salta todo con la tecla de habilidad (por si alguien se traba): no
   cuenta como hecho. Cuando los dos terminan, despiertan los aliens.
3. Las tarjetas caben con 2, 3 y 4 jugadores (1920x1080, 1366x768 y
   1280x720). (En inglés: prueba_idioma recorre todos los pasos.)

Capturas en pruebas/capturas/tutorial_*.png.
"""

import os
import random
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

pygame.init()

from juego import app as App
from juego import tutorial as T
from juego.dificultad import Dificultad
from screens import tutorial as dibujo

OUT = os.environ.get("NEXUS_CAPTURAS") or os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)
DT = 1000 // 60


class Teclas(dict):
    def __getitem__(self, k):
        return self.get(k, False)


TECLAS = Teclas()
pygame.key.get_pressed = lambda: TECLAS


def partida(roles=("Tecnomante", "Forjador"), tam=(1280, 720), semilla=3):
    random.seed(semilla)
    g = App.Game()
    g.screen = pygame.Surface(tam)
    g.cantidad_jugadores = len(roles)
    g.abrir_seleccion_roles(ir=False)
    for estado, rol in zip(g.seleccion_roles, roles):
        estado["rol"], estado["listo"] = rol, True
    g.dificultad = Dificultad("facil")
    g._preparar_partida()
    g.current_screen = "partida"
    g.transitions = App.TransitionManager()
    g.presentacion = None
    for j in g.jugadores:
        j.puede_moverse = True
    return g


def frames(g, n):
    for _ in range(n):
        g._actualizar_partida(DT)


def cap(g, nombre):
    g._dibujar()
    pygame.image.save(g.screen, os.path.join(OUT, nombre))


def poner(j, punto, abajo=False):
    if abajo:
        j.personaje.hitbox.midbottom = punto
    else:
        j.personaje.hitbox.center = punto
    j.personaje.sync_sprite_from_hitbox()


def tecla(g, j, accion):
    g._tecla_en_partida(j.teclas[accion][0])
    frames(g, 2)


def paso(g, j):
    return g.tutorial._de(j)["paso"]


# -- 1. J1 lo hace todo -----------------------------------------------------------------------
g = partida()
j1, j2 = g.jugadores
assert g.en_tutorial and all(a.aturdido for a in g.aliens)
tut = g.tutorial
cap(g, "tutorial_a_moverse.png")
assert T.PASOS[paso(g, j1)]["accion"] == "mover"

TECLAS[pygame.K_d] = True
frames(g, 6)
TECLAS.clear()
assert T.PASOS[paso(g, j1)]["accion"] == "sigilo" and tut._de(j1)["hechos"] == 1
g._dibujar()                                    # (aquí se ve el "¡Bien!")
pygame.image.save(g.screen, os.path.join(OUT, "tutorial_b_bien.png"))

TECLAS[pygame.K_a] = True
TECLAS[j1.teclas["sigilo"][0]] = True
frames(g, 20)
cap(g, "tutorial_c_sigilo.png")
frames(g, 60)
TECLAS.clear()
assert T.PASOS[paso(g, j1)]["accion"] == "esconderse", paso(g, j1)

# El casillero marcado: está en el mapa, con su camino, y no sale la flecha amarilla.
objetivo = tut.objetivo(j1)
assert objetivo is not None and objetivo[1] == "Escóndete aquí"
punto, _, rect = objetivo
casillero = next(e for e in g.escondites if e["rect"] == rect)
assert not casillero.get("candado") and casillero.get("ocupante") is None
cap(g, "tutorial_d_casillero.png")
poner(j1, rect.midbottom, abajo=True)
tecla(g, j1, "interactuar")
assert j1.escondido, "no se metió al casillero"
frames(g, 2)
assert T.PASOS[paso(g, j1)]["accion"] == "nota" and tut._de(j1)["hechos"] == 3
assert tut.objetivo(j1) is None, "escondido, primero tiene que salir"
cap(g, "tutorial_e_escondido.png")
tecla(g, j1, "interactuar")
assert not j1.escondido
objetivo = tut.objetivo(j1)
assert objetivo is not None and objetivo[1] == "Lee esta nota"
nota = next(n for n in g.mision.notas if n["rect"] == objetivo[2])
poner(j1, nota["rect"].center)
cap(g, "tutorial_f_nota.png")
tecla(g, j1, "interactuar")
assert j1 in nota["leida_por"] and j1.panel is not None
assert T.PASOS[paso(g, j1)]["accion"] == "celular", paso(g, j1)
tecla(g, j1, "interactuar")                     # cierra la nota
assert j1.panel is None

tecla(g, j1, "celular")
assert T.PASOS[paso(g, j1)]["accion"] == "arbol", "abrir el celular no completó el paso"
tecla(g, j1, "celular")
if j1.panel is not None:
    j1.cerrar_panel()
cap(g, "tutorial_g_arbol.png")
tecla(g, j1, "habilidades")
assert T.PASOS[paso(g, j1)]["accion"] == "leer", "abrir el árbol no completó el paso"
tecla(g, j1, "habilidades")
if j1.panel is not None:
    j1.cerrar_panel()
assert tut._de(j1)["hechos"] == 6
frames(g, 30)
cap(g, "tutorial_h_cuidado.png")
tecla(g, j1, "habilidad")
cap(g, "tutorial_i_mision.png")
tecla(g, j1, "habilidad")
assert tut.esta_listo(j1) and g.en_tutorial
cap(g, "tutorial_j_esperando.png")
assert tut.objetivo(j1) is None
print("1. J1 aprende haciendo: caminar, sigilo, casillero, nota, celular, árbol (6 '¡Bien!') y "
      "las dos tarjetas: OK")

# -- 2. J2 salta todo -------------------------------------------------------------------------
for _ in range(len(T.PASOS)):
    tecla(g, j2, "habilidad")
assert tut._de(j2)["hechos"] == 0, "saltar contó como hecho"
assert not g.en_tutorial and all(not a.aturdido for a in g.aliens)
print("2. saltar con la tecla de habilidad no cuenta como hecho; al terminar los dos, despiertan: OK")

# -- 3. Tamaños e idioma ----------------------------------------------------------------------
for roles, tam, nombre in ((("Tecnomante", "Forjador"), (1920, 1080), "2j_1080"),
                           (("Tecnomante", "Forjador", "Biomante", "Resonante"), (1280, 720), "4j_720"),
                           (("Tecnomante", "Forjador", "Biomante"), (1366, 768), "3j_768")):
    g = partida(roles, tam)
    for j in g.jugadores:
        for _ in range(min(j.puesto * 2, len(T.PASOS) - 1)):
            g.tutorial.siguiente(j)
    frames(g, 2)
    cap(g, f"tutorial_k_{nombre}.png")
    for j in g.jugadores:
        anotado = j.hud_tutorial
        assert anotado is not None, (nombre, j.puesto)
        vista = pygame.Rect(anotado[0])
        assert vista.top <= anotado[1] < vista.bottom, (nombre, j.puesto, anotado)

print("3. la tarjeta cabe con 2, 3 y 4 jugadores (1080p, 768 y 720): OK")
print("OK prueba_tutorial")
