"""Las cuentas falsas que nadie reporta crecen (redes/nexus.py).

    python pruebas/prueba_bots_crecen.py

1. Cada bot gana un seguidor cada `cada_cuanto_crece()` (BOT_GANA_SEGUIDOR_S ×
   "bot_crece_cada" de la dificultad), de preferencia un amigo de uno que ya
   lo sigue, hasta BOT_MAX_SEGUIDORES. No crece en el tutorial.
2. Con más seguidores, un rumor suyo le llega de una vez a más prisioneros.
3. A 6 seguidores (AVISOS_SEGUIDORES) les avisa a todos.
4. Reportarlo temprano / tarde: el mensaje dice a cuántos les llegaba y
   cuántos ganó; los resultados cuentan los seguidores ganados y, si nadie
   reportó ningún bot, dan el consejo.
5. Se ve: seguidores en la publicación, en "¿De dónde salió esto?" y el
   bot más grande en la vista del grafo. Capturas en
   pruebas/capturas/bots_crecen_*.png.
"""

import os
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
from juego import objetos_mapa
from redes import celular
from redes.nexus import GRIS, ROJO, Propagacion
from data.nexus import (RUMORES, BOT_GANA_SEGUIDOR_S, BOT_MAX_SEGUIDORES, AVISOS_SEGUIDORES,
                        SEGUIDORES_BOT, SEGUIDORES_PARA_CONSEJO)
objetos_mapa.mapa_activo = lambda: "Nave"
DT = 1000 // 60


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
    juego.mision.abrir_puerta()
    juego.quitar_cambiaformas()
    for a in juego.aliens:
        a.hitbox.topleft = (5, 5)
        a.descanso_ms = 10 ** 9
    red = juego.nexus
    red.reloj_rumor_ms = red.reloj_normal_ms = 10 ** 9
    return juego


def foto(juego, nombre):
    juego._dibujar()
    pygame.image.save(juego.screen, os.path.join(OUT, f"bots_crecen_{nombre}.png"))


# -- 1. Crece, con amigos de sus seguidores, hasta el máximo --------------------------------------
juego = nueva_partida()
red = juego.nexus
g = red.grafo
bot = red.bots()[0]
assert red.seguidores(bot) == SEGUIDORES_BOT and red.ganados(bot) == 0
assert abs(red.cada_cuanto_crece() - BOT_GANA_SEGUIDOR_S * 1000) < 1, "sin dificultad: el tiempo base"
amigos = 0
for _ in range(40):
    ya = set(g.vecinos(bot))
    habia_amigos = any(p not in ya and any(p in g.vecinos(f) for f in ya) for p in red._presos())
    nuevo = red._ganar_seguidor(bot)
    if nuevo is None:
        break
    assert nuevo not in ya and g.datos[nuevo]["tipo"] == "preso"
    if habia_amigos:
        assert any(nuevo in g.vecinos(f) for f in ya), "prefiere a un amigo de un seguidor"
        amigos += 1
assert red.seguidores(bot) == BOT_MAX_SEGUIDORES, red.seguidores(bot)
assert red._ganar_seguidor(bot) is None, "no pasa del máximo"
assert red.seguidores_ganados == BOT_MAX_SEGUIDORES - SEGUIDORES_BOT

# Con el reloj: los demás bots ganan uno cada cada_cuanto_crece().
otro = red.bots()[1]
antes = red.seguidores(otro)
g.datos[otro]["crece_ms"] = red.cada_cuanto_crece()
for _ in range(int(red.cada_cuanto_crece() // DT) + 2):
    red.actualizar(DT)
assert red.seguidores(otro) == antes + 1, (red.seguidores(otro), antes)
tutorial = juego.tutorial
juego.tutorial = type("T", (), {"activo": True})()
for _ in range(int(red.cada_cuanto_crece() // DT) + 2):
    red.actualizar(DT)
assert red.seguidores(otro) == antes + 1, "en el tutorial no crece"
juego.tutorial = tutorial

# Más lento en las dificultades fáciles.
from juego import dificultad
juego.dificultad = dificultad.Dificultad("facil")
assert red.cada_cuanto_crece() > BOT_GANA_SEGUIDOR_S * 1000
juego.dificultad = None
print(f"1. crece de a uno ({amigos} por amigos de seguidores) hasta {BOT_MAX_SEGUIDORES}, "
      "no en el tutorial, más lento en Fácil: OK")

# -- 2. Con más seguidores, el rumor llega de una vez a más ---------------------------------------


def primer_nivel(red, autor):
    for n in red._presos():
        red.grafo.datos[n]["color"] = GRIS
    pub = red.lanzar_rumor(RUMORES[0], bot=autor) or red.lanzar_rumor(bot=autor)
    prop = next(p for p in red.propagaciones if p.pub is pub)
    red._avanzar(prop)
    alcanzados = {n for n in pub.alcanzados if red.grafo.datos[n]["tipo"] == "preso"}
    red.propagaciones.remove(prop)
    red.publicaciones.remove(pub)
    return len(alcanzados)


chico = red.bots()[2]
assert primer_nivel(red, chico) == red.seguidores(chico) - sum(
    red.grafo.datos[n]["tipo"] != "preso" for n in red.grafo.vecinos(chico))
grande = primer_nivel(red, bot)
assert grande == BOT_MAX_SEGUIDORES, grande
print(f"2. el primer salto de un rumor: {primer_nivel(red, chico)} prisioneros con el bot nuevo, "
      f"{grande} con el que creció: OK")

# -- 3. Aviso a todos a los 6 -----------------------------------------------------------------------
juego = nueva_partida()
red = juego.nexus
bot = red.bots()[0]
for j in juego.jugadores:
    j.mensaje = ""
while red.seguidores(bot) < AVISOS_SEGUIDORES[0] - 1:
    red._ganar_seguidor(bot)
assert not any("seguidores" in j.mensaje for j in juego.jugadores)
red._ganar_seguidor(bot)
assert all(f"ya le llega a {AVISOS_SEGUIDORES[0]} personas" in j.mensaje for j in juego.jugadores), \
    [j.mensaje for j in juego.jugadores]
assert "falsa" not in juego.jugadores[0].mensaje, "el aviso no dice que es falsa"
print("3. aviso a todos cuando llega a", AVISOS_SEGUIDORES[0], "seguidores: OK")

# -- 4. Reportar temprano / tarde, y los resultados ----------------------------------------------
j1, j2 = juego.jugadores
temprano = red.bots()[1]
texto, puntos = red.reportar(j1, temprano)
assert "La cortaron a tiempo" in texto and f"le llegaba a {SEGUIDORES_BOT}" in texto, texto
ganados = red.ganados(bot)
texto, _ = red.reportar(j2, bot)
assert f"ganó {ganados} seguidores" in texto, texto
assert red.resumen()["seguidores_bots"] == red.seguidores_ganados

juego = nueva_partida()
red = juego.nexus
for b in red.bots():
    for _ in range(4):
        red._ganar_seguidor(b)
assert red.seguidores_ganados >= SEGUIDORES_PARA_CONSEJO
resumen = red.resumen()
assert "Nadie reportó las cuentas falsas" in resumen["consejo"], resumen["consejo"]
print("4. reportar temprano/tarde lo dice, y los resultados lo cuentan: OK")

# -- 5. Se ve en el celular y en el grafo --------------------------------------------------------
j1, j2 = juego.jugadores
bot = max(red.bots(), key=red.seguidores)
llega = next(p for p in red._presos() if red.nodo_de(j1) in red.grafo.vecinos(p))
red.grafo.agregar_arista(bot, llega)
pub = red.lanzar_rumor(bot=bot)
pub.alcanzados.update({llega, red.nodo_de(j1)})
pub.via[red.nodo_de(j1)] = llega
pub.via[llega] = bot
j1.abrir_panel(celular._post(juego, j1, pub))
foto(juego, "post")
j1.cursor = [a for _, a in j1.panel["opciones"]].index("rastrear")
celular.confirmar(juego, j1)
assert j1.panel["vista"] == "origen" and j1.panel["origen"] == bot
foto(juego, "origen")
j1.cursor = [a for _, a in j1.panel["opciones"]].index("reportar_origen")
celular.confirmar(juego, j1)
foto(juego, "reportado")
j1.cerrar_panel()
juego.vista_grafo = "nexus"
foto(juego, "grafo")
print("5. seguidores en la publicación, el origen y el grafo: OK (capturas bots_crecen_*.png)")
print("\nTODO OK")
