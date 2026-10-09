"""Vista en vivo del árbol de comportamiento de un alien ([B] en partida).

Dibuja el árbol completo encima de la partida y resalta el camino que el
alien recorrió en este frame, de la raíz a la hoja. Como el alien vuelve a
decidir en cada frame, la rama resaltada cambia sola cuando el alien ve a un
jugador, oye un latido o pierde el rastro. Es la forma de mostrar en la
sustentación que el árbol no es decoración: es lo que mueve al alien.

Disposición: cada hoja ocupa una columna (en orden de izquierda a derecha) y
cada pregunta se centra sobre sus dos hijos. Así el árbol cabe a lo ancho
aunque las preguntas sean largas. Los niveles salen del recorrido por niveles
(BFS) del árbol.
"""

import pygame

from fuentes import fuente_de_tamano
from screens.paneles import partir_lineas


COLOR_FONDO = (14, 15, 28, 232)
COLOR_BORDE = (120, 132, 190)
COLOR_TITULO = (255, 214, 64)
COLOR_TEXTO = (240, 242, 252)
COLOR_TENUE = (130, 136, 170)
COLOR_PREGUNTA = (52, 57, 92)
COLOR_ACCION = (40, 70, 52)
COLOR_ACTIVO = (255, 214, 64)
COLOR_ARISTA = (90, 96, 130)


def _posiciones(arbol):
    """Columna (x relativa de 0 a 1) y nivel de cada nodo."""
    hojas = arbol.hojas()
    columna = {id(h): (i + 0.5) / len(hojas) for i, h in enumerate(hojas)}

    def x_de(nodo):
        if id(nodo) not in columna:
            hijos = nodo.hijos()
            columna[id(nodo)] = sum(x_de(h) for h in hijos) / len(hijos)
        return columna[id(nodo)]

    niveles = {}
    for nodo, nivel, _ in arbol.por_niveles():
        x_de(nodo)
        niveles[id(nodo)] = nivel
    return columna, niveles


def render_arbol_alien(screen, alien, arbol, numero=1, total=1):
    if alien is None or arbol is None or arbol.raiz is None:
        return
    ancho, alto = screen.get_size()
    panel = pygame.Rect(0, 0, min(ancho - 40, 1100), min(alto - 40, 560))
    panel.center = (ancho // 2, alto // 2)

    capa = pygame.Surface(panel.size, pygame.SRCALPHA)
    capa.fill(COLOR_FONDO)
    screen.blit(capa, panel.topleft)
    pygame.draw.rect(screen, COLOR_BORDE, panel, 2)

    f_titulo = fuente_de_tamano(max(16, min(24, panel.width // 40)))
    f_nodo = fuente_de_tamano(max(11, min(15, panel.width // 72)))
    f_pista = fuente_de_tamano(max(11, min(14, panel.width // 80)))

    titulo = f_titulo.render(f"Árbol de comportamiento · {alien.nombre} ({numero}/{total})",
                             True, COLOR_TITULO)
    screen.blit(titulo, (panel.x + 18, panel.y + 12))
    accion = alien.camino[-1].texto if alien.camino else "-"
    estado = f_titulo.render(f"Ahora: {accion}", True, COLOR_ACTIVO)
    screen.blit(estado, (panel.right - estado.get_width() - 18, panel.y + 12))

    pista = f_pista.render("[B] cerrar   [N] siguiente alien   amarillo = la rama que está tomando",
                           True, COLOR_TENUE)
    screen.blit(pista, (panel.x + 18, panel.bottom - pista.get_height() - 10))

    columna, niveles = _posiciones(arbol)
    profundidad = max(niveles.values()) + 1
    zona = pygame.Rect(panel.x + 12, panel.y + 56, panel.width - 24,
                       panel.height - 56 - pista.get_height() - 22)
    alto_nivel = zona.height / profundidad
    ancho_caja = int(min(170, zona.width / len(arbol.hojas()) - 10))
    alto_caja = int(min(62, alto_nivel - 14))

    activos = {id(n) for n in alien.camino}

    def centro(nodo):
        return (int(zona.x + columna[id(nodo)] * zona.width),
                int(zona.y + niveles[id(nodo)] * alto_nivel + alto_caja / 2 + 4))

    # Aristas primero, para que las cajas queden encima.
    for nodo, _, padre in arbol.por_niveles():
        if padre is None:
            continue
        activo = id(nodo) in activos and id(padre) in activos
        a, b = centro(padre), centro(nodo)
        a = (a[0], a[1] + alto_caja // 2)
        b = (b[0], b[1] - alto_caja // 2)
        pygame.draw.line(screen, COLOR_ACTIVO if activo else COLOR_ARISTA, a, b, 4 if activo else 2)
        etiqueta = "sí" if padre.si is nodo else "no"
        texto = f_pista.render(etiqueta, True, COLOR_ACTIVO if activo else COLOR_TENUE)
        medio = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
        lado = -1 if b[0] < a[0] else 1
        screen.blit(texto, (medio[0] + lado * 8 - (texto.get_width() if lado < 0 else 0),
                            medio[1] - texto.get_height()))

    for nodo, _, _ in arbol.por_niveles():
        cx, cy = centro(nodo)
        caja = pygame.Rect(0, 0, ancho_caja, alto_caja)
        caja.center = (cx, cy)
        activo = id(nodo) in activos
        fondo = COLOR_ACCION if nodo.es_hoja else COLOR_PREGUNTA
        pygame.draw.rect(screen, fondo, caja, border_radius=8)
        pygame.draw.rect(screen, COLOR_ACTIVO if activo else COLOR_BORDE, caja,
                         3 if activo else 1, border_radius=8)

        lineas = partir_lineas(nodo.texto, f_nodo, ancho_caja - 12)[:3]
        alto_texto = len(lineas) * f_nodo.get_linesize()
        y = cy - alto_texto // 2
        for linea in lineas:
            color = COLOR_ACTIVO if activo and nodo.es_hoja else COLOR_TEXTO
            render = f_nodo.render(linea, True, color)
            screen.blit(render, (cx - render.get_width() // 2, y))
            y += f_nodo.get_linesize()
