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

`probar_voces`: las voces grabadas viajan al cliente y suenan una sola vez
(dos en la puerta a la vez; cada línea del diálogo).

`probar_liberar`: el baúl de la prisión desde el cliente (el teclado, el
martillo al inventario), "liberar" en el menú en vez de "quedarse" y, al
ganar, que el cliente vea las cápsulas rotas, a los niños caminando donde
mismo que en el servidor y el final "liberados".
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


def probar_liberar(feria):
    nombre = "feria" if feria else "normal"
    s = Servidor(2, avisar=lambda t: None, semilla=5, presentaciones=False, mapa="MapaFinal", feria=feria)
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
    for j in g.jugadores:
        j.invulnerable_ms = 10 ** 9
    j1, j2 = g.jugadores[:2]
    baul = sala.baul
    assert baul is not None, "el baúl de la prisión"
    poner(j1, (baul["rect"].centerx, baul["rect"].bottom + 30))
    s._pulsar(j1, "interactuar")
    cuadros(s, 2)
    pasar(s, espejo)
    panel = espejo.g.jugadores[0].panel or {}
    assert panel.get("titulo") == "Baúl con candado" and len(panel.get("opciones", [])) == 4, panel
    # Abierto sin querer: el botón del celular lo cierra sin marcar (y no abre el celular).
    s._pulsar(j1, "celular")
    cuadros(s, 2)
    pasar(s, espejo)
    assert espejo.g.jugadores[0].panel is None and not baul["abierto"], "el celular cierra el teclado"
    s._pulsar(j1, "interactuar")
    cuadros(s, 2)
    j1.cursor = j1.panel["codigos"].index(baul["codigo"])
    s._pulsar(j1, "interactuar")
    cuadros(s, 2)
    s._pulsar(j1, "interactuar")
    cuadros(s, 2)
    pasar(s, espejo)
    assert sala_c.baul["abierto"] and not sala_c.baul["con_martillo"], sala_c.baul
    assert "martillo" in espejo.g.jugadores[0].objetos, "el martillo en el inventario del cliente"

    g.mision.abrir_puerta()
    g.mision.empezar_huida()
    cuadros(s, 200)
    poner(j1, (sala.sala.left + 120, sala.pasillo.centery))
    poner(j2, (sala.celular[0] - 30, sala.celular[1]))
    cuadros(s, 3)
    while sala.estado == "dialogo":
        cuadros(s, 1)
    s._pulsar(j2, "interactuar")
    cuadros(s, 2)
    s._pulsar(j2, "interactuar")
    cuadros(s, 30)
    pasar(s, espejo)
    assert sala_c.estado == "votacion" and sala_c.claves == ["escapar", "liberar"], sala_c.claves
    textos = [o["texto"] for o in (espejo.g.jugadores[0].panel or {}).get("opciones", [])]
    assert textos == ["Correr a la cápsula", "Romper las cápsulas y sacarlos"], textos
    for j in (j1, j2):
        s._pulsar(j, "abajo")                       # (con el stick: la otra opción)
        s._pulsar(j, "interactuar")
    cuadros(s, 2)
    assert sala.votos == ["liberar", "liberar"], sala.votos
    while sala.estado == "votacion":
        cuadros(s, 1)
    assert sala.resultado == "liberar"
    revisado = False
    while g.mision.resultado is None:
        cuadros(s, 1)
        if sala.fase_liberar == "capsula" and sala.fase_ms > 2500 and not revisado:
            revisado = True
            pasar(s, espejo)
            assert all(sala_c.rota(i) for i in sala.vivas()), "las cápsulas rotas en el cliente"
            for i in sala.vivas():
                a, b = sala.posicion_nino(i), sala_c.posicion_nino(i)
                assert (a is None) == (b is None) and (a is None or abs(a[0] - b[0]) + abs(a[1] - b[1]) < 1), \
                    (i, a, b)
            red = pygame.Surface(TAMANO)
            espejo.g._dibujar_partida_en(red, list(espejo.g.jugadores), espejo.g._extras_dibujo())
            pygame.image.save(red, os.path.join(CARPETA, f"ninos_{nombre}_liberar_red.png"))
    assert revisado
    pasar(s, espejo)
    assert (espejo.g.mision.final, espejo.g.mision.resultado) == ("liberados", "victoria"), \
        (espejo.g.mision.final, espejo.g.mision.resultado)
    print(f"{nombre}: liberar -> final '{espejo.g.mision.final}' en el cliente")


def probar_voces(feria):
    """Las voces en red: suenan en el servidor, viajan como un sonido más
    ("voz:...") y el cliente las toca. Dos llegan juntos a la puerta (falta el
    tercero): la frase suena una sola vez. Y en el diálogo cada línea suena
    una vez, con la voz del que la dice."""
    nombre = "feria" if feria else "normal"
    s = Servidor(3, avisar=lambda t: None, semilla=7, presentaciones=False, mapa="MapaFinal", feria=feria)
    s.preparar_partida()
    s.lista.set()
    for p in s.puestos:
        p.ocupado = True
    g = s.juego
    if g.tutorial is not None:
        g.saltar_tutorial()
    from juego.app import Game
    from juego import voces
    espejo = Espejo(Game(), s.bienvenida(s.puestos[0]))
    espejo.preparar()
    sala = g.sala_secreta
    for j in g.jugadores:
        j.invulnerable_ms = 10 ** 9
    g.mision.abrir_puerta()
    g.mision.empezar_huida()
    cuadros(s, 200)
    s.sonidos = []
    tocadas = []
    espejo.g.ambiente.sonar = lambda nombre, volumen=1.0, *a, **k: tocadas.append(nombre)

    def voces_enviadas():
        enviadas = [n for n, _ in s.sonidos if n.startswith(voces.PREFIJO)]
        pasar(s, espejo)
        espejo.sonar(s.sonidos)
        s.sonidos = []
        return enviadas

    j1, j2, j3 = g.jugadores[:3]
    poner(j3, (sala.puerta.centerx + 2000, sala.puerta.bottom + 600))
    poner(j1, (sala.puerta.centerx - 30, sala.puerta.bottom - 12))
    poner(j2, (sala.puerta.centerx + 30, sala.puerta.bottom - 12))
    cuadros(s, 3)
    enviadas = voces_enviadas()
    assert len(enviadas) == 1 and enviadas[0].startswith(voces.PREFIJO + "sala_esperar"), enviadas
    assert [t for t in tocadas if t.startswith(voces.PREFIJO)] == enviadas, "el cliente la toca una vez"
    assert espejo.g.jugadores[0].mensaje == espejo.g.jugadores[1].mensaje, "los dos lo piensan (texto)"
    print(f"{nombre}: dos en la puerta, la voz viaja y suena una sola vez ({enviadas[0][4:]})")
    # Entran todos: cada línea del diálogo suena una vez, con la voz de quien la dice.
    poner(j1, (sala.sala.left + 120, sala.pasillo.centery))
    poner(j2, (sala.sala.left + 60, sala.pasillo.centery + 40))
    poner(j3, (sala.sala.left + 60, sala.pasillo.centery - 40))
    voces_enviadas()
    tocadas.clear()
    dichas = []
    for _ in range(6000):
        cuadros(s, 1)
        dichas += voces_enviadas()
        if sala.estado not in ("abierta", "dialogo"):
            break
    assert sala.estado == "espera", sala.estado
    lineas = [d[len(voces.PREFIJO):] for d in dichas]
    esperadas = [voces.de_rol(sala._voz_linea(i), sala._hablantes[i].rol) for i in range(len(sala._hablantes))]
    esperadas = [e for e in esperadas if e]
    assert lineas == esperadas, (lineas, esperadas)
    assert [t[len(voces.PREFIJO):] for t in tocadas if t.startswith(voces.PREFIJO)] == lineas
    print(f"{nombre}: diálogo en red, {len(lineas)} voces, cada una una vez y en orden")


pygame.init()
probar(False)
probar(True)
probar_liberar(False)
probar_liberar(True)
probar_voces(False)
probar_voces(True)
print(f"capturas en {CARPETA}")
print("OK prueba_red_ninos")
