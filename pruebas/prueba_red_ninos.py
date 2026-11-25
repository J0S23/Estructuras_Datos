"""La sala oculta de los niños en red (misiones/sala_secreta.py).

    python pruebas/prueba_red_ninos.py

En el mismo proceso, como pruebas/prueba_red_capturas.py: un servidor (sin
sockets) en MapaFinal, normal y en modo feria, y el espejo de un cliente.
Se repara la cápsula, se abre la pared, un jugador entra a la sala, hablan,
votan (con las acciones que manda el cliente: "derecha" e "interactuar") y
llegan los aliens. En cada paso se pasa la instantánea por JSON al espejo y
se revisa que el cliente vea lo mismo: la pared abierta (y sin su losa en
las paredes, o el campo de visión seguía tapado), la sala pintada, el menú de
la votación, los votos, el contador y el final. Al final se compara el
dibujo del servidor y del cliente píxel por píxel durante la votación.
"""

import json
import os
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["NEXUS_SIN_EFECTOS"] = "1"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

from cliente_servidor.servidor import Servidor, Teclas
from cliente_servidor.espejo import Espejo
from cliente_servidor.protocolo import Reconstructor, comprimir

CARPETA = os.environ.get("NEXUS_CAPTURAS") or os.path.join(tempfile.gettempdir(), "nexus_capturas")
os.makedirs(CARPETA, exist_ok=True)
TAMANO = (1280, 720)


def pasar(s, espejo):
    mensaje = json.loads(json.dumps({"tipo": "estado", "c": s.cuadro, "base": None,
                                     "z": comprimir(s.instantanea())}))
    espejo.aplicar(Reconstructor().aplicar(mensaje))


def cuadros(s, n):
    s.teclas = Teclas()
    for _ in range(n):
        s.juego._actualizar_partida(16)


def poner(j, punto):
    j.personaje.hitbox.center = punto
    j.personaje.sync_sprite_from_hitbox()


def diferencia(a, b):
    pa = pygame.image.tobytes(a, "RGB")
    pb = pygame.image.tobytes(b, "RGB")
    distintos = 0
    for i in range(0, len(pa), 3 * 7):
        if abs(pa[i] - pb[i]) + abs(pa[i + 1] - pb[i + 1]) + abs(pa[i + 2] - pb[i + 2]) > 24:
            distintos += 1
    return distintos / (len(pa) / (3 * 7))


def probar(feria):
    nombre = "feria" if feria else "normal"
    s = Servidor(2, avisar=lambda t: None, semilla=11, presentaciones=False, mapa="MapaFinal", feria=feria)
    s.preparar_partida()
    s.lista.set()
    for p in s.puestos:
        p.ocupado = True
    g = s.juego
    if g.tutorial is not None:
        g.saltar_tutorial()
    from juego.app import Game
    espejo = Espejo(Game(), s.bienvenida(s.puestos[0]))
    espejo.preparar()
    s.juego.screen = espejo.g.screen
    sala, sala_c = g.sala_secreta, espejo.g.sala_secreta
    assert sala is not None and sala.activa, "MapaFinal tiene sala oculta"
    assert sala_c is not None and sala_c.activa, "el espejo también la arma"
    assert sala.puerta in g.mundo.paredes and sala_c.puerta in espejo.g.mundo.paredes, "cerrada: la losa tapa"
    assert len(sala_c.pistas) == len(sala.pistas) == 3, (len(sala.pistas), len(sala_c.pistas))
    for j in g.jugadores:
        j.invulnerable_ms = 10 ** 9

    # 1) Se repara la cápsula: se abre la pared.
    g.mision.abrir_puerta()
    g.mision.empezar_huida()
    cuadros(s, 200)
    pasar(s, espejo)
    assert sala.estado == "abierta", sala.estado
    assert sala_c.estado == "abierta", sala_c.estado
    assert sala.puerta not in g.mundo.paredes, "servidor: la losa ya no tapa"
    assert sala_c.puerta not in espejo.g.mundo.paredes, "cliente: la losa ya no tapa (campo de visión)"
    from screens import sala_secreta as dibujo_sala
    assert dibujo_sala.pintura(espejo.g.mundo, sala_c), "cliente: lo de adentro se arma (aparte del mapa)"

    # 2) Una pista: la revisa J2 (con su tecla de interactuar).
    pista = sala.pistas[0]
    poner(g.jugadores[1], (pista["punto"][0] - 30, pista["punto"][1]))
    s._pulsar(g.jugadores[1], "interactuar")
    cuadros(s, 2)
    pasar(s, espejo)
    assert sala_c.pistas[0]["encontrada"], "la pista revisada se ve revisada en el cliente"
    assert espejo.g.jugadores[1].mensaje, "y el cliente ve lo que dijo"

    # 3) Entra J1: hablan y empieza la votación.
    poner(g.jugadores[0], (sala.sala.left + 120, sala.pasillo.centery))
    poner(g.jugadores[1], (sala.sala.left + 60, sala.pasillo.centery + 40))
    cuadros(s, 3)
    pasar(s, espejo)
    assert sala_c.estado == "dialogo" and sala_c.entraron
    assert espejo.g.jugadores[0].mensaje, "el diálogo llega al cliente"
    # El celular del piso: J2 lo revisa (se abre en el cliente) y lo cierra.
    poner(g.jugadores[1], (sala.celular[0] - 30, sala.celular[1]))
    s._pulsar(g.jugadores[1], "interactuar")
    cuadros(s, 2)
    pasar(s, espejo)
    assert (espejo.g.jugadores[1].panel or {}).get("tipo") == "celular_nino", "el celular en el cliente"
    red = pygame.Surface(TAMANO)
    espejo.g._dibujar_partida_en(red, list(espejo.g.jugadores), espejo.g._extras_dibujo())
    pygame.image.save(red, os.path.join(CARPETA, f"ninos_{nombre}_celular_red.png"))
    s._pulsar(g.jugadores[1], "interactuar")
    cuadros(s, 2)
    pasar(s, espejo)
    assert espejo.g.jugadores[1].panel is None, "cerrado"
    while sala.estado == "dialogo":
        cuadros(s, 1)
    from data.historia import SE_APAGA
    pasar(s, espejo)
    assert SE_APAGA["capsula"] in sala_c.apagadas, ("la que se apaga, apagada en el cliente", sala_c.apagadas)
    cuadros(s, 30)
    pasar(s, espejo)
    assert sala_c.estado == "votacion"
    for j in espejo.g.jugadores:
        assert (j.panel or {}).get("tipo") == "votacion", "el menú de la votación en el cliente"

    # 4) Votan con lo que manda el cliente. J2 cierra el menú con "volver": vuelve.
    s._pulsar(g.jugadores[0], "derecha")
    s._pulsar(g.jugadores[0], "interactuar")
    s._pulsar(g.jugadores[1], "volver")
    cuadros(s, 2)
    pasar(s, espejo)
    assert sala_c.votos[0] == "quedarse", sala_c.votos
    assert (g.jugadores[1].panel or {}).get("tipo") == "votacion", "el menú no se puede cerrar"
    assert 0 < sala_c.quedan_ms < sala_c.total_ms
    cuadros(s, 300)
    pasar(s, espejo)
    local = pygame.Surface(TAMANO)
    g._dibujar_partida_en(local, list(g.jugadores), g._extras_dibujo())
    red = pygame.Surface(TAMANO)
    espejo.g._dibujar_partida_en(red, list(espejo.g.jugadores), espejo.g._extras_dibujo())
    pygame.image.save(local, os.path.join(CARPETA, f"ninos_{nombre}_local.png"))
    pygame.image.save(red, os.path.join(CARPETA, f"ninos_{nombre}_red.png"))
    d = diferencia(local, red)
    print(f"{nombre}: votación, {d * 100:.2f} % de píxeles distintos")
    assert d < 0.03, f"el cliente no se ve como el local en la votación ({d * 100:.1f} %)"

    # 5) J2 también vota: el contador se acorta; llegan los aliens y termina.
    s._pulsar(g.jugadores[1], "interactuar")       # (el cursor estaba en "escapar")
    cuadros(s, 2)
    assert sala.acortado and sala.votos == ["quedarse", "escapar"], sala.votos
    while sala.estado == "votacion":
        cuadros(s, 1)
    assert sala.resultado == "quedarse", "empate: se quedan"
    while g.mision.resultado is None:
        cuadros(s, 1)
    pasar(s, espejo)
    assert espejo.g.mision.final == "quedarse" and espejo.g.mision.resultado == "derrota", \
        (espejo.g.mision.final, espejo.g.mision.resultado)
    print(f"{nombre}: final '{espejo.g.mision.final}' en el cliente")


pygame.init()
probar(False)
probar(True)
print(f"capturas en {CARPETA}")
print("OK prueba_red_ninos")
