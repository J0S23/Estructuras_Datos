"""Pantalla de publicación: aquí se ve en vivo el árbol de decisión (Estructuras/arbol_decision.py).

nodo_raiz es la publicación (NodoDecision raíz); nodo_actual es dónde está
parado el jugador dentro de ese árbol. Si nodo_actual es la raíz, se muestran
sus hijos como opciones (Verificar/Compartir/Ignorar/Reportar, según la
publicación). Si nodo_actual ya avanzó, se muestra el nodo de consecuencia.
"""

import pygame


OPCION_TECLAS = ["1", "2", "3", "4"]


def render_publicacion(screen, font=None, nodo_raiz=None, nodo_actual=None, small_font=None):
    if font is None:
        font = pygame.font.SysFont("arial", 30)
    if small_font is None:
        small_font = pygame.font.SysFont("arial", 20)

    screen.fill((90, 60, 80))

    if nodo_raiz is None:
        label = font.render("No hay publicación activa.", True, (255, 255, 255))
        screen.blit(label, (50, 50))
        aviso = small_font.render("Vuelve a la ciudad y presiona [E].", True, (220, 220, 220))
        screen.blit(aviso, (50, 100))
        return

    _dibujar_texto_ajustado(screen, font, nodo_raiz.texto, (40, 40), 880, (255, 255, 255))

    en_raiz = nodo_actual is nodo_raiz

    if en_raiz:
        y = 170
        titulo = small_font.render("¿Qué quieres hacer?", True, (240, 220, 140))
        screen.blit(titulo, (40, y))
        y += 40
        for idx, hijo in enumerate(nodo_actual.hijos):
            texto = f"[{OPCION_TECLAS[idx]}] {hijo.texto}"
            label = small_font.render(texto, True, (255, 255, 255))
            screen.blit(label, (60, y))
            y += 36
    else:
        titulo = small_font.render("Consecuencia:", True, (240, 220, 140))
        screen.blit(titulo, (40, 170))
        _dibujar_texto_ajustado(screen, small_font, nodo_actual.texto, (40, 210), 880, (255, 255, 255))
        aviso = small_font.render("[ENTER] Volver a la ciudad", True, (220, 220, 220))
        screen.blit(aviso, (40, 520))


def _dibujar_texto_ajustado(screen, font, texto, pos, ancho_max, color):
    """Parte el texto en varias líneas para que no se salga de la pantalla."""
    palabras = texto.split(" ")
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
    for linea in lineas:
        label = font.render(linea, True, color)
        screen.blit(label, (x, y))
        y += font.get_height() + 6
