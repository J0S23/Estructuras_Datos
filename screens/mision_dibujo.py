"""Dibujo de lo de la misión (mision.py): puerta, notas, consolas, cápsula,
consumibles y los barrotes de quien está encerrado.

Figuras provisionales hasta que llegue el arte: cuando haya sprites, se cambian
aquí sin tocar la lógica.
"""

import math
import os

import pygame

from juego.fuentes import fuente, fuente_de_tamano
from juego import sprites_objetos, decoracion
from screens.flechas import flecha_alrededor, cerca_del_borde, dibujar_camino


COLOR_SOMBRA = (12, 11, 23)
COLOR_PUERTA = (150, 60, 70)
COLOR_NOTA = (240, 226, 170)
COLOR_CONSOLA = (180, 110, 255)
COLOR_LISTO = (96, 210, 120)
COLOR_CAPSULA = (90, 220, 230)
# El kit era naranja como las piezas y se confundían: ahora es verde.
COLOR_CONSUMIBLE = {"decodificador": (90, 160, 255), "kit": (110, 210, 140),
                    "fruta": (232, 84, 60), "abono": (176, 128, 80)}


def _texto(screen, texto, centro_x, y, color):
    f = fuente("small")
    img = f.render(texto, True, color)
    sombra = f.render(texto, True, COLOR_SOMBRA)
    pos = (int(centro_x - img.get_width() // 2), int(y))
    screen.blit(sombra, (pos[0] + 2, pos[1] + 2))
    screen.blit(img, pos)


def _en_pantalla(rect, offset):
    return rect.move(-offset[0], -offset[1])


def _barra(screen, x, y, ancho, valor, color):
    pygame.draw.rect(screen, (30, 32, 48), (x, y, ancho, 8))
    pygame.draw.rect(screen, color, (x, y, int(ancho * max(0, min(1, valor))), 8))
    pygame.draw.rect(screen, (200, 205, 225), (x, y, ancho, 8), 1)


COLOR_FLECHA = (255, 214, 64)
ALTO_CONSOLA = sprites_objetos.ALTOS["consola"]


def dibujar_flecha_objetivo(screen, vista, camara, dueño, mision, dificultad, red, tiempo_ms):
    """Dificultades fáciles (dificultad.py): una flecha amarilla hacia lo que
    toca hacer (Mision.punto_objetivo). Si ya va a verificar un rumor en NEXUS,
    manda esa flecha (la azul) y esta no sale."""
    if mision is None or dificultad is None or not dificultad.flecha:
        return
    if red is not None and red.investigando.get(dueño) is not None:
        return
    objetivo = mision.punto_objetivo(dueño)
    if objetivo is None:
        return
    (x, y), texto = objetivo
    dibujar_camino(screen, vista, camara, dueño, (x, y), COLOR_FLECHA, tiempo_ms)
    f = fuente_de_tamano(14)
    if camara.collidepoint(x, y):
        centro = (int(x - camara.x + vista.x), int(y - camara.y + vista.y))
        radio = 34 + int(5 * math.sin(tiempo_ms / 180))
        pygame.draw.circle(screen, COLOR_FLECHA, centro, radio, 2)
        img = f.render(texto, True, COLOR_FLECHA)
        fondo = pygame.Surface((img.get_width() + 10, img.get_height() + 4), pygame.SRCALPHA)
        fondo.fill((14, 15, 28, 180))
        r = fondo.get_rect(midbottom=(centro[0], centro[1] - radio - 4))
        r.clamp_ip(vista.inflate(-8, -8))
        screen.blit(fondo, r)
        screen.blit(img, img.get_rect(center=r.center))
        if not cerca_del_borde(vista, centro):
            return
    # Fuera de pantalla (o en el borde, donde lo tapa el HUD): una flecha
    # alrededor del jugador (screens/flechas.py).
    # Si el objetivo ya está en pantalla (en el borde), su letrero ya salió
    # encima del aro: la flecha va sin texto para no repetirlo.
    flecha_alrededor(screen, vista, camara, dueño, (x, y), COLOR_FLECHA,
                     None if camara.collidepoint(x, y) else texto, tiempo_ms)


def dibujar_piso(screen, offset, camara, dueño, mision, tiempo_ms):
    if mision is None or not mision.activa:
        return
    brillo = 0.6 + 0.4 * math.sin(tiempo_ms / 280)

    varias = len(getattr(mision, "puertas", ())) > 1
    for puerta in getattr(mision, "puertas", ()):
        if puerta["abierta"] or not puerta["rect"].colliderect(camara):
            continue
        r = _en_pantalla(puerta["rect"], offset)
        color = puerta["color"] if varias else COLOR_PUERTA
        pygame.draw.rect(screen, (60, 62, 78), r)
        for i in range(r.top + 6, r.bottom, 14):
            pygame.draw.line(screen, color, (r.left, i), (r.right, i), 4)
        pygame.draw.rect(screen, color, r, 3)
        # La luz del teclado, del color de la puerta (el de las tachuelas de sus notas).
        luz = puerta["color"]
        pygame.draw.circle(screen, luz if brillo > 0.8 else tuple(c // 2 for c in luz),
                           (r.centerx, r.top - 10), 6)

    if mision.capsula is not None and mision.capsula.inflate(120, 160).colliderect(camara):
        r = _en_pantalla(mision.capsula, offset)
        capa = pygame.Surface(r.size, pygame.SRCALPHA)
        alfa = int(60 + 60 * brillo) if mision.fase == "huida" else 40
        capa.fill((*COLOR_CAPSULA, alfa))
        screen.blit(capa, r.topleft)
        nave = imagen_nave(etapa_nave(mision))
        if nave is not None:
            # La nave de Anny encima del piso de la cápsula: rota, en partes o
            # completa según la barra de reparación.
            pos = nave.get_rect(midtop=(r.centerx, r.bottom + PIE_NAVE - BASE_NAVE * ESCALA_NAVE))
            screen.blit(nave, pos)
            pygame.draw.rect(screen, COLOR_CAPSULA, r, 2, border_radius=10)
            arriba = min(r.top, pos.top + nave.get_bounding_rect().top)
        else:
            pygame.draw.rect(screen, COLOR_CAPSULA, r, 3, border_radius=10)
            arriba = r.top
        _texto(screen, "Cápsula de escape", r.centerx, arriba - 40, COLOR_CAPSULA)
        if mision.fase in ("capsula", "huida"):
            from misiones.mision import PIEZAS_NECESARIAS
            estado = (f"Piezas {mision.piezas_entregadas}/{PIEZAS_NECESARIAS}"
                      if mision.piezas_entregadas < PIEZAS_NECESARIAS else "Reparación")
            _texto(screen, estado, r.centerx, arriba - 20, (230, 235, 250))
            if mision.piezas_entregadas >= PIEZAS_NECESARIAS:
                _barra(screen, r.x + 10, r.bottom + 6, r.width - 20, mision.reparacion, COLOR_LISTO)

    for nota in mision.notas:
        if not nota["rect"].colliderect(camara):
            continue
        r = _en_pantalla(nota["rect"], offset)
        nueva = dueño not in nota["leida_por"]
        if nueva:
            halo = pygame.Surface((r.width + 24, r.height + 24), pygame.SRCALPHA)
            pygame.draw.ellipse(halo, (*COLOR_NOTA, int(70 * brillo)), halo.get_rect())
            screen.blit(halo, (r.x - 12, r.y - 12))
        pygame.draw.rect(screen, COLOR_NOTA if nueva else (150, 145, 120), r.inflate(-6, 0))
        for i in range(3):
            y = r.y + 7 + i * 7
            pygame.draw.line(screen, (120, 110, 80), (r.x + 7, y), (r.right - 7, y), 1)
        if nota.get("de_codigo"):
            # Las de código (vienen con una puerta): tachuela del color de su puerta.
            color = nota.get("color", (220, 60, 60))
            pygame.draw.circle(screen, (30, 24, 24), (r.centerx, r.y + 3), 5)
            pygame.draw.circle(screen, color if nueva else tuple(c * 2 // 3 for c in color),
                               (r.centerx, r.y + 2), 4)
            pygame.draw.rect(screen, color, (r.x + 7, r.bottom - 8, r.width - 14, 3))

    for cons in mision.consumibles:
        if cons["tomado"] or not cons["rect"].colliderect(camara):
            continue
        r = _en_pantalla(cons["rect"], offset)
        color = COLOR_CONSUMIBLE[cons["tipo"]]
        if cons["tipo"] in ("fruta", "abono", "kit", "decodificador"):
            # Su dibujito (el mismo del inventario), con un halo que late.
            from screens.paneles import _icono_objeto
            brillo = 0.6 + 0.4 * math.sin(tiempo_ms / 260)
            halo = pygame.Surface((r.width + 20, r.height + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(halo, (*color, int(80 * brillo)), halo.get_rect())
            screen.blit(halo, (r.x - 10, r.y - 10))
            _icono_objeto(screen, cons["tipo"], r.center, r.width + 6)
            continue
        pygame.draw.rect(screen, (30, 30, 40), r, border_radius=5)
        pygame.draw.rect(screen, color, r.inflate(-10, -10), border_radius=3)
        pygame.draw.rect(screen, color, r, 2, border_radius=5)



# -- La nave de la cápsula (de Anny) ------------------------------------------------
# Tres dibujos de 64x64: rota, en partes y completa. Cambia con cada tercio de
# la barra de reparación (la que se llena después de entregar las piezas): de
# 0 a 1/3 rota, de 1/3 a 2/3 en partes, de 2/3 en adelante (y en la huida)
# completa. Si el Cambiaformas la sabotea y la barra baja, vuelve atrás.
ARCHIVOS_NAVE = ("nave_rota.png", "nave_en_partes.png", "nave_completa.png")
ESCALA_NAVE = 3          # como el mapa (ESCALA_MAPA): cada pixel del dibujo = 3 px
PIE_NAVE = 8             # cuánto baja el dibujo del borde de abajo de la cápsula
BASE_NAVE = 56           # fila (del dibujo de 64) donde apoya el casco: la misma en las tres
_naves = {}


def etapa_nave(mision):
    """0 (rota), 1 (en partes) o 2 (completa)."""
    if mision.fase == "huida" or mision.reparacion >= 2 / 3:
        return 2
    if mision.reparacion >= 1 / 3:
        return 1
    return 0


def imagen_nave(etapa):
    """El dibujo de esa etapa agrandado (entero: todas quedan alineadas), o None."""
    if etapa not in _naves:
        img = None
        try:
            original = pygame.image.load(os.path.join(sprites_objetos.CARPETA, ARCHIVOS_NAVE[etapa]))
            try:
                original = original.convert_alpha()
            except pygame.error:
                pass
            img = pygame.transform.scale(original, (original.get_width() * ESCALA_NAVE,
                                                    original.get_height() * ESCALA_NAVE))
        except (pygame.error, OSError, FileNotFoundError, IndexError):
            img = None
        _naves[etapa] = img
    return _naves[etapa]


def erguidos(mision, camara, tiempo_ms):
    """Las consolas de navegación como cosas paradas en el piso
    (decoracion.Erguido): se dibujan ordenadas con los personajes, así quien
    pasa por detrás queda tapado (screens/partida.py)."""
    if mision is None or not mision.activa:
        return []
    brillo = 0.6 + 0.4 * math.sin(tiempo_ms / 280)
    lista = []
    for consola in mision.consolas:
        img = sprites_objetos.sprite("consola", ALTO_CONSOLA)
        caja = sprites_objetos.caja_dibujo("consola", consola["base"], img)
        if not caja.inflate(20, 40).colliderect(camara):
            continue
        lista.append(decoracion.Erguido(
            consola["solido"], caja,
            lambda screen, offset, c=consola: _dibujar_consola(screen, offset, c, mision, brillo)))
    return lista


def _dibujar_consola(screen, offset, consola, mision, brillo):
    r = _en_pantalla(consola["base"], offset)
    lista = consola["progreso"] >= 1
    color = COLOR_LISTO if lista else COLOR_CONSOLA
    img = None
    if lista:
        # Apagada: su dibujo con las pantallas apagadas (si no está, la
        # prendida en gris).
        img = sprites_objetos.sprite("consola_apagada", ALTO_CONSOLA)
    if img is None:
        img = sprites_objetos.sprite("consola", ALTO_CONSOLA, apagado=lista)
    if img is not None:
        # La consola de Anny: prendida hasta que la apagan (queda apagada,
        # con una palomita verde encima).
        pos = sprites_objetos.caja_dibujo("consola", consola["base"], img).move(-offset[0], -offset[1])
        screen.blit(img, pos)
        if lista:
            c = (pos.centerx, pos.y - 12)
            pygame.draw.circle(screen, (20, 40, 28), c, 11)
            pygame.draw.lines(screen, COLOR_LISTO, False,
                              [(c[0] - 6, c[1]), (c[0] - 2, c[1] + 4), (c[0] + 6, c[1] - 5)], 3)
        elif mision.fase == "sabotaje":
            sprites_objetos.resaltar(screen, img, pos.topleft,
                                     tuple(int(v * brillo) for v in COLOR_CONSOLA), 2)
    else:
        pygame.draw.rect(screen, (34, 30, 52), r, border_radius=6)
        pygame.draw.rect(screen, tuple(int(c * (1 if lista else brillo)) for c in color),
                         r.inflate(-14, -14), border_radius=4)
        pygame.draw.rect(screen, color, r, 2, border_radius=6)
    if mision.fase == "sabotaje" and not lista:
        _barra(screen, r.x, r.bottom + 4, r.width, consola["progreso"], COLOR_CONSOLA)

def dibujar_encima(screen, offset, camara, mision, tiempo_ms):
    """Barrotes delante de quien está encerrado, y su pedido de ayuda."""
    if mision is None or not mision.activa:
        return
    for celda in mision.celdas:
        preso = celda["preso"]
        if preso is None:
            continue
        hb = preso.personaje.hitbox
        x = hb.centerx - offset[0]
        arriba = int(preso.personaje.y) - offset[1]
        abajo = hb.bottom - offset[1]
        for i in range(-30, 31, 12):
            pygame.draw.line(screen, (150, 155, 170), (x + i, arriba), (x + i, abajo), 3)
        if (tiempo_ms // 500) % 2 == 0:
            _texto(screen, "¡Ayuda!", x, arriba - 24, (255, 120, 120))


def render_progreso(screen, vista, jugador):
    """Barra de lo que está haciendo con la tecla mantenida."""
    progreso = getattr(jugador, "progreso", None)
    if not progreso:
        return
    texto, valor = progreso
    ancho = min(320, vista.width - 80)
    x = vista.centerx - ancho // 2
    from screens.paneles import tope_abajo
    y = min(vista.bottom - 150, tope_abajo(vista, jugador) - 66)   # encima de la pista
    fondo = pygame.Surface((ancho + 20, 46), pygame.SRCALPHA)
    fondo.fill((14, 15, 28, 220))
    screen.blit(fondo, (x - 10, y - 26))
    _texto(screen, texto, vista.centerx, y - 22, (240, 242, 252))
    pygame.draw.rect(screen, (40, 42, 64), (x, y, ancho, 12))
    pygame.draw.rect(screen, COLOR_LISTO, (x, y, int(ancho * valor), 12))
    pygame.draw.rect(screen, (120, 132, 190), (x, y, ancho, 12), 1)
