"""Puertas para dos y compuertas.

**Puerta para dos**: una puerta reforzada con dos paneles. Se abre solo si dos
jugadores distintos mantienen la tecla de interactuar, cada uno en un panel, al
mismo tiempo. Obliga a coordinarse con la pantalla partida ("¿ya estás?").
Una vez abierta, queda abierta.

**Compuerta**: una reja que el evento aleatorio "cierre de emergencia"
(eventos.py) baja un rato y luego vuelve a subir.

La puerta para dos, mientras está cerrada, frena a **todos**: a los jugadores
(`Game._colisiona_jugador`) y a los aliens (`mundo.puertas_alien`, que usan
`mundo.colisiona_alien` y la búsqueda de caminos). La compuerta frena solo a
los jugadores: a los aliens la nave les abre paso (es su nave). Ninguna va en
`mundo.paredes` como la puerta de la prisión.

Las dos se ponen en el mapa con el editor (Editores/editor_mapa.py).
"""

import math

import pygame

from juego.fuentes import fuente
from juego import sprites_objetos
from juego import efectos


TIEMPO_ABRIR_S = 1.4          # los dos manteniendo a la vez
RADIO_PANEL = 46               # qué tan cerca del panel hay que estar
TAMANO_PANEL = (30, 30)
PUNTOS_PUERTA_DOBLE = 15

COLOR_BIEN = (96, 200, 120)
COLOR_AVISO = (255, 214, 64)
COLOR_MAL = (245, 130, 120)


def _rect_de(datos, mundo):
    rect = pygame.Rect(0, 0, max(8, int(datos["ancho"] * mundo.ancho)),
                       max(8, int(datos["alto"] * mundo.alto)))
    rect.center = (int(datos["rx"] * mundo.ancho), int(datos["ry"] * mundo.alto))
    return rect


def crear_puertas_dobles(objetos, mundo):
    puertas = []
    for datos in objetos.get("puertas_dobles", []):
        paneles = []
        for rx, ry in datos.get("paneles", [])[:2]:
            panel = pygame.Rect(0, 0, *TAMANO_PANEL)
            panel.center = (int(rx * mundo.ancho), int(ry * mundo.alto))
            paneles.append(panel)
        if len(paneles) < 2:
            print("[AVISO] Una puerta para dos no tiene sus dos paneles: se deja abierta.")
        puertas.append({"rect": _rect_de(datos, mundo), "paneles": paneles,
                        "abierta": len(paneles) < 2, "progreso": 0.0,
                        "en_panel": [None, None]})
    return puertas


def crear_compuertas(objetos, mundo):
    return [{"rect": _rect_de(datos, mundo), "cerrada": False}
            for datos in objetos.get("compuertas", [])]


def bloquea(puertas, compuertas, rect):
    """True si una puerta para dos cerrada o una compuerta bajada choca con `rect`."""
    for puerta in puertas:
        if not puerta["abierta"] and puerta["rect"].colliderect(rect):
            return True
    for compuerta in compuertas:
        if compuerta["cerrada"] and compuerta["rect"].colliderect(rect):
            return True
    return False


def panel_cerca(puertas, jugador):
    """(puerta, índice del panel) frente al que está el jugador, o None."""
    c = jugador.hitbox.center
    for puerta in puertas:
        if puerta["abierta"]:
            continue
        for i, panel in enumerate(puerta["paneles"]):
            if math.dist(c, panel.center) <= RADIO_PANEL:
                return puerta, i
    return None


def actualizar(puertas, sosteniendo, dt, al_abrir=None):
    """`sosteniendo` son los jugadores que mantienen la tecla este frame.

    Cada panel lo ocupa un jugador distinto; si los dos paneles están
    ocupados, la puerta avanza. Si alguno suelta, el progreso se pierde de a
    poco (no de golpe, para que un parpadeo no los castigue).
    """
    for puerta in puertas:
        if puerta["abierta"] or puerta.get("sin_corriente"):
            continue        # (sin corriente: una noticia de NEXUS que nadie arregló, redes/nexus._empeorar)
        en_panel = [None, None]
        for jugador in sosteniendo:
            cerca = panel_cerca([puerta], jugador)
            if cerca is None:
                continue
            i = cerca[1]
            if en_panel[i] is None and jugador not in en_panel:
                en_panel[i] = jugador
        puerta["en_panel"] = en_panel
        if en_panel[0] is not None and en_panel[1] is not None:
            puerta["progreso"] = min(1.0, puerta["progreso"] + dt / 1000 / TIEMPO_ABRIR_S)
            for jugador in en_panel:
                jugador.progreso = ("Abriendo la puerta", puerta["progreso"])
            if puerta["progreso"] >= 1:
                puerta["abierta"] = True
                for jugador in en_panel:
                    jugador.sumar_puntos(PUNTOS_PUERTA_DOBLE)
                    jugador.avisar(f"¡Abrimos la puerta! +{PUNTOS_PUERTA_DOBLE}", COLOR_BIEN)
                if al_abrir is not None:
                    al_abrir(puerta)
        else:
            puerta["progreso"] = max(0.0, puerta["progreso"] - dt / 1000 / (TIEMPO_ABRIR_S * 2))
            for jugador in en_panel:
                if jugador is not None:
                    jugador.progreso = ("Esperando al otro panel...", puerta["progreso"])


def pista(puertas, jugador):
    cerca = panel_cerca(puertas, jugador)
    if cerca is None:
        return None
    return "Mantener: panel (se necesitan dos)"


# -- Dibujo ------------------------------------------------------------------------------

ALTO_PANEL_PUERTA = 40


def dibujar(screen, offset, camara, puertas, compuertas, tiempo_ms):
    for puerta in puertas:
        rect = puerta["rect"]
        r = rect.move(-offset[0], -offset[1])
        # Cada cosa se dibuja si ELLA está en pantalla: los paneles pueden estar
        # lejos de la puerta, y antes solo se veían cuando la puerta entraba
        # en la cámara.
        if rect.inflate(60, 60).colliderect(camara):
            # Se abre deslizándose (juego/efectos.py lleva cuánto va).
            abierta = efectos.apertura("puerta_doble", rect, puerta["abierta"])
            if abierta >= 1:
                pygame.draw.rect(screen, (60, 70, 90), r, 2)
            elif abierta <= 0:
                _dibujar_reforzada(screen, r, puerta["progreso"])
            else:
                _dibujar_abriendose(screen, r, abierta)
        for i, panel in enumerate(puerta["paneles"]):
            if not panel.inflate(60, 60).colliderect(camara) and not (
                    not puerta["abierta"] and camara.clipline(panel.center, rect.center)):
                continue          # ni el panel ni su línea a la puerta se ven aquí
            p = panel.move(-offset[0], -offset[1])
            ocupado = puerta["en_panel"][i] is not None
            if puerta["abierta"]:
                luz = COLOR_BIEN
            elif ocupado:
                luz = COLOR_AVISO
            else:
                luz = (236, 70, 60) if (tiempo_ms // 500) % 2 else (120, 40, 40)
            img = sprites_objetos.sprite("panel_puerta", ALTO_PANEL_PUERTA)
            if img is not None:
                # El escáner de mano de Anny, con el borde del color de su estado.
                pos = img.get_rect(center=p.center)
                screen.blit(img, pos)
                sprites_objetos.resaltar(screen, img, pos.topleft, luz, 3)
            else:
                pygame.draw.rect(screen, (10, 12, 20), p.move(2, 2), border_radius=4)
                pygame.draw.rect(screen, (70, 78, 100), p, border_radius=4)
                pygame.draw.rect(screen, luz, p.inflate(-14, -14), border_radius=3)
                pygame.draw.rect(screen, (20, 22, 34), p, 2, border_radius=4)
            # Una línea punteada del panel a la puerta: son pareja.
            if not puerta["abierta"]:
                _punteada(screen, p.center, r.center, (255, 214, 64, 90))
    for compuerta in compuertas:
        rect = compuerta["rect"]
        if not rect.colliderect(camara):
            continue
        # Baja desde arriba (y sube) en vez de aparecer: 1 = arriba del todo.
        arriba = efectos.apertura("compuerta", rect, not compuerta["cerrada"])
        if arriba >= 1:
            continue
        r = rect.move(-offset[0], -offset[1])
        if arriba <= 0:
            _dibujar_reja(screen, r, tiempo_ms)
        else:
            _dibujar_reja_bajando(screen, r, 1 - arriba, tiempo_ms)


def _dibujar_reforzada(screen, r, progreso):
    pygame.draw.rect(screen, (46, 52, 70), r)
    # Franjas amarillas y negras.
    capa = pygame.Surface(r.size, pygame.SRCALPHA)
    paso = 14
    for i in range(-r.height, r.width + r.height, paso * 2):
        pygame.draw.polygon(capa, (255, 200, 40, 150),
                            [(i, 0), (i + paso, 0), (i + paso - r.height, r.height), (i - r.height, r.height)])
    screen.blit(capa, r.topleft)
    pygame.draw.rect(screen, (20, 22, 34), r, 3)
    if progreso > 0:
        barra = pygame.Rect(r.x, r.bottom + 4, int(r.width * progreso), 5)
        pygame.draw.rect(screen, COLOR_BIEN, barra)
    etiqueta = fuente("small").render("x2", True, (255, 214, 64))
    screen.blit(etiqueta, etiqueta.get_rect(center=r.center))


def _dibujar_abriendose(screen, r, abierta):
    """La puerta para dos a medio abrir: sus dos hojas se meten en las paredes
    (por el lado largo) y por la rendija se ve la luz de adentro."""
    hoja = pygame.Surface(r.size, pygame.SRCALPHA)
    _dibujar_reforzada(hoja, hoja.get_rect(), 0)
    horizontal = r.width >= r.height
    largo = r.width if horizontal else r.height
    mitad = largo // 2
    queda = int(mitad * (1 - abierta))
    if horizontal:
        rendija = pygame.Rect(r.x + queda, r.y, r.width - 2 * queda, r.height)
    else:
        rendija = pygame.Rect(r.x, r.y + queda, r.width, r.height - 2 * queda)
    if rendija.width > 0 and rendija.height > 0:
        screen.fill((40, 120, 70), rendija, special_flags=pygame.BLEND_RGB_ADD)
    if queda <= 0:
        return
    if horizontal:
        screen.blit(hoja, (r.x, r.y), pygame.Rect(mitad - queda, 0, queda, r.height))
        screen.blit(hoja, (r.right - queda, r.y), pygame.Rect(mitad, 0, queda, r.height))
        pygame.draw.line(screen, COLOR_BIEN, (r.x + queda - 1, r.y), (r.x + queda - 1, r.bottom - 1), 2)
        pygame.draw.line(screen, COLOR_BIEN, (r.right - queda, r.y), (r.right - queda, r.bottom - 1), 2)
    else:
        screen.blit(hoja, (r.x, r.y), pygame.Rect(0, mitad - queda, r.width, queda))
        screen.blit(hoja, (r.x, r.bottom - queda), pygame.Rect(0, mitad, r.width, queda))
        pygame.draw.line(screen, COLOR_BIEN, (r.x, r.y + queda - 1), (r.right - 1, r.y + queda - 1), 2)
        pygame.draw.line(screen, COLOR_BIEN, (r.x, r.bottom - queda), (r.right - 1, r.bottom - queda), 2)


def _dibujar_reja_bajando(screen, r, bajado, tiempo_ms):
    """La compuerta a medio camino: se ve su parte de abajo saliendo del techo,
    con la barra de metal pesada en el borde."""
    alto = int(r.height * bajado)
    if alto <= 0:
        return
    reja = pygame.Surface(r.size)
    _dibujar_reja(reja, reja.get_rect(), tiempo_ms)
    screen.blit(reja, (r.x, r.y), pygame.Rect(0, r.height - alto, r.width, alto))
    barra = pygame.Rect(r.x - 2, r.y + alto - 6, r.width + 4, 6)
    pygame.draw.rect(screen, (70, 72, 86), barra)
    pygame.draw.rect(screen, (255, 200, 60), barra, 1)


def _dibujar_reja(screen, r, tiempo_ms):
    pygame.draw.rect(screen, (60, 20, 24), r)
    vertical = r.height > r.width
    n = max(3, (r.height if vertical else r.width) // 12)
    for i in range(n):
        if vertical:
            y = r.y + int((i + 0.5) * r.height / n)
            pygame.draw.line(screen, (200, 70, 60), (r.x, y), (r.right, y), 3)
        else:
            x = r.x + int((i + 0.5) * r.width / n)
            pygame.draw.line(screen, (200, 70, 60), (x, r.y), (x, r.bottom), 3)
    color = (255, 80, 60) if (tiempo_ms // 300) % 2 else (140, 40, 30)
    pygame.draw.rect(screen, color, r, 3)


def _punteada(screen, a, b, color):
    largo = math.dist(a, b)
    if largo < 1:
        return
    pasos = int(largo // 16)
    for i in range(0, pasos, 2):
        t0, t1 = i / max(1, pasos), (i + 1) / max(1, pasos)
        p0 = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
        p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
        pygame.draw.line(screen, color[:3], p0, p1, 1)
