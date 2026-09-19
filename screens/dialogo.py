"""Pantalla de conversación con un NPC, manejada por un árbol de diálogo.

Muestra lo que dice el NPC y, debajo, las respuestas posibles (los hijos del
nodo actual del árbol). Cuando el nodo no tiene hijos, la conversación
terminó.
"""

import pygame


TECLAS_RESPUESTA = ["1", "2", "3", "4"]

COLOR_FONDO = (34, 30, 52)
COLOR_PANEL = (46, 41, 70)
COLOR_BORDE = (96, 86, 140)
COLOR_NOMBRE = (240, 220, 140)
COLOR_TEXTO = (255, 255, 255)
COLOR_RESPUESTA = (200, 226, 255)
COLOR_AVISO = (194, 216, 248)


def render_dialogo(screen, font=None, nombre_npc="", nodo_actual=None, small_font=None):
    if font is None:
        font = pygame.font.SysFont("arial", 28)
    if small_font is None:
        small_font = font

    screen.fill(COLOR_FONDO)

    if nodo_actual is None:
        screen.blit(small_font.render("No hay nadie con quien hablar.", True, COLOR_TEXTO), (40, 40))
        return

    ancho = screen.get_width()

    # Panel con lo que dice el NPC
    panel = pygame.Rect(40, 40, ancho - 80, 190)
    pygame.draw.rect(screen, COLOR_PANEL, panel)
    pygame.draw.rect(screen, COLOR_BORDE, panel, 3)

    screen.blit(small_font.render(nombre_npc, True, COLOR_NOMBRE), (panel.x + 18, panel.y + 14))
    _texto_ajustado(screen, small_font, nodo_actual.texto,
                    (panel.x + 18, panel.y + 52), panel.width - 36, COLOR_TEXTO)

    # Respuestas posibles = hijos del nodo actual
    y = panel.bottom + 34
    if nodo_actual.hijos:
        screen.blit(small_font.render("¿Qué respondes?", True, COLOR_NOMBRE), (48, y))
        y += 34
        for idx, hijo in enumerate(nodo_actual.hijos[:len(TECLAS_RESPUESTA)]):
            etiqueta = f"[{TECLAS_RESPUESTA[idx]}] {hijo.respuesta}"
            y += _texto_ajustado(screen, small_font, etiqueta, (64, y), ancho - 130, COLOR_RESPUESTA) + 8
    else:
        aviso = small_font.render("La conversación terminó.", True, COLOR_NOMBRE)
        screen.blit(aviso, (48, y))
        volver = small_font.render("[ENTER] Volver a la ciudad", True, COLOR_AVISO)
        screen.blit(volver, volver.get_rect(center=(ancho // 2, screen.get_height() - 30)))


def _texto_ajustado(screen, font, texto, pos, ancho_max, color):
    """Dibuja el texto partido en varias líneas. Devuelve el alto que ocupó."""
    palabras = str(texto).split(" ")
    lineas = []
    actual = ""
    for palabra in palabras:
        prueba = (actual + " " + palabra).strip()
        if font.size(prueba)[0] > ancho_max and actual:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)

    x, y = pos
    alto_linea = font.get_height() + 5
    for linea in lineas:
        screen.blit(font.render(linea, True, color), (x, y))
        y += alto_linea
    return len(lineas) * alto_linea
