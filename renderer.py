"""Renderer mínimo para la primera entrega."""

import pygame


def draw_text(surface, text, pos, font=None, color=(255, 255, 255), size=24):
    if font is None:
        font = pygame.font.SysFont("arial", size)
    label = font.render(str(text), True, color)
    surface.blit(label, pos)


def draw_panel(surface, rect, color=(40, 40, 60), border_color=(120, 120, 200), border=2):
    pygame.draw.rect(surface, border_color, rect, border)
    inner = pygame.Rect(rect.x + border, rect.y + border, rect.w - border * 2, rect.h - border * 2)
    pygame.draw.rect(surface, color, inner)
