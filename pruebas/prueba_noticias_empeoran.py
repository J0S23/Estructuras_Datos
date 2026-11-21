"""Las noticias verdaderas que nadie arregla empeoran (redes/nexus._empeorar).

    python pruebas/prueba_noticias_empeoran.py

Cuando una noticia verdadera se vuelve viral sin que nadie la haya
arreglado: los breakers terminan en un apagón, el panel en corto baja una
compuerta, la terminal se desconecta, la cerradura de las celdas hace la
fuga el doble de lenta y la puerta para dos se queda sin corriente; y cada
prisionero en verde deja de confiar con PROB_DESCONFIAR ("nadie hace nada").
Arreglarla después deshace lo que dura (terminal, puerta). Si ya la habían
arreglado, volverse viral no hace nada. Sale en los resultados.
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
from juego.dificultad import Dificultad
from misiones import puertas
from redes.nexus import Publicacion, VERDE, GRIS
from data.nexus import NOTICIAS, PROB_DESCONFIAR
from screens.resultados import render_resultados

OUT = os.environ.get("NEXUS_CAPTURAS") or os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)


def partida(semilla=3):
    random.seed(semilla)
    g = App.Game()
    g.cantidad_jugadores = 2
    g.abrir_seleccion_roles(ir=False)
    for estado, rol in zip(g.seleccion_roles, ("Tecnomante", "Forjador")):
        estado["rol"], estado["listo"] = rol, True
    g.dificultad = Dificultad("normal")
    g._preparar_partida()
    g.current_screen = "partida"
    g.saltar_tutorial()
    g.presentacion = None
    g.nexus.rng = random.Random(semilla)
    g.nexus.reloj_rumor_ms = g.nexus.reloj_normal_ms = 10 ** 9
    g.eventos.proximo_ms = 10 ** 9
    avisos = []
    for j in g.jugadores:
        original = j.avisar
        j.avisar = (lambda o: lambda texto, *a, **k: (avisos.append(texto), o(texto, *a, **k)))(original)
    return g, avisos


def noticia(g, lugar):
    """Una noticia verdadera de ese lugar (si el reloj no la puede poner por
    cómo están las puertas, se arma a mano en uno de sus lugares)."""
    red = g.nexus
    datos = next(n for n in NOTICIAS if n["lugar"] == lugar)
    pub = red.lanzar_noticia(datos)
    if pub is None:
        lugares = red._todos_los_lugares(lugar)
        assert lugares, f"el mapa no tiene lugares de {lugar}"
        pub = Publicacion(red._presos()[0], "noticia", datos["texto"], falsa=False, rumor=datos)
        pub.lugar = lugares[0]
        red.publicaciones.append(pub)
    return pub


def poner_verdes(red, n):
    presos = red._presos()
    for nodo in presos:
        red.grafo.datos[nodo]["color"] = GRIS
    for nodo in presos[:n]:
        red.grafo.datos[nodo]["color"] = VERDE


# -- Cada lugar ----------------------------------------------------------------------------------
resultados = {}

# Breakers -> apagón.
g, avisos = partida()
red = g.nexus
poner_verdes(red, 10)
assert not g.eventos.apagon
pub = noticia(g, "fusibles")
red._volverse_viral(pub)
assert g.eventos.apagon, "los breakers sin arreglar no terminaron en un apagón"
verdes = sum(red.color(n) == VERDE for n in red._presos())
assert verdes < 10, "nadie dejó de confiar"
assert any("era verdad y nadie lo arregló" in a and "luz" in a for a in avisos), avisos[-3:]
assert any("dejaron de confiar" in a or "dejó de confiar" in a for a in avisos)
resultados["fusibles"] = f"apagón, verdes 10 -> {verdes}"
r = red.resumen()
assert r["empeoradas"] == 1

# Panel en corto -> compuerta.
g, avisos = partida(4)
red = g.nexus
assert g.eventos.activo is None
pub = noticia(g, "panel")
red._volverse_viral(pub)
assert g.eventos.activo == "compuerta" and g.eventos.compuerta["cerrada"], "el panel no bajó una compuerta"
resultados["panel"] = "compuerta"

# Terminal -> desconectada, y al arreglarla se reconecta.
g, avisos = partida(5)
red = g.nexus
pub = noticia(g, "terminal")
red._volverse_viral(pub)
zona = pub.efecto.get("zona")
assert zona is not None and zona["desconectada"], "la terminal no se desconectó"
red.arreglar(g.jugadores[0], pub)
assert not zona["desconectada"], "arreglarla no reconectó la terminal"
resultados["terminal"] = "desconectada y reconectada al arreglar"

# Celda -> la fuga va más lenta.
g, avisos = partida(6)
red = g.nexus
pub = noticia(g, "celda")
assert not red.efecto_activo("celda")
red._volverse_viral(pub)
assert red.efecto_activo("celda"), "la cerradura trabada no hace más lenta la fuga"
red.arreglar(g.jugadores[0], pub)
assert not red.efecto_activo("celda")
resultados["celda"] = "fuga lenta hasta arreglarla"

# Puerta para dos -> sin corriente: con dos en los paneles no abre.
g, avisos = partida(7)
red = g.nexus
if g.puertas_dobles:
    puerta = g.puertas_dobles[0]
    puerta["abierta"] = False
    pub = noticia(g, "puerta_doble")
    red._volverse_viral(pub)
    assert any(p.get("sin_corriente") for p in g.puertas_dobles), "la puerta para dos sigue con corriente"
    p_sin = next(p for p in g.puertas_dobles if p.get("sin_corriente"))
    j1, j2 = g.jugadores
    for j, panel in zip((j1, j2), p_sin["paneles"]):
        j.personaje.hitbox.center = panel.center
        j.personaje.sync_sprite_from_hitbox()
    for _ in range(200):
        puertas.actualizar(g.puertas_dobles, [j1, j2], 16)
    assert not p_sin["abierta"], "la puerta sin corriente se abrió"
    g._actualizar_partida(16)
    assert j1.pista_mision == "Puerta sin energía", j1.pista_mision
    red.arreglar(j1, pub)
    assert not p_sin.get("sin_corriente")
    for _ in range(200):
        puertas.actualizar(g.puertas_dobles, [j1, j2], 16)
    assert p_sin["abierta"], "arreglada, la puerta para dos no abrió"
    resultados["puerta_doble"] = "sin corriente hasta arreglarla"
else:
    resultados["puerta_doble"] = "(el mapa no tiene puertas para dos)"

# Ya arreglada: volverse viral no empeora nada.
g, avisos = partida(8)
red = g.nexus
poner_verdes(red, 10)
pub = noticia(g, "fusibles")
red.arreglar(g.jugadores[0], pub)
red._volverse_viral(pub)
assert not g.eventos.apagon and red.empeoradas == 0
assert sum(red.color(n) == VERDE for n in red._presos()) == 10
resultados["arreglada antes"] = "nada"

# La desconfianza, en promedio PROB_DESCONFIAR de los verdes.
perdidos = []
for semilla in range(10, 16):
    g, _ = partida(semilla)
    poner_verdes(g.nexus, 12)
    g.nexus._volverse_viral(noticia(g, "escondite" if semilla % 2 else "celda"))
    perdidos.append(12 - sum(g.nexus.color(n) == VERDE for n in g.nexus._presos()))
media = sum(perdidos) / len(perdidos)
assert 0.5 * PROB_DESCONFIAR * 12 <= media <= 1.6 * PROB_DESCONFIAR * 12, (perdidos, media)

# En los resultados.
g, _ = partida(20)
g.nexus._volverse_viral(noticia(g, "celda"))
g.mision.resultado = "derrota"
pantalla = pygame.Surface((1280, 720))
from screens import resultados as pantalla_resultados
for k in range(45):          # (la escena del final se salta; las cifras cuentan hacia arriba)
    render_resultados(pantalla, g.jugadores, g.font, g.small_font, g.mision, g.equipo, g.infiltrado,
                      g.logros, 0, g.nexus, g.cambiaformas, g.npcs, g.dificultad, g.tiempo_jugado_ms)
    if k == 0:
        pantalla_resultados.saltar_intro()
    pygame.time.wait(60)
pygame.image.save(pantalla, os.path.join(OUT, "noticias_empeoran_resultados.png"))
assert g.nexus.resumen()["empeoradas"] == 1

for lugar, que in resultados.items():
    print(f"   {lugar}: {que}")
print(f"desconfianza: {perdidos} de 12 verdes (media {media:.1f})")
print("OK prueba_noticias_empeoran")
