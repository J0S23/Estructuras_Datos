"""Pantalla de créditos: un rollo que sube y vuelve a empezar.

Antes el texto se dibujaba en `80 + scroll_y`, o sea que BAJABA, y el
desplazamiento se guardaba en `Game.credit_scroll`. Eso daba dos problemas:
entrar y salir varias veces retomaba donde se había quedado en vez de empezar
de nuevo, y una vez que las líneas se iban por abajo no volvían nunca.

Ahora sube (como cualquier rollo de créditos), arranca desde abajo del todo y
al terminar vuelve a empezar solo. `reiniciar_scroll()` da el valor inicial, y
App.py lo llama cada vez que se entra a la pantalla.
"""

import pygame

from fuentes import fuente_de_tamano


COLOR_FONDO = (15, 15, 25)
COLOR_TITULO = (255, 214, 64)
COLOR_TEXTO = (245, 246, 252)
COLOR_TENUE = (168, 176, 214)

VELOCIDAD = 0.6  # píxeles por frame

# (texto, estilo). "espacio" deja un hueco.
LINEAS = [
    ("ALCALDE DIGITAL", "titulo"),
    ("", "espacio"),
    ("Estructura de Datos II", "tenue"),
    ("Universidad del Norte", "tenue"),
    ("", "espacio"),
    ("", "espacio"),
    ("Equipo", "titulo"),
    ("Joseph Arias", "texto"),
    ("Diego Payares", "texto"),
    ("Anny Delgado", "texto"),
    ("Juan David Campo", "texto"),
    ("", "espacio"),
    ("", "espacio"),
    ("Hecho con Python y Pygame", "tenue"),
    ("Tipografía: Determination Mono", "tenue"),
    ("", "espacio"),
    ("", "espacio"),
    ("Gracias por jugar.", "titulo"),
]


def reiniciar_scroll():
    """Valor inicial del desplazamiento: el rollo empieza fuera de pantalla."""
    return 0.0


def render_creditos(screen, font=None, scroll=0.0, pausado=False):
    """Dibuja el rollo y devuelve el desplazamiento siguiente.

    El desplazamiento se mide en píxeles recorridos desde el inicio. Cuando el
    rollo entero ya pasó por arriba, vuelve a cero y empieza de nuevo.
    """
    screen.fill(COLOR_FONDO)
    ancho, alto = screen.get_size()

    f_titulo = fuente_de_tamano(max(18, min(34, ancho // 42)))
    f_texto = fuente_de_tamano(max(14, min(24, ancho // 60)))
    paso = f_texto.get_linesize() + 10

    alto_rollo = len(LINEAS) * paso
    # El rollo recorre su propio alto más una pantalla, para entrar desde abajo
    # y salir del todo por arriba antes de reiniciarse.
    recorrido = alto_rollo + alto

    y = alto - scroll
    for texto, estilo in LINEAS:
        if texto:
            f = f_titulo if estilo == "titulo" else f_texto
            color = COLOR_TITULO if estilo == "titulo" else (
                COLOR_TENUE if estilo == "tenue" else COLOR_TEXTO)
            etiqueta = f.render(texto, True, color)
            # Solo se dibuja lo que se ve, para no pedirle trabajo de más.
            if -etiqueta.get_height() < y < alto:
                screen.blit(etiqueta, etiqueta.get_rect(center=(ancho // 2, int(y))))
        y += paso

    pie = f_texto.render("[ENTER] volver", True, (194, 216, 248))
    screen.blit(pie, pie.get_rect(center=(ancho // 2, alto - 24)))

    if pausado:
        return scroll
    siguiente = scroll + VELOCIDAD
    return siguiente if siguiente < recorrido else 0.0
