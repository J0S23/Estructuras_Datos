"""Dibujo del menú de admin (F1; la lógica está en juego/admin.py).

Un panel al centro encima de la partida congelada: la lista de cosas que se
pueden lanzar, la del cursor resaltada y, a la derecha de algunas, cómo
están ahora (a oscuras, modo invencible sí/no...).
"""

import pygame

from juego.admin import OPCIONES
from juego.fuentes import fuente, fuente_de_tamano
from screens.paneles import COLOR_TITULO, COLOR_TENUE

COLOR_VELO = (6, 6, 14, 150)
COLOR_FONDO = (16, 14, 30)
COLOR_BORDE = (236, 92, 92)          # rojo: no es parte del juego
COLOR_CURSOR = (58, 40, 70)
COLOR_TEXTO = (232, 234, 246)
COLOR_ESTADO = (255, 214, 64)
PISTA = "Flechas o W/S + Enter (o clic)  ·  F1 o Esc: cerrar"


def render_admin(screen, admin):
    ancho, alto = screen.get_size()
    velo = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    velo.fill(COLOR_VELO)
    screen.blit(velo, (0, 0))

    alto_fila = 34 if alto >= 700 else 26
    letra = fuente_de_tamano(20 if alto >= 700 else 16)
    titulo = fuente("subtitle").render("Menú de admin", True, COLOR_TITULO)
    pista = fuente("small").render(PISTA, True, COLOR_TENUE)
    panel = pygame.Rect(0, 0, min(640, ancho - 32),
                        titulo.get_height() + pista.get_height() + 44 + alto_fila * len(OPCIONES))
    panel.center = (ancho // 2, alto // 2)
    pygame.draw.rect(screen, COLOR_FONDO, panel, border_radius=10)
    pygame.draw.rect(screen, COLOR_BORDE, panel, 3, border_radius=10)
    screen.blit(titulo, titulo.get_rect(midtop=(panel.centerx, panel.y + 12)))

    y = panel.y + 22 + titulo.get_height()
    mouse = pygame.mouse.get_pos()
    admin.rects = []
    for i, opcion in enumerate(OPCIONES):
        fila = pygame.Rect(panel.x + 12, y, panel.width - 24, alto_fila - 4)
        admin.rects.append(fila)
        if i == admin.cursor or fila.collidepoint(mouse):
            pygame.draw.rect(screen, COLOR_CURSOR, fila, border_radius=6)
        texto = letra.render(f"{i + 1:>2}. {opcion['texto']}", True, COLOR_TEXTO)
        screen.blit(texto, texto.get_rect(midleft=(fila.x + 10, fila.centery)))
        estado = admin.estado(i)
        if estado:
            img = letra.render(estado, True, COLOR_ESTADO)
            screen.blit(img, img.get_rect(midright=(fila.right - 10, fila.centery)))
        y += alto_fila
    screen.blit(pista, pista.get_rect(midbottom=(panel.centerx, panel.bottom - 10)))
