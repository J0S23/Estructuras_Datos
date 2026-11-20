"""Los minijuegos de las tareas y las noticias verdaderas, en red.

    python pruebas/prueba_red_minijuegos.py

Sin sockets, en el mismo proceso (como pruebas/prueba_red_estado.py): un
servidor arma la partida y sus instantáneas pasan por JSON, el Reconstructor
y el espejo del cliente. Revisa que en red sea igual que en el juego local:

1. El servidor juega con minijuegos y con noticias verdaderas (antes las
   apagaba).
2. Cada minijuego llega al cliente con su clase y su estado y se dibuja
   igual que en el servidor (píxel a píxel).
3. La consola con las teclas que manda el cliente (`Servidor._pulsar`): las
   flechas lo juegan, al ganar se apaga la consola y el panel se cierra en el
   cliente. Sin barra de "mantener la tecla" ("prog" va vacío).
4. Entre instantánea e instantánea el cliente lo anima él (`Minijuego.animar`)
   y con la siguiente vuelve a lo del servidor.
5. El abono: el servidor juzga con lo que VIO el jugador (`visto`, como la
   aguja del casillero); la planta crece en el mapa del cliente (`visto`).
6. La noticia del candado: el candado llega al cliente, la ganzúa se juega
   con lo que vio el jugador, y al ganar el candado se quita y la noticia
   queda arreglada en el celular del cliente.
7. `Sesion._extra` manda lo visto con la tecla de interactuar.
"""

import json
import math
import os
import sys
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["NEXUS_SIN_EFECTOS"] = "1"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

from cliente_servidor import estado as E
from cliente_servidor.servidor import Servidor, Teclas
from cliente_servidor.espejo import Espejo
from cliente_servidor.protocolo import Reconstructor, comprimir

OUT = os.environ.get("NEXUS_CAPTURAS") or os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)
DT = 16


class Red:
    """Completa o delta, por JSON, como de verdad (ver prueba_red_estado.py)."""

    def __init__(self, servidor):
        self.s = servidor
        self.r = Reconstructor()
        self.anterior = None
        self.cuadro = 0

    def mandar(self, completa=False):
        ahora = self.s.instantanea()
        self.cuadro += 2
        if completa or self.anterior is None:
            m = {"tipo": "estado", "c": self.cuadro, "base": None, "z": comprimir(ahora)}
        else:
            cambios = {}
            for seccion, datos in ahora.items():
                d = E.diferencias(self.anterior.get(seccion, {}), datos)
                if d:
                    cambios[seccion] = d
            m = {"tipo": "estado", "c": self.cuadro, "base": self.cuadro - 2, "s": cambios}
        self.anterior = ahora
        secciones = self.r.aplicar(json.loads(json.dumps(m)))
        assert secciones is not None
        return secciones


pygame.init()
s = Servidor(2, avisar=lambda t: None, semilla=5, presentaciones=False, aliens_quietos=True,
             roles=["Tecnomante", "Forjador"])
s.preparar_partida()
s.lista.set()
for p in s.puestos:
    p.ocupado = True
g = s.juego
g.admin_invencible = True
g.quitar_cambiaformas()
if g.eventos is not None:
    g.eventos.reloj_ms = 10 ** 9
red = g.nexus
red.reloj_rumor_ms = red.reloj_normal_ms = 10 ** 9
for a in g.aliens:
    a.hitbox.topleft = (5, 5)
s.teclas = Teclas()

from juego.app import Game
from juego import tareas
from misiones import minijuegos
from entidades.jugador import WASD, FLECHAS
espejo = Espejo(Game(), s.bienvenida(s.puestos[0]))
espejo.preparar()
espejo.controles({0: WASD, 1: FLECHAS})
canal = Red(s)
m = espejo.g


def frames(n, mantener=None):
    for _ in range(n):
        teclas = Teclas()
        for i, acciones in (mantener or {}).items():
            j = g.jugadores[i]
            for a in acciones:
                for t in j.teclas.get(a, ()):
                    teclas[t] = True
        s.teclas = teclas
        g._actualizar_partida(DT)


def sincronizar(completa=False):
    secciones = canal.mandar(completa)
    espejo.aplicar(secciones)
    return secciones


def parar_en(jugador, punto):
    jugador.personaje.hitbox.center = (int(punto[0]), int(punto[1]))
    jugador.personaje.sync_sprite_from_hitbox()


def pulsar(i, accion, visto=None):
    """Lo que hace el servidor con una tecla que mandó el cliente."""
    buzon = s.buzones[i]
    with buzon.candado:
        buzon.pulsar.append(accion)
        if visto is not None:
            buzon.mini = visto
    s._aplicar_entradas()


def mismo_dibujo(mini_s, mini_m, nombre):
    """El minijuego del servidor y el del cliente, dibujados igual."""
    vista = pygame.Rect(0, 0, 960, 540)
    a, b = pygame.Surface(vista.size), pygame.Surface(vista.size)
    mini_s.dibujar(a, vista, g.jugadores[0])
    mini_m.dibujar(b, vista, m.jugadores[0])
    pygame.image.save(b, os.path.join(OUT, f"red_minijuego_{nombre}.png"))
    distintos = sum(1 for x in range(0, vista.w, 3) for y in range(0, vista.h, 3)
                    if a.get_at((x, y)) != b.get_at((x, y)))
    return distintos


j1, j2 = g.jugadores
c1, c2 = m.jugadores

# -- 1. Con minijuegos y noticias ----------------------------------------------------------
assert g.minijuegos, "el servidor apagó los minijuegos"
assert red.con_noticias, "el servidor apagó las noticias verdaderas"
print("1. el servidor juega con minijuegos y noticias verdaderas: OK")

# -- 2. Cada minijuego llega y se ve igual --------------------------------------------------
sincronizar(completa=True)
for tipo in minijuegos.TIPOS:
    mini = tareas.empezar(g, j1, tipo, None)
    frames(5)
    mini.tecla("derecha")
    mini.tecla("ok")
    frames(3)
    sincronizar()
    otro = tareas.de(c1)
    assert type(otro) is type(mini), f"{tipo}: al cliente le llegó {otro!r}"
    assert c1.ocupado, "con el minijuego abierto el cliente no lo ve ocupado (la predicción lo movería)"
    for clave in ("estado", "cursor", "rot", "arriba", "f", "a", "aciertos", "puestos", "base"):
        if hasattr(mini, clave):
            assert getattr(otro, clave) == getattr(mini, clave), (tipo, clave)
    distintos = mismo_dibujo(mini, otro, tipo)
    # (lo que se mece va con 3 decimales: un borde puede caer un píxel al lado)
    assert distintos <= 40, f"{tipo}: el cliente lo dibuja distinto ({distintos} puntos)"
    j1.cerrar_panel()
    sincronizar()
    assert tareas.de(c1) is None and c1.panel is None, "el panel no se cerró en el cliente"
print(f"2. los {len(minijuegos.TIPOS)} minijuegos llegan al cliente y se dibujan igual: OK")

# -- 3. La consola, con las teclas del cliente ---------------------------------------------
mision = g.mision
mision.abrir_puerta()
frames(2)
assert mision.fase == "sabotaje", mision.fase
j1.objetos.add("decodificador")
consola = mision.consolas[0]
parar_en(j1, consola["rect"].center)
frames(1)
assert j1.pista_mision and not j1.pista_mision.startswith("Mantener"), j1.pista_mision
# Mantener la tecla ya no hace nada (ni barra).
frames(60, {0: {"interactuar"}})
secciones = sincronizar()
assert consola["progreso"] == 0 and not j1.progreso and secciones["j0"]["prog"] is None, \
    "mantener la tecla todavía llena la barra"
pulsar(0, "interactuar")
mini = tareas.de(j1)
assert isinstance(mini, minijuegos.Senal), mini
sincronizar()
assert isinstance(tareas.de(c1), minijuegos.Senal)
x0 = j1.hitbox.x
f0 = mini.f
pulsar(0, "derecha" if mini.f < mini.FRECUENCIAS else "izquierda")
frames(3, {0: {"derecha"}})
assert mini.f != f0, "la flecha del cliente no movió la frecuencia"
assert j1.hitbox.x == x0, "se movió jugando el minijuego"
sincronizar()
assert tareas.de(c1).f == mini.f
while not mini.ganado:
    f, a = mini.objetivo
    while mini.f < f:
        pulsar(0, "derecha")
    while mini.f > f:
        pulsar(0, "izquierda")
    while mini.a < a:
        pulsar(0, "arriba")
    while mini.a > a:
        pulsar(0, "abajo")
    pulsar(0, "interactuar")
sincronizar()
assert tareas.de(c1).ganado, "el cliente no ve el ¡Listo!"
frames(minijuegos.FIN_MS // DT + 3)
sincronizar()
assert consola["progreso"] >= 1, "al ganar no se apagó la consola"
assert tareas.de(j1) is None and c1.panel is None
assert m.mision.consolas[0]["progreso"] >= 1, "el cliente no ve la consola apagada"
# Con "volver" (el botón B del mando) se cierra.
otra = mision.consolas[1]
parar_en(j1, otra["rect"].center)
frames(1)
pulsar(0, "interactuar")
assert tareas.de(j1) is not None
pulsar(0, "volver")
assert tareas.de(j1) is None, "B no cerró el minijuego"
print("3. la consola con las teclas del cliente, sin barra; B lo cierra: OK")

# -- 4. El cliente lo anima entre instantáneas -----------------------------------------------
mini = tareas.empezar(g, j1, "abono", None)
frames(2)
sincronizar()
otro = tareas.de(c1)
t0, fase0 = otro.t, otro.fase
time.sleep(0.05)
espejo.aplicar(canal.r.secciones)           # la misma instantánea: no llegó otra
assert otro.t > t0 and otro.fase > fase0, "el cliente no lo movió entre instantáneas"
frames(2)
sincronizar()
assert abs(otro.t - round(mini.t, 3)) < 1e-6 and abs(otro.fase - mini.fase) < 1e-3, \
    "con la instantánea nueva no volvió a lo del servidor"
j1.cerrar_panel()
print("4. entre instantáneas el cliente lo anima, y vuelve a lo del servidor: OK")

# -- 5. El abono, con lo que vio el jugador ---------------------------------------------------
planta = g.guardia_planta
p = planta.planta
j2.objetos.add("abono")
parar_en(j2, (p["rect"].centerx, p["rect"].bottom + 30))
frames(1)
pulsar(1, "interactuar")
mini = tareas.de(j2)
assert isinstance(mini, minijuegos.Abono), mini
sincronizar()
otro = tareas.de(c2)
assert isinstance(otro, minijuegos.Abono)
for _ in range(mini.necesarios):
    # El servidor tiene el saco lejos de la maceta, pero el jugador lo vio
    # justo encima (la red va atrasada): cuenta lo que vio.
    mini.fase = math.pi / 2                      # x = 1: lejos
    pulsar(1, "interactuar", visto=round(math.pi * 2 * (1 + _), 4))
    frames(mini.CAIDA_MS // DT + 2)
assert mini.aciertos == mini.necesarios, f"juzgó con el saco del servidor ({mini.aciertos} aciertos)"
frames(40)
sincronizar()
assert m.guardia_planta.planta["visto"] > 0.5, m.guardia_planta.planta.get("visto")
frames(minijuegos.FIN_MS // DT + 3)
sincronizar()
assert p["crecida"] and m.guardia_planta.planta["crecida"], "la planta no creció"
assert c2.panel is None
print("5. el abono se juzga con lo que vio el jugador y la planta crece en el cliente: OK")

# -- 6. La noticia del candado ------------------------------------------------------------------
from data.nexus import NOTICIAS, PUNTOS_ARREGLAR
pub = red.lanzar_noticia(next(n for n in NOTICIAS if n["lugar"] == "escondite"))
assert pub is not None
escondite = pub.efecto["escondite"]
k = g.escondites.index(escondite)
sincronizar()
assert m.escondites[k].get("candado"), "el candado no llegó al cliente"
mp = espejo.pubs.get(pub.id)
assert mp is not None and mp.tipo == "noticia" and not mp.arreglada
pub.alcanzados.add(red.nodo_de(j1))
parar_en(j1, escondite["rect"].center)
frames(2)
assert red.noticia_para(j1) is pub
puntos = j1.puntos
pulsar(0, "interactuar")
mini = tareas.de(j1)
assert isinstance(mini, minijuegos.Ganzua), mini
sincronizar()
assert isinstance(tareas.de(c1), minijuegos.Ganzua)
assert mismo_dibujo(mini, tareas.de(c1), "ganzua_candado") <= 40
en_linea = math.asin(2 * (sum(mini.ZONA) / 2) - 1)       # la altura del medio de la línea
while not mini.ganado:
    mini.fases[mini.puestos] = -math.pi / 2                # en el servidor, abajo del todo
    pulsar(0, "interactuar", visto=[mini.puestos, round(en_linea, 4)])
frames(minijuegos.FIN_MS // DT + 3)
sincronizar()
assert pub.arreglada and not escondite["candado"]
assert j1.puntos == puntos + PUNTOS_ARREGLAR
assert not m.escondites[k].get("candado"), "en el cliente sigue el candado"
assert espejo.pubs[pub.id].arreglada, "en el celular del cliente no está arreglada"
# Un "visto" de otro pin no cuenta.
otra = minijuegos.Ganzua()
otra.fases[0] = -math.pi / 2
otra.usar_visto([1, en_linea])
assert otra.tecla("ok") == "fallo", "usó lo visto de otro pin"
print("6. la noticia del candado: llega, la ganzúa con lo que vio, se arregla en el cliente: OK")

# -- 7. El cliente manda lo que vio -----------------------------------------------------------
from cliente_servidor import cliente


class SesionFalsa:
    def __init__(self):
        self.espejo = espejo

    def _vista_de(self, conexion):
        return None


class ConexionFalsa:
    jugador = 1


j2.objetos.add("abono")
p["crecida"] = False
p["progreso"] = 0.0
parar_en(j2, (p["rect"].centerx, p["rect"].bottom + 30))
frames(1)
pulsar(1, "interactuar")
sincronizar()
otro = tareas.de(c2)
assert isinstance(otro, minijuegos.Abono)
extra = cliente.Sesion._extra(SesionFalsa(), ConexionFalsa(), ["interactuar"])
assert extra and abs(extra.get("mini") - otro.fase) < 1e-3, extra
assert cliente.Sesion._extra(SesionFalsa(), ConexionFalsa(), ["derecha"]) is None
print("7. el cliente manda con la tecla dónde vio el saco: OK")

print("OK prueba_red_minijuegos")
