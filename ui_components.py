"""Componentes de interfaz con el estilo pixel del juego.

Mismo estilo de botón que EmpatiaQuest: tarjeta clara con sombra dura y
borde grueso, que se ilumina cuando el mouse pasa encima o está seleccionado
con el teclado.
"""

import pygame

from config import CARD, CARD_HOVER, CARD_BORDER, TEXT_MAIN
from fuentes import fuente


COLOR_SOMBRA = (12, 11, 23)


class Button:
    """Botón interactivo con estilo pixel."""

    def __init__(self, rect, text, action):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action

    def draw(self, surface, hover=False):
        color = CARD_HOVER if hover else CARD
        pygame.draw.rect(surface, COLOR_SOMBRA, self.rect.move(4, 4))
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, CARD_BORDER, self.rect, width=4)

        etiqueta = fuente("button").render(self.text, True, TEXT_MAIN)
        surface.blit(etiqueta, etiqueta.get_rect(center=self.rect.center))

    def contains(self, pos):
        return self.rect.collidepoint(pos)


def construir_botones(labels, ancho_pantalla, alto_pantalla,
                      centro_y=None, ancho=None, alto=52, separacion=14):
    """Crea una columna de botones centrada horizontalmente.

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
        botones.append(Button((ancho_pantalla // 2 - ancho // 2, y, ancho, alto), texto, accion))
    return botones
