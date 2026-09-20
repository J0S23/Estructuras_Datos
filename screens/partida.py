"""Pantalla de partida: el mundo con la vista dividida por jugador.

Cada jugador tiene su propio viewport con una cámara que lo sigue. Todos los
personajes se dibujan en todos los viewports, así que cada jugador ve al otro
moverse por el mapa.

Los layouts siguen el CLAUDE.md: con dos jugadores la pantalla se parte en
vertical (izquierda y derecha); con tres, dos arriba y uno abajo a lo ancho;
con cuatro, en cuartos.
"""

import pygame

from fuentes import fuente
from screens.paneles import render_panel, render_hud, render_mensaje, render_pista_zona
from screens.panel_habilidades import render_panel_habilidades


COLOR_SEPARADOR = (18, 16, 30)
COLOR_ETIQUETA = (255, 255, 255)
COLOR_SOMBRA = (12, 11, 23)
GROSOR_SEPARADOR = 4

# Colores de la vista de hitboxes ([H]). Son los mismos que usan los editores
# de Editores/, para que lo que se dibuja ahí se reconozca aquí.
COLOR_PARED = (90, 180, 255)
COLOR_ZONA = (255, 140, 70)
COLOR_COLISION = (230, 60, 60)
COLOR_INTERACCION = (255, 210, 40)


def calcular_viewports(ancho, alto, cantidad):
    """Divide la pantalla según cuántos jugadores haya (ver CLAUDE.md)."""
    if cantidad <= 1:
        return [pygame.Rect(0, 0, ancho, alto)]

    mitad_x = ancho // 2
    if cantidad == 2:
        # Ciudadano izquierda, Candidato derecha.
        return [
            pygame.Rect(0, 0, mitad_x, alto),
            pygame.Rect(mitad_x, 0, ancho - mitad_x, alto),
        ]

    mitad_y = alto // 2
    if cantidad == 3:
        # Jugadores 1 y 2 arriba, lado a lado; el 3 abajo ocupando todo el
        # ancho. Queda como una Y invertida: dos ramas arriba y el tronco
        # abajo.
        return [
            pygame.Rect(0, 0, mitad_x, mitad_y),
            pygame.Rect(mitad_x, 0, ancho - mitad_x, mitad_y),
            pygame.Rect(0, mitad_y, ancho, alto - mitad_y),
        ]

    # Cuatro: ciudadano arriba-izq, candidato arriba-der,
    # influencer abajo-izq, periodista abajo-der.
    return [
        pygame.Rect(0, 0, mitad_x, mitad_y),
        pygame.Rect(mitad_x, 0, ancho - mitad_x, mitad_y),
        pygame.Rect(0, mitad_y, mitad_x, alto - mitad_y),
        pygame.Rect(mitad_x, mitad_y, ancho - mitad_x, alto - mitad_y),
    ]


def render_partida(screen, mundo, jugadores, zonas=(), segundos_restantes=0,
                   mostrar_hitboxes=False):
    """Dibuja un viewport por jugador, cada uno con su cámara, HUD y paneles."""
    ancho, alto = screen.get_size()
    viewports = calcular_viewports(ancho, alto, len(jugadores))
    screen.fill(COLOR_SEPARADOR)

    for indice, jugador in enumerate(jugadores):
        if indice >= len(viewports):
            break
        vista = viewports[indice]
        _dibujar_vista(screen, vista, mundo, jugadores, jugador, zonas, mostrar_hitboxes)

        # Lo de la interfaz va después del mundo pero sigue recortado al
        # viewport: si el ciudadano abre una tarea, el candidato no la ve ni se
        # le congela su mitad.
        clip_previo = screen.get_clip()
        screen.set_clip(vista)
        render_hud(screen, vista, jugador, segundos_restantes)
        render_pista_zona(screen, vista, jugador)
        if jugador.panel is not None and jugador.panel.get("tipo") == "habilidades":
            render_panel_habilidades(screen, vista, jugador)
        else:
            render_panel(screen, vista, jugador)
        render_mensaje(screen, vista, jugador)
        screen.set_clip(clip_previo)

    _dibujar_separadores(screen, viewports)
    if mostrar_hitboxes:
        _dibujar_leyenda(screen, mundo, jugadores)
    else:
        _dibujar_pista(screen)


def _dibujar_pista(screen):
    """Recordatorio de las teclas del prototipo, abajo a la derecha."""
    font = fuente("small")
    texto = "[H] hitboxes   [TAB] ver el ABB   [ESC] menu"
    etiqueta = font.render(texto, True, (200, 210, 235))
    sombra = font.render(texto, True, COLOR_SOMBRA)
    pos = (screen.get_width() - etiqueta.get_width() - 12,
           screen.get_height() - etiqueta.get_height() - 8)
    screen.blit(sombra, (pos[0] + 2, pos[1] + 2))
    screen.blit(etiqueta, pos)


def _dibujar_leyenda(screen, mundo, jugadores):
    """Franja inferior que explica de qué es cada color, al activar [H]."""
    entradas = [
        (COLOR_PARED, f"paredes ({len(mundo.paredes)})"),
        (COLOR_ZONA, f"zonas ({len(mundo.interactuables)})"),
        (COLOR_COLISION, "colision personaje"),
        (COLOR_INTERACCION, "interaccion personaje"),
    ]
    font = fuente("small")
    alto_franja = 26
    y = screen.get_height() - alto_franja

    franja = pygame.Surface((screen.get_width(), alto_franja), pygame.SRCALPHA)
    franja.fill((0, 0, 0, 190))
    screen.blit(franja, (0, y))

    x = 12
    for color, texto in entradas:
        pygame.draw.rect(screen, color, (x, y + 8, 14, 10), 2)
        etiqueta = font.render(texto, True, COLOR_ETIQUETA)
        screen.blit(etiqueta, (x + 20, y + 4))
        x += 20 + etiqueta.get_width() + 22

    pista = font.render("[H] ocultar", True, (170, 180, 205))
    screen.blit(pista, (screen.get_width() - pista.get_width() - 12, y + 4))


def _dibujar_vista(screen, vista, mundo, jugadores, dueño, zonas, mostrar_hitboxes):
    camara = mundo.camara(dueño.hitbox.center, vista.width, vista.height)

    # Recorta el dibujo al viewport para que nada se salga a la mitad vecina.
    clip_previo = screen.get_clip()
    screen.set_clip(vista)

    # En pantallas muy grandes un viewport puede ser más ancho o alto que el
    # mapa; en ese caso se centra lo que hay en vez de dejarlo pegado a un borde.
    destino = list(vista.topleft)
    if camara.width > mundo.ancho:
        destino[0] += (camara.width - mundo.ancho) // 2
    if camara.height > mundo.alto:
        destino[1] += (camara.height - mundo.alto) // 2
    screen.blit(mundo.imagen, destino, area=camara)

    if mostrar_hitboxes:
        # Hitboxes del fondo: paredes y zonas interactuables del mapa.
        for pared in mundo.paredes:
            if pared.colliderect(camara):
                pygame.draw.rect(screen, COLOR_PARED, _a_pantalla(pared, vista, camara), 2)
        for zona in mundo.interactuables:
            if zona.colliderect(camara):
                pygame.draw.rect(screen, COLOR_ZONA, _a_pantalla(zona, vista, camara), 2)

    # Zonas de tarea: se dibujan antes que los personajes para que queden en
    # el piso. Solo se marcan las que ese jugador puede usar, así cada mitad de
    # la pantalla le muestra a su dueño a dónde le toca ir.
    for zona in zonas:
        if zona["roles"] and getattr(dueño, "rol", None) not in zona["roles"]:
            continue
        rect = zona["rect"]
        if not rect.colliderect(camara):
            continue
        en_pantalla = _a_pantalla(rect, vista, camara)
        _dibujar_zona(screen, en_pantalla, zona, dueño)

    # Todos los personajes, ordenados por Y para que el de adelante tape al de atrás.
    for jugador in sorted(jugadores, key=lambda j: j.hitbox.bottom):
        offset = (camara.x - vista.x, camara.y - vista.y)
        jugador.dibujar(screen, offset)
        if mostrar_hitboxes:
            # Hitboxes del personaje: la de colisión y la de interacción.
            interaccion = getattr(jugador, "interactable_hitbox", None)
            if interaccion is not None:
                pygame.draw.rect(screen, COLOR_INTERACCION,
                                 _a_pantalla(interaccion, vista, camara), 1)
            pygame.draw.rect(screen, COLOR_COLISION,
                             _a_pantalla(jugador.hitbox, vista, camara), 2)

    screen.set_clip(clip_previo)


def _dibujar_zona(screen, rect, zona, dueño):
    """Marca una zona en el piso, más brillante si el jugador está encima."""
    encima = getattr(dueño, "zona_cerca", None) is zona
    color = zona.get("color", COLOR_ZONA)
    grosor = 4 if encima else 2

    marca = pygame.Surface(rect.size, pygame.SRCALPHA)
    marca.fill((*color, 70 if encima else 38))
    screen.blit(marca, rect.topleft)
    pygame.draw.ellipse(screen, color, rect, grosor)

    etiqueta = fuente("small").render(zona["nombre"], True, color)
    sombra = fuente("small").render(zona["nombre"], True, COLOR_SOMBRA)
    pos = (rect.centerx - etiqueta.get_width() // 2, rect.top - etiqueta.get_height() - 4)
    screen.blit(sombra, (pos[0] + 2, pos[1] + 2))
    screen.blit(etiqueta, pos)


def _a_pantalla(rect, vista, camara):
    """Pasa un rect de coordenadas del mundo a coordenadas de pantalla."""
    return pygame.Rect(
        rect.x - camara.x + vista.x,
        rect.y - camara.y + vista.y,
        rect.width, rect.height,
    )


def _dibujar_etiqueta(screen, vista, jugador):
    texto = f"{getattr(jugador, 'rol', 'Jugador')}  ·  {getattr(jugador, 'controles_nombre', '')}"
    etiqueta = fuente("small").render(texto.strip(" ·"), True, COLOR_ETIQUETA)
    sombra = fuente("small").render(texto.strip(" ·"), True, COLOR_SOMBRA)
    pos = (vista.x + 14, vista.y + 10)
    screen.blit(sombra, (pos[0] + 2, pos[1] + 2))
    screen.blit(etiqueta, pos)


def _dibujar_separadores(screen, viewports, color=COLOR_SEPARADOR,
                         grosor=GROSOR_SEPARADOR):
    """Dibuja el borde interior de cada viewport.

    Antes se trazaban líneas de lado a lado de la pantalla a la altura de cada
    borde. Con dos o cuatro jugadores daba igual porque los cortes van de punta
    a punta, pero con tres la línea vertical que separa a J1 de J2 seguía bajando
    y partía en dos la vista de J3. Recorriendo los bordes de cada viewport, el
    separador se dibuja solo donde de verdad hay dos vistas pegadas.
    """
    ancho, alto = screen.get_size()
    mitad = max(1, grosor // 2)
    for vista in viewports:
        if vista.left > 0:
            pygame.draw.rect(screen, color, (vista.left - mitad, vista.top, grosor, vista.height))
        if vista.right < ancho:
            pygame.draw.rect(screen, color, (vista.right - mitad, vista.top, grosor, vista.height))
        if vista.top > 0:
            pygame.draw.rect(screen, color, (vista.left, vista.top - mitad, vista.width, grosor))
        if vista.bottom < alto:
            pygame.draw.rect(screen, color, (vista.left, vista.bottom - mitad, vista.width, grosor))
