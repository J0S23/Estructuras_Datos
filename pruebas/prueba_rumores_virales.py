"""Rumores que se vuelven virales y desmentidos que llegan tarde (redes/nexus.py).

    python pruebas/prueba_rumores_virales.py

1. Llegar tarde convence menos: `convence_a_tiempo` (1 hasta TARDE_DESDE,
   CONVENCE_TARDE cuando ya es viral) y los mensajes "¡A tiempo!" /
   "Llegaste tarde: N personas ya se lo habían creído".
2. Un rumor que nadie desmiente se vuelve viral: los grises se lo creen,
   todos reciben el aviso y cuenta para los resultados.
3. Lo que hace la gente en cada caso, y que desmentirlo lo deshace:
   - casilleros: los prisioneros que se lo creen se meten en casilleros (no se
     puede entrar ahí; "Ocupado") y salen al desmentirlo;
   - cápsula: el que te seguía se rinde y nadie más acepta ir;
   - terminal: se desconecta la terminal NEXUS más cercana (no abre);
   - celdas: la fuga avanza a FUGA_VIRAL.
4. El celular: la barrita en la tarjeta y el texto en la publicación.
Capturas en pruebas/capturas/viral_*.png.
"""

import os
import sys
import math

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
from redes.nexus import RedNexus, GRIS, ROJO, VERDE
from data.nexus import RUMORES, TARDE_DESDE, CONVENCE_TARDE, FUGA_VIRAL, ESCONDITES_VIRAL
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


def frames(juego, n):
    for _ in range(n):
        juego._actualizar_partida(DT)


def rumor_de(lugar):
    return next(r for r in RUMORES if r["lugar"] == lugar)


def hacer_viral(juego, pub):
    pub.viral_ms = juego.nexus.limite_viral() - 5
    frames(juego, 2)
    assert pub.viral, "no se volvió viral"


def foto(juego, nombre):
    juego._dibujar()
    pygame.image.save(juego.screen, os.path.join(OUT, f"viral_{nombre}.png"))


# -- 1. Llegar tarde convence menos ---------------------------------------------------------------
assert RedNexus.convence_a_tiempo(0.0) == 1.0
assert RedNexus.convence_a_tiempo(TARDE_DESDE) == 1.0
assert abs(RedNexus.convence_a_tiempo(1.0) - CONVENCE_TARDE) < 1e-9
assert CONVENCE_TARDE < RedNexus.convence_a_tiempo(0.65) < 1.0

juego = nueva_partida()
red = juego.nexus
j1, j2 = juego.jugadores
a_tiempo = red.lanzar_rumor(rumor_de("consola"))
red.evidencias[j1].append(a_tiempo)
texto, _ = red.desmentir(j1, a_tiempo, False)
assert texto.startswith("¡A tiempo!"), texto
convence = [p for p in red.propagaciones if p.pub.desmiente is a_tiempo][0].prob
tarde = red.lanzar_rumor(rumor_de("fusibles"))
tarde.viral_ms = red.limite_viral() * 0.9
presos = red._presos()
for nodo in presos[:4]:
    red.grafo.datos[nodo]["color"] = ROJO
    tarde.creyentes.add(nodo)
red.evidencias[j2].append(tarde)
texto, _ = red.desmentir(j2, tarde, False)
assert texto.startswith("Llegaste tarde: 4 personas ya se lo habían creído"), texto
convence_tarde = [p for p in red.propagaciones if p.pub.desmiente is tarde][0].prob
assert convence_tarde < convence, (convence_tarde, convence)
assert red.creyeron_tarde == 4
print(f"1. llegar tarde convence menos ({convence:.2f} a tiempo, {convence_tarde:.2f} tarde) "
      "y lo dice: OK")

# -- 2 y 3a. Casilleros --------------------------------------------------------------------------
juego = nueva_partida()
red = juego.nexus
j1, j2 = juego.jugadores
for npc in juego.npcs.npcs:                      # que haya quién se lo crea
    red.grafo.datos[npc.nodo]["color"] = GRIS
grises = sum(red.color(n) == GRIS for n in red._presos())
pub = red.lanzar_rumor(rumor_de("escondite"))
hacer_viral(juego, pub)
assert red.virales == 1
assert any("se volvió viral" in getattr(j, "mensaje", "") for j in juego.jugadores), \
    [getattr(j, "mensaje", "") for j in juego.jugadores]
assert sum(red.color(n) == GRIS for n in red._presos()) < grises, "a los grises les llegó"
ocupados = [e for e in juego.escondites if e.get("npc") is not None]
assert 1 <= len(ocupados) <= ESCONDITES_VIRAL, len(ocupados)
assert all(red.color(e["npc"].nodo) != VERDE for e in ocupados), "los que saben la verdad no se esconden"
frames(juego, 25000 // DT + 5)                     # (TIEMPO_MAX_ESCONDERSE_MS)
assert all(e["npc"].escondido_en is e for e in ocupados), "se metieron"
esc = ocupados[0]
j1.personaje.hitbox.midbottom = esc["rect"].midbottom
j1.personaje.sync_sprite_from_hitbox()
frames(juego, 1)
assert juego.escondite_bajo(j1) is None and juego.escondite_con_prisionero(j1) is esc
j1.mensaje = ""
# (que no lea una nota o abra otra cosa que quede al lado del casillero)
juego.mision.interactuar = lambda jugador: False
juego.infiltrado = None
juego.guardia_planta = None
juego._tecla_en_partida(pygame.K_e)
assert not j1.escondido and "Ocupado" in j1.mensaje, (j1.mensaje, j1.panel)
foto(juego, "casillero_ocupado")
red.evidencias[j1].append(pub)
red.desmentir(j1, pub, False)
assert all(e.get("npc") is None for e in ocupados)
assert all(n.escondido_en is None and n.va_a_esconderse is None for n in juego.npcs.npcs)
resumen = red.resumen()
assert resumen["virales"] == 1 and "virales" in resumen["consejo"], resumen["consejo"]
print(f"2. se vuelve viral (aviso, grises, resultados) y 3a. {len(ocupados)} prisioneros "
      "ocupan casilleros y salen al desmentirlo: OK")

# -- 3b. Cápsula ----------------------------------------------------------------------------------
juego = nueva_partida()
red = juego.nexus
j1, j2 = juego.jugadores
npc = juego.npcs.npcs[0]
red.grafo.datos[npc.nodo]["color"] = VERDE
npc.siguiendo = j1
pub = red.lanzar_rumor(rumor_de("capsula"))
hacer_viral(juego, pub)
assert npc.siguiendo is None, "se rindió"
red.grafo.datos[npc.nodo]["color"] = VERDE
j1.personaje.hitbox.center = npc.centro
j1.personaje.sync_sprite_from_hitbox()
juego.npcs.hablar(j1)
assert npc.siguiendo is None and "se rindió" in j1.mensaje, j1.mensaje
red.evidencias[j1].append(pub)
red.desmentir(j1, pub, False)
juego.npcs.hablar(j1)
assert npc.siguiendo is j1, "desmentido: vuelve a querer ir"
print("3b. cápsula: el que te seguía se rinde y nadie acepta hasta desmentirlo: OK")

# -- 3c. Terminal NEXUS ---------------------------------------------------------------------------
juego = nueva_partida()
red = juego.nexus
j1, j2 = juego.jugadores
pub = red.lanzar_rumor(rumor_de("terminal"))
hacer_viral(juego, pub)
zona = pub.efecto.get("zona")
assert zona is not None and zona["desconectada"]
cercana = min((z for z in juego.zonas if z["tipo"] == "nexus"),
              key=lambda z: math.dist(z["rect"].center, pub.lugar))
assert zona is cercana
juego._abrir_nexus(j1, zona)
assert j1.panel is None and "desconectaron" in j1.mensaje
j1.personaje.hitbox.center = zona["rect"].center
j1.personaje.sync_sprite_from_hitbox()
foto(juego, "terminal")
red.evidencias[j1].append(pub)
red.desmentir(j1, pub, False)
assert not zona["desconectada"]
juego._abrir_nexus(j1, zona)
assert j1.panel is not None
j1.cerrar_panel()
print("3c. terminal: se desconecta la NEXUS más cercana y vuelve al desmentirlo: OK")

# -- 3d. Celdas ---------------------------------------------------------------------------------
juego = nueva_partida()
red = juego.nexus
j1, j2 = juego.jugadores
juego.mision.encarcelar(j1)
celda = j1.preso
celda["fuga_ms"] = 10000
frames(juego, 60)
normal = 10000 - celda["fuga_ms"]
pub = red.lanzar_rumor(rumor_de("celda"))
hacer_viral(juego, pub)
antes = celda["fuga_ms"]
frames(juego, 60)
lento = antes - celda["fuga_ms"]
assert abs(lento - normal * FUGA_VIRAL) <= DT, (lento, normal)
print(f"3d. celdas: la fuga avanza a {FUGA_VIRAL:.0%} ({lento} de {normal} ms): OK")

# -- 4. El celular ---------------------------------------------------------------------------------
juego = nueva_partida()
red = juego.nexus
j1, j2 = juego.jugadores
casi = red.lanzar_rumor(rumor_de("panel"))
casi.alcanzados.add(red.nodo_de(j1))
casi.viral_ms = red.limite_viral() * 0.8
viral = red.lanzar_rumor(rumor_de("puerta_doble") if juego.puertas_dobles else rumor_de("consola"))
if viral is not None:
    viral.alcanzados.add(red.nodo_de(j1))
    hacer_viral(juego, viral)
juego._tecla_en_partida(pygame.K_TAB)
foto(juego, "celular")
from screens.celular import _tarjeta
from juego.fuentes import fuente_de_tamano
f = fuente_de_tamano(16)
t = _tarjeta(red, j1, "misiones", casi, f, f, f, 300)
assert 0.79 < t["viral"] < 0.81
if viral is not None:
    t = _tarjeta(red, j1, "misiones", viral, f, f, f, 300)
    assert t["viral"] == 1.0 and any(c[0] == "¡Viral!" for c in t["chips"])
    indice = next(i for i, (_, p) in enumerate(j1.panel["opciones"]) if p is viral)
    j1.cursor = indice
    juego._tecla_en_partida(pygame.K_e)
    assert j1.panel["vista"] == "post"
    foto(juego, "post")
print("4. el celular muestra la barra y el aviso de viral: OK")
print("\nTODO OK")
