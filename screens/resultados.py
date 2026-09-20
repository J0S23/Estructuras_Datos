"""Pantalla de resultados al terminar la ronda.

Muestra cómo le fue a cada jugador y cómo quedó Ciudad Nova. Los puntos son
de cada rol (cada uno persigue su propio objetivo), pero los indicadores son
compartidos: es una sola ciudad y las decisiones de todos la movieron.
"""

import pygame

from config import (INDICADORES_CIUDAD_INICIALES, INDICADORES_INVERSOS,
                    INDICADOR_LABELS)
from fuentes import fuente_de_tamano


COLOR_FONDO = (26, 28, 48)
COLOR_TITULO = (255, 214, 64)
COLOR_TEXTO = (245, 246, 252)
COLOR_TENUE = (170, 178, 214)
COLOR_BARRA = (96, 188, 118)
COLOR_BARRA_MALA = (214, 74, 68)


def render_resultados(screen, jugadores, state, font=None, small_font=None):
    screen.fill(COLOR_FONDO)
    ancho, alto = screen.get_size()
    f = fuente_de_tamano(max(14, min(22, ancho // 62)))
    titulo_f = font or fuente_de_tamano(30)
    paso = f.get_linesize() + 6

    encabezado = titulo_f.render("SE ACABÓ LA RONDA", True, COLOR_TEXTO)
    screen.blit(encabezado, encabezado.get_rect(center=(ancho // 2, 56)))

    columna = ancho // 2

    # -- Jugadores --------------------------------------------------------------
    y = 130
    screen.blit(f.render("Cómo le fue a cada uno", True, COLOR_TITULO), (60, y))
    y += paso + 6

    ordenados = sorted(jugadores, key=lambda j: j.puntos, reverse=True)
    for puesto, jugador in enumerate(ordenados, start=1):
        linea = f"{puesto}.  {jugador.rol}  —  {jugador.puntos} pts"
        screen.blit(f.render(linea, True, COLOR_TEXTO), (80, y))
        y += paso

        detalle = f"tareas hechas: {jugador.tareas_hechas}"
        screen.blit(f.render(detalle, True, COLOR_TENUE), (110, y))
        y += paso

        camino = [n.nombre for n in jugador.arbol.desbloqueadas()] if not jugador.arbol.vacio else []
        if camino:
            screen.blit(f.render("rama: " + " > ".join(camino), True, COLOR_TENUE), (110, y))
        else:
            screen.blit(f.render("sin árbol de habilidades definido", True, COLOR_TENUE), (110, y))
        y += paso + 14

    # -- Ciudad -----------------------------------------------------------------
    y = 130
    screen.blit(f.render("Cómo quedó Ciudad Nova", True, COLOR_TITULO), (columna + 40, y))
    y += paso + 6

    for clave in INDICADORES_CIUDAD_INICIALES:
        valor = state.indicadores.get(clave, 0)
        inicial = INDICADORES_CIUDAD_INICIALES[clave]
        delta = valor - inicial
        nombre = INDICADOR_LABELS.get(clave, clave)

        etiqueta = f"{nombre}: {valor}"
        if delta:
            etiqueta += f"  ({'+' if delta > 0 else ''}{delta})"
        screen.blit(f.render(etiqueta, True, COLOR_TEXTO), (columna + 60, y))

        bueno = (delta <= 0) if clave in INDICADORES_INVERSOS else (delta >= 0)
        barra = pygame.Rect(columna + 60, y + f.get_linesize() + 2, 300, 12)
        pygame.draw.rect(screen, (20, 22, 34), barra)
        relleno = int((barra.width - 4) * max(0, min(100, valor)) / 100)
        pygame.draw.rect(screen, COLOR_BARRA if bueno else COLOR_BARRA_MALA,
                         (barra.x + 2, barra.y + 2, relleno, barra.height - 4))
        y += paso + 18

    pie = f.render("[ENTER] volver al menú", True, (194, 216, 248))
    screen.blit(pie, pie.get_rect(center=(ancho // 2, alto - 40)))
