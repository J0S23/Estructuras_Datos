"""Dibujo de lo de la misión (mision.py): puerta, notas, consolas, cápsula,
consumibles y los barrotes de quien está encerrado.

Figuras provisionales hasta que llegue el arte: cuando haya sprites, se cambian
aquí sin tocar la lógica.
"""

import math

import pygame

from fuentes import fuente


COLOR_SOMBRA = (12, 11, 23)
COLOR_PUERTA = (150, 60, 70)
COLOR_NOTA = (240, 226, 170)
COLOR_CONSOLA = (180, 110, 255)
COLOR_LISTO = (96, 210, 120)
COLOR_CAPSULA = (90, 220, 230)
COLOR_CONSUMIBLE = {"decodificador": (90, 160, 255), "kit": (255, 170, 50)}


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


def dibujar_piso(screen, offset, camara, dueño, mision, tiempo_ms):
    if mision is None or not mision.activa:
        return
    brillo = 0.6 + 0.4 * math.sin(tiempo_ms / 280)

    if mision.puerta is not None and not mision.puerta_abierta and mision.puerta.colliderect(camara):
        r = _en_pantalla(mision.puerta, offset)
        pygame.draw.rect(screen, (60, 62, 78), r)
        for i in range(r.top + 6, r.bottom, 14):
            pygame.draw.line(screen, COLOR_PUERTA, (r.left, i), (r.right, i), 4)
        pygame.draw.rect(screen, COLOR_PUERTA, r, 3)
        pygame.draw.circle(screen, (255, 80, 80) if brillo > 0.8 else (140, 40, 40),
                           (r.centerx, r.top - 10), 6)

    if mision.capsula is not None and mision.capsula.colliderect(camara):
        r = _en_pantalla(mision.capsula, offset)
        capa = pygame.Surface(r.size, pygame.SRCALPHA)
        alfa = int(60 + 60 * brillo) if mision.fase == "huida" else 40
        capa.fill((*COLOR_CAPSULA, alfa))
        screen.blit(capa, r.topleft)
        pygame.draw.rect(screen, COLOR_CAPSULA, r, 3, border_radius=10)
        _texto(screen, "Cápsula de escape", r.centerx, r.top - 40, COLOR_CAPSULA)
        if mision.fase in ("capsula", "huida"):
            from mision import PIEZAS_NECESARIAS
            estado = (f"Piezas {mision.piezas_entregadas}/{PIEZAS_NECESARIAS}"
                      if mision.piezas_entregadas < PIEZAS_NECESARIAS else "Reparación")
            _texto(screen, estado, r.centerx, r.top - 20, (230, 235, 250))
            if mision.piezas_entregadas >= PIEZAS_NECESARIAS:
                _barra(screen, r.x + 10, r.bottom + 6, r.width - 20, mision.reparacion, COLOR_LISTO)

    for consola in mision.consolas:
        if not consola["rect"].colliderect(camara):
            continue
        r = _en_pantalla(consola["rect"], offset)
        lista = consola["progreso"] >= 1
        color = COLOR_LISTO if lista else COLOR_CONSOLA
        pygame.draw.rect(screen, (34, 30, 52), r, border_radius=6)
        pygame.draw.rect(screen, tuple(int(c * (1 if lista else brillo)) for c in color),
                         r.inflate(-14, -14), border_radius=4)
        pygame.draw.rect(screen, color, r, 2, border_radius=6)
        if mision.fase == "sabotaje" and not lista:
            _barra(screen, r.x, r.bottom + 4, r.width, consola["progreso"], COLOR_CONSOLA)

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

    for cons in mision.consumibles:
        if cons["tomado"] or not cons["rect"].colliderect(camara):
            continue
        r = _en_pantalla(cons["rect"], offset)
        color = COLOR_CONSUMIBLE[cons["tipo"]]
        pygame.draw.rect(screen, (30, 30, 40), r, border_radius=5)
        pygame.draw.rect(screen, color, r.inflate(-10, -10), border_radius=3)
        pygame.draw.rect(screen, color, r, 2, border_radius=5)


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
    y = vista.bottom - 150
    fondo = pygame.Surface((ancho + 20, 46), pygame.SRCALPHA)
    fondo.fill((14, 15, 28, 220))
    screen.blit(fondo, (x - 10, y - 26))
    _texto(screen, texto, vista.centerx, y - 22, (240, 242, 252))
    pygame.draw.rect(screen, (40, 42, 64), (x, y, ancho, 12))
    pygame.draw.rect(screen, COLOR_LISTO, (x, y, int(ancho * valor), 12))
    pygame.draw.rect(screen, (120, 132, 190), (x, y, ancho, 12), 1)
