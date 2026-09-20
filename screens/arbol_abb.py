"""Panel que dibuja el ABB de publicaciones tal como está en memoria.

Es la pantalla que hace visible la estructura: se abre con [TAB] durante la
partida y muestra el árbol real, no un dibujo de adorno. Cada vez que alguien
atiende o reporta una publicación el nodo desaparece y el dibujo cambia.

Cómo se calculan las posiciones: el recorrido inorden de un ABB entrega los
nodos de izquierda a derecha en el orden en que deben aparecer en pantalla. Así
que se numera cada nodo con su índice inorden (eso da la columna) y con su
profundidad (eso da la fila). Es el método clásico y garantiza que ningún nodo
se dibuje encima de otro.
"""

import pygame

from fuentes import fuente
from ui_components import dibujar_texto_ajustado


COLOR_FONDO = (26, 28, 48)
COLOR_LINEA = (108, 118, 170)
COLOR_TEXTO = (255, 255, 255)
COLOR_TEXTO_TENUE = (176, 184, 220)
COLOR_TITULO = (240, 220, 140)
COLOR_BORDE_NODO = (18, 19, 32)
COLOR_SIGUIENTE = (255, 214, 64)

# Los nodos se colorean por veracidad: rojo lo más dudoso, verde lo más confiable.
COLOR_DUDOSA = (214, 74, 68)
COLOR_MEDIA = (222, 160, 62)
COLOR_CONFIABLE = (96, 188, 118)

RADIO_NODO = 22
UMBRAL_DUDOSA = 40

# Separación máxima entre columnas: sin esto, con pocos nodos el árbol se
# estira de lado a lado de la pantalla y se ve deshilachado.
SEPARACION_MAXIMA = 130


def color_por_veracidad(veracidad):
    if veracidad < UMBRAL_DUDOSA:
        return COLOR_DUDOSA
    if veracidad < 60:
        return COLOR_MEDIA
    return COLOR_CONFIABLE


def calcular_posiciones(raiz):
    """Asigna a cada nodo una columna (su índice inorden) y una fila (su profundidad).

    Devuelve la lista de tuplas (nodo, columna, fila) y cuántas columnas y filas
    hizo falta en total, para poder escalar el dibujo al tamaño de la ventana.
    """
    colocados = []
    contador = [0]  # lista para poder mutarlo desde la función anidada

    def _recorrer(nodo, profundidad):
        if nodo is None:
            return
        _recorrer(nodo.izquierdo, profundidad + 1)
        colocados.append((nodo, contador[0], profundidad))
        contador[0] += 1
        _recorrer(nodo.derecho, profundidad + 1)

    _recorrer(raiz, 0)
    columnas = contador[0]
    filas = max((fila for _, _, fila in colocados), default=0) + 1
    return colocados, columnas, filas


def altura_minima_posible(n):
    """Niveles que tendría un ABB perfectamente balanceado de n nodos."""
    niveles = 0
    while (1 << niveles) - 1 < n:
        niveles += 1
    return niveles


def render_arbol_abb(screen, arbol, font=None, small_font=None):
    if font is None:
        font = fuente("subtitle")
    if small_font is None:
        small_font = fuente("small")

    screen.fill(COLOR_FONDO)
    ancho, alto = screen.get_size()

    screen.blit(font.render("ABB DE PUBLICACIONES", True, COLOR_TEXTO), (40, 28))

    subtitulo = ("Ordenadas por veracidad. Izquierda = menos veraz. "
                 "La próxima que sale es la de más a la izquierda.")
    dibujar_texto_ajustado(screen, subtitulo, small_font, 40, 78, ancho - 80, COLOR_TEXTO_TENUE)

    inorden = arbol.recorrido_inorden()
    total = arbol.contar()

    if total == 0:
        vacio = "El árbol quedó vacío: ya atendiste todas las publicaciones."
        etiqueta = small_font.render(vacio, True, COLOR_TEXTO)
        screen.blit(etiqueta, etiqueta.get_rect(center=(ancho // 2, alto // 2)))
        _dibujar_pie(screen, small_font)
        return

    ficha = (f"Nodos: {total}    Altura: {arbol.altura()}    "
             f"Altura mínima posible con {total} nodos: {altura_minima_posible(total)}    "
             f"Raíz: {arbol.raiz.veracidad}")
    dibujar_texto_ajustado(screen, ficha, small_font, 40, 108, ancho - 80, COLOR_TITULO)

    # -- El árbol -------------------------------------------------------------
    colocados, columnas, filas = calcular_posiciones(arbol.raiz)

    margen_x = 70
    tope_y = 170
    base_y = max(tope_y + 60, alto - 210)
    ancho_util = max(1, ancho - margen_x * 2)
    alto_util = max(1, base_y - tope_y)

    paso_x = min(SEPARACION_MAXIMA, ancho_util / (columnas - 1)) if columnas > 1 else 0
    paso_y = min(110, alto_util / (filas - 1)) if filas > 1 else 0

    # El árbol se centra en el espacio disponible en vez de ocuparlo todo.
    izquierda = (ancho - paso_x * (columnas - 1)) / 2
    arriba = tope_y + max(0, (alto_util - paso_y * (filas - 1)) / 2)

    centros = {}
    for nodo, columna, fila in colocados:
        centros[id(nodo)] = (int(izquierda + columna * paso_x), int(arriba + fila * paso_y))

    # Primero las aristas, para que queden por debajo de los nodos.
    for nodo, _, _ in colocados:
        for hijo in (nodo.izquierdo, nodo.derecho):
            if hijo is not None and id(hijo) in centros:
                pygame.draw.line(screen, COLOR_LINEA, centros[id(nodo)], centros[id(hijo)], 3)

    siguiente = inorden[0]["veracidad"]
    for nodo, _, _ in colocados:
        centro = centros[id(nodo)]
        if nodo.veracidad == siguiente:
            pygame.draw.circle(screen, COLOR_SIGUIENTE, centro, RADIO_NODO + 6, 4)
        pygame.draw.circle(screen, color_por_veracidad(nodo.veracidad), centro, RADIO_NODO)
        pygame.draw.circle(screen, COLOR_BORDE_NODO, centro, RADIO_NODO, 3)
        numero = small_font.render(str(nodo.veracidad), True, (16, 16, 24))
        screen.blit(numero, numero.get_rect(center=centro))

    # -- El recorrido inorden como tira de números ----------------------------
    y_recorrido = base_y + 42
    screen.blit(small_font.render("Recorrido inorden (izquierdo - nodo - derecho):",
                                 True, COLOR_TITULO), (40, y_recorrido))
    y_recorrido += 28
    x = 60
    for i, item in enumerate(inorden):
        etiqueta = small_font.render(str(item["veracidad"]), True,
                                    COLOR_SIGUIENTE if i == 0 else COLOR_TEXTO)
        if x + etiqueta.get_width() > ancho - 70:
            screen.blit(small_font.render("...", True, COLOR_TEXTO_TENUE), (x, y_recorrido))
            break
        screen.blit(etiqueta, (x, y_recorrido))
        x += etiqueta.get_width()
        if i < len(inorden) - 1:
            flecha = small_font.render("  >  ", True, COLOR_TEXTO_TENUE)
            screen.blit(flecha, (x, y_recorrido))
            x += flecha.get_width()

    titulo = inorden[0]["titulo"]
    if len(titulo) > 76:
        titulo = titulo[:73] + "..."
    linea = f"Próxima ({inorden[0]['veracidad']} de veracidad): {titulo}"
    dibujar_texto_ajustado(screen, linea, small_font, 40, y_recorrido + 34,
                    ancho - 80, COLOR_TEXTO_TENUE)

    _dibujar_pie(screen, small_font)


def _dibujar_pie(screen, small_font):
    pie = small_font.render("[TAB] o [ENTER] volver a la partida",
                           True, (194, 216, 248))
    screen.blit(pie, pie.get_rect(center=(screen.get_width() // 2, screen.get_height() - 24)))

