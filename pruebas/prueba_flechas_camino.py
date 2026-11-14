"""Las flechas guía (amarilla, azul y roja) siguen el camino, no la línea
recta (screens/flechas.py).

    python pruebas/prueba_flechas_camino.py

1. `flechas.ruta` va del jugador al objetivo sin cruzar paredes, y la flecha
   apunta al primer tramo de ese camino (no derecho a través de la pared).
2. Mientras camina se recorta lo que ya pasó, y se vuelve a buscar si cambia
   el objetivo.
3. Sin mundo (o sin camino) vuelve la flecha en línea recta.
4. Se ve: capturas pruebas/capturas/flechas_camino_*.png con la amarilla, la
   azul de un rumor y la roja de un apagón.
5. La amarilla no manda a donde no se llega: si lo que toca hacer queda
   detrás de una puerta para dos cerrada, lleva a sus paneles; si no hay
   forma de llegar, no sale.
6. De varias cosas iguales (consolas, terminales...) escoge la más cercana
   CAMINANDO, no en línea recta.
"""

import math
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
OUT = os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)

from juego import app as App
from juego import objetos_mapa, navegacion, dificultad
from screens import flechas
objetos_mapa.mapa_activo = lambda: "Nave"


class Teclas(dict):
    def __getitem__(self, k):
        return self.get(k, False)


pygame.key.get_pressed = lambda: Teclas()


def nueva_partida():
    juego = App.Game()

    def avanzar():
        for _ in range(80):
            if juego.transitions.is_idle():
                break
            juego.transitions.update(juego, 33)
    juego._activar_opcion_menu("jugar"); avanzar(); juego.current_screen = "cantidad"
    juego._manejar_tecla(pygame.K_RETURN); avanzar(); juego.current_screen = "roles"
    juego._manejar_tecla(pygame.K_e); juego._manejar_tecla(pygame.K_RETURN)
    avanzar(); juego.current_screen = "partida"
    juego.saltar_tutorial()
    juego.presentacion = None
    juego.quitar_cambiaformas()
    for a in juego.aliens:
        a.hitbox.topleft = (5, 5)
        a.descanso_ms = 10 ** 9
    if juego.nexus is not None:
        juego.nexus.reloj_rumor_ms = juego.nexus.reloj_normal_ms = 10 ** 9
    return juego


def completa(dueño, destino, color, t):
    """Pide la ruta hasta que el A* por partes termine."""
    for i in range(200):
        navegacion.siguiente_cuadro()
        r = flechas.ruta(dueño, destino, color, t + i)
        if r is not None:
            return r
    return None


juego = nueva_partida()
mundo = juego.mundo
nav = navegacion.de_mundo(mundo, flechas.ANCHO_GUIA, flechas.ALTO_GUIA)
j1 = juego.jugadores[0]

# -- 1. Un objetivo detrás de una pared ---------------------------------------------------------
# Busca un par (jugador, objetivo) con pared en medio y camino de rodeo.
libres = sorted(nav.libre)
par = None
for i in range(0, len(libres), 37):
    a = (libres[i][0] + 17, libres[i][1] + 10)
    for j in range(i + 11, len(libres), 53):
        b = (libres[j][0] + 17, libres[j][1] + 10)
        if 250 < math.dist(a, b) < 600 and not nav.libre_entre(a, b):
            camino = nav.camino(a, b, sellos=False)
            if camino and len(camino) >= 2:
                par = (a, b)
                break
    if par:
        break
assert par, "no encontré una pared en medio"
a, b = par
j1.hitbox.center = a
flechas.empezar(mundo)
r = completa(j1, b, (255, 214, 64), 0)
assert r is not None and len(r) >= 3, r
assert r[0] == j1.hitbox.center


def cruza(p, q):
    """¿El tramo pasa por una pared? (un punto del tamaño de la guía cada 8 px)"""
    pasos = max(1, int(math.dist(p, q) // 8))
    caja = pygame.Rect(0, 0, flechas.ANCHO_GUIA - 2, flechas.ALTO_GUIA - 2)
    for k in range(pasos + 1):
        caja.center = (p[0] + (q[0] - p[0]) * k / pasos, p[1] + (q[1] - p[1]) * k / pasos)
        if caja.collidelist(mundo.paredes) != -1:
            return True
    return False


assert cruza(a, b), "la línea recta sí cruza la pared"
for p, q in zip(r[1:], r[2:]):
    assert not cruza(p, q), f"un tramo cruza una pared: {p} -> {q}"
assert math.dist(r[-1], b) < 30, (r[-1], b)
recta = math.atan2(b[1] - a[1], b[0] - a[0])
guia = math.atan2(r[1][1] - a[1], r[1][0] - a[0])
dif = abs((guia - recta + math.pi) % (2 * math.pi) - math.pi)
print(f"1. camino de {len(r) - 1} tramos sin cruzar paredes; la flecha gira "
      f"{math.degrees(dif):.0f}° respecto de la línea recta: OK")

# -- 2. Camina: recorta y busca de nuevo si cambia el objetivo ----------------------------------
antes = len(r)
j1.hitbox.center = (int(r[1][0]), int(r[1][1]))
r2 = flechas.ruta(j1, b, (255, 214, 64), 10)
assert r2 is not None and len(r2) <= antes, (len(r2), antes)
r3 = completa(j1, (a[0], a[1]), (255, 214, 64), 20)
assert r3 is not None and math.dist(r3[-1], a) < 30
print("2. recorta lo caminado y busca de nuevo con otro objetivo: OK")

# -- 3. Sin mundo: línea recta ------------------------------------------------------------------
flechas.empezar(None)
assert flechas.ruta(j1, b, (1, 2, 3), 0) is None
lienzo = pygame.Surface((800, 600))
vista = pygame.Rect(0, 0, 800, 600)
camara = pygame.Rect(j1.hitbox.centerx - 400, j1.hitbox.centery - 300, 800, 600)
flechas.flecha_alrededor(lienzo, vista, camara, j1, b, (1, 2, 3))
assert flechas.dibujar_camino(lienzo, vista, camara, j1, b, (1, 2, 3), 0) is None
print("3. sin mundo: la flecha de antes, sin camino: OK")

# -- 4. Capturas en el juego -------------------------------------------------------------------
juego.dificultad = dificultad.Dificultad("normal")
j1.hitbox.center = a
j1.personaje.sync_sprite_from_hitbox()


def foto(nombre, cuadros=40):
    for _ in range(cuadros):
        navegacion.siguiente_cuadro()
        juego._dibujar()
    pygame.image.save(juego.screen, os.path.join(OUT, f"flechas_camino_{nombre}.png"))


foto("amarilla")
red = juego.nexus
if red is not None:
    pub = red.lanzar_rumor()
    if pub is not None and pub.lugar is not None:
        red.investigando[j1] = pub
        foto("azul")
        red.investigando.pop(j1, None)
juego.eventos.lanzar("apagon")
foto("roja")
print("4. capturas flechas_camino_*.png: OK")

# -- 5. Lo que no se alcanza: a la puerta que lo tapa ---------------------------------------------
juego = nueva_partida()
mundo = juego.mundo
m = juego.mision
nav = navegacion.de_mundo(mundo, flechas.ANCHO_GUIA, flechas.ALTO_GUIA)
j1 = juego.jugadores[0]
m.abrir_puerta(j1)
for i, p in enumerate(m.puertas):
    if not p["abierta"]:
        m.abrir_puerta(j1, i)
doble = next(p for p in juego.puertas_dobles if not p["abierta"])
pie = j1.hitbox.center
todo = nav._bloqueos_extra(False)
sin_doble = [r for r in todo if r != doble["rect"]]
detras = next((c[0] + 17, c[1] + 10) for c in sorted(nav.libre)
              if not nav.conectados(pie, (c[0] + 17, c[1] + 10), sellos=False)
              and nav.conectados(pie, (c[0] + 17, c[1] + 10), sellos=False, extra=sin_doble))
original = m._objetivo
m._objetivo = lambda j: (detras, "Algo detrás de la puerta")
punto, texto = m.punto_objetivo(j1)
assert "puerta para dos" in texto and any(r.center == punto for r in doble["paneles"]), (punto, texto)
assert nav.conectados(pie, punto, sellos=False), "el panel al que manda sí se alcanza"
# Sin forma de llegar (afuera del mapa caminable): no sale.
m._desvios.clear()
m._objetivo = lambda j: ((-500, -500), "Nada")
assert m.punto_objetivo(j1) is None
m._objetivo = original
print(f"5. detrás de la puerta para dos: '{texto}'; sin camino, sin flecha: OK")

# -- 6. La más cercana caminando ----------------------------------------------------------------
libres = sorted(nav.libre)
rng = random.Random(4)
caso = None
for _ in range(20000):
    a, b, c = (rng.choice(libres) for _ in range(3))
    a, b, c = (a[0] + 17, a[1] + 10), (b[0] + 17, b[1] + 10), (c[0] + 17, c[1] + 10)
    if not (math.dist(a, b) < math.dist(a, c) < 1600):
        continue
    cb, cc = nav.camino(a, b, sellos=False), nav.camino(a, c, sellos=False)
    if not cb or not cc:
        continue
    lb = sum(math.dist(p, q) for p, q in zip([a] + cb, cb))
    lc = sum(math.dist(p, q) for p, q in zip([a] + cc, cc))
    if lb > lc + 250:
        caso = (a, b, c)
        break
assert caso, "no encontré un caso en el mapa"
a, b, c = caso
j1.hitbox.center = a
cosas = [{"p": b}, {"p": c}]
elegida = None
for _ in range(120):
    navegacion.siguiente_cuadro()
    elegida = m._elegir(j1, cosas, lambda x: x["p"])
assert elegida["p"] == c, "escoge la que queda más cerca caminando"
print(f"6. en línea recta ganaba {b}, caminando gana {c}: OK")
print("\nTODO OK")
