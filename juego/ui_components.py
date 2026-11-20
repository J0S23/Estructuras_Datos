"""Componentes de interfaz con el estilo pixel del juego.

Mismo estilo de botón que EmpatiaQuest: tarjeta clara con sombra dura y
borde grueso, que se ilumina cuando el mouse pasa encima o está seleccionado
con el teclado. Con los efectos prendidos (juego/efectos.py), vidrio oscuro
con borde de neón, que combina con el fondo del menú: el escogido brilla, le
cruza un reflejo y lleva dos marcas a los lados.
"""

import math

import pygame

from juego.config import CARD, CARD_HOVER, CARD_BORDER, TEXT_MAIN
from juego.fuentes import fuente, fuente_de_tamano


COLOR_SOMBRA = (12, 11, 23)


class Button:
    """Botón interactivo con estilo pixel."""

    def __init__(self, rect, text, action):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action

    def draw(self, surface, hover=False):
        from juego import efectos
        if efectos.ACTIVOS:
            # Vidrio oscuro con borde de neón; el escogido brilla (como el logo).
            _dibujar_vidrio(surface, self, hover, pygame.time.get_ticks())
            return
        color = CARD_HOVER if hover else CARD
        pygame.draw.rect(surface, COLOR_SOMBRA, self.rect.move(4, 4))
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, CARD_BORDER, self.rect, width=4)

        etiqueta = fuente("button").render(self.text, True, TEXT_MAIN)
        surface.blit(etiqueta, etiqueta.get_rect(center=self.rect.center))

    def contains(self, pos):
        return self.rect.collidepoint(pos)


def construir_botones(labels, ancho_pantalla, alto_pantalla,
                      centro_y=None, ancho=None, alto=52, separacion=14, centro_x=None):
    """Crea una columna de botones (centrada, o en `centro_x` si se da).

    `labels` es una lista de (texto, accion).
    """
    if ancho is None:
        ancho = min(460, int(ancho_pantalla * 0.34))
    if centro_y is None:
        centro_y = alto_pantalla // 2 + 40

    alto_total = len(labels) * alto + (len(labels) - 1) * separacion
    y_inicial = centro_y - alto_total // 2

    botones = []
    for i, (texto, accion) in enumerate(labels):
        y = y_inicial + i * (alto + separacion)
        cx = ancho_pantalla // 2 if centro_x is None else int(centro_x)
        botones.append(Button((cx - ancho // 2, y, ancho, alto), texto, accion))
    return botones


def dibujar_texto_ajustado(surface, texto, fuente_base, x, y, ancho_maximo, color):
    """Dibuja una línea encogiendo la letra si no cabe en el ancho disponible.

    Las pantallas del juego se dibujan tanto maximizadas como en la ventana
    chica de F11, y una línea larga que en pantalla completa cabe sobrada se
    sale del borde en la ventana pequeña. En vez de cortar el texto con puntos
    suspensivos, se busca el primer tamaño de letra en el que cabe entero.

    Devuelve la fuente que terminó usando, por si hay que seguir dibujando
    debajo con el mismo tamaño.
    """
    f = fuente_base
    if f.size(texto)[0] > ancho_maximo:
        for px in range(f.get_height(), 9, -1):
            candidata = fuente_de_tamano(px)
            if candidata.size(texto)[0] <= ancho_maximo:
                f = candidata
                break
        else:
            f = fuente_de_tamano(10)
    surface.blit(f.render(texto, True, color), (int(x), int(y)))
    return f


# -- Botones de vidrio (con los efectos prendidos) ---------------------------------------

COLOR_NEON = (90, 220, 255)
COLOR_NEON_2 = (233, 110, 255)
_vidrios = {}


def _vidrio(tamano, elegido):
    clave = (tamano, elegido)
    img = _vidrios.get(clave)
    if img is None:
        if len(_vidrios) > 40:
            _vidrios.clear()
        w, h = tamano
        img = pygame.Surface(tamano, pygame.SRCALPHA)
        arriba = (40, 30, 90, 235) if elegido else (16, 16, 38, 225)
        abajo = (24, 60, 110, 235) if elegido else (10, 10, 26, 225)
        for y in range(h):
            t = y / max(1, h - 1)
            pygame.draw.line(img, tuple(int(arriba[i] + (abajo[i] - arriba[i]) * t) for i in range(4)),
                             (0, y), (w, y))
        mascara = pygame.Surface(tamano, pygame.SRCALPHA)
        pygame.draw.rect(mascara, (255, 255, 255, 255), (0, 0, w, h), border_radius=10)
        img.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        brillo = pygame.Surface((w - 16, max(2, h // 4)), pygame.SRCALPHA)
        for y in range(brillo.get_height()):
            pygame.draw.line(brillo, (255, 255, 255, int(16 * (1 - y / brillo.get_height()))),
                             (0, y), (brillo.get_width(), y))
        img.blit(brillo, (8, 3))
        _vidrios[clave] = img
    return img


_reflejos = {}


def _reflejo(alto):
    """Una franja diagonal clara (para sumarla): el reflejo que cruza el botón."""
    img = _reflejos.get(alto)
    if img is None:
        ancho = alto
        img = pygame.Surface((ancho + alto // 2, alto))
        img.fill((0, 0, 0))
        for y in range(alto):
            corrida = (alto - y) // 2
            for x in range(ancho):
                v = math.sin(math.pi * x / (ancho - 1)) ** 2
                c = int(46 * v)
                img.set_at((x + corrida, y), (c, c, c + 8))
        _reflejos[alto] = img
    return img


_halos = {}


def _halo(tamano, color):
    clave = (tamano, color)
    img = _halos.get(clave)
    if img is None:
        w, h = tamano
        chico = pygame.Surface((max(4, w // 6), max(4, h // 6)))
        chico.fill((0, 0, 0))
        b = max(1, min(chico.get_width(), chico.get_height()) // 4)
        pygame.draw.rect(chico, color, chico.get_rect().inflate(-2 * b, -2 * b), border_radius=b)
        img = pygame.transform.smoothscale(chico, tamano)
        _halos[clave] = img
    return img


def _dibujar_vidrio(screen, boton, elegido, t):
    r = boton.rect
    if elegido:
        latido = 0.6 + 0.4 * math.sin(t / 260)
        nivel = round(latido * 4) / 4
        halo = _halo((r.w + 40, r.h + 40), tuple(int(c * 0.5 * nivel) for c in COLOR_NEON))
        screen.blit(halo, (r.x - 20, r.y - 20), special_flags=pygame.BLEND_RGB_ADD)
    screen.blit(_vidrio(r.size, elegido), r.topleft)
    borde = COLOR_NEON if elegido else (70, 90, 150)
    pygame.draw.rect(screen, borde, r, 2, border_radius=10)
    if elegido:
        # Un brillo que cruza el botón y dos marcas a los lados.
        periodo = 2600
        dentro = t % periodo
        if dentro < 1100:
            x = r.x - r.h + int((dentro / 1100) * (r.w + r.h * 2))
            recorte = screen.get_clip()
            screen.set_clip(r.inflate(-4, -4).clip(recorte))
            screen.blit(_reflejo(r.h), (x, r.y), special_flags=pygame.BLEND_RGB_ADD)
            screen.set_clip(recorte)
        for lado in (-1, 1):
            cx = r.centerx + lado * (r.w // 2 + 14)
            pygame.draw.polygon(screen, COLOR_NEON_2, [(cx, r.centery - 7), (cx - lado * 8, r.centery),
                                                       (cx, r.centery + 7)])
    texto = fuente("button").render(boton.text, True, (245, 248, 255) if elegido else (190, 200, 230))
    screen.blit(texto, texto.get_rect(center=r.center))
