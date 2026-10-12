"""Pantalla de partida: el mundo con la vista dividida por jugador.

Cada jugador tiene su propio viewport con una cámara que lo sigue. Todos los
personajes se dibujan en todos los viewports, así que cada jugador ve al otro
moverse por el mapa.

Los layouts siguen el CLAUDE.md: con dos jugadores la pantalla se parte en
vertical (izquierda y derecha); con tres, dos arriba y uno abajo a lo ancho;
con cuatro, en cuartos.
"""

import pygame

from fuentes import fuente, fuente_de_tamano
import oscuridad
import puertas
from eventos import dibujar_cajas, dibujar_brillo_caja
from alien import DISTANCIA_OJOS
from screens.paneles import (render_panel, render_hud, render_mensaje, render_pista_zona,
                             render_pulso, render_tension, render_minijuego,
                             render_escondido)
from ambiente import temblor, dibujar_susto
from screens.panel_habilidades import render_panel_habilidades
from screens import roles as dibujo_roles
from screens import mision_dibujo


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
                   mostrar_hitboxes=False, aliens=(), escondites=(), extras=None):
    """Dibuja un viewport por jugador, cada uno con su cámara, HUD y paneles."""
    ancho, alto = screen.get_size()
    viewports = calcular_viewports(ancho, alto, len(jugadores))
    extras = dict(extras or {})
    extras.setdefault("aliens", aliens)
    extras.setdefault("escondites", escondites)
    extras.setdefault("jugadores", jugadores)
    extras.setdefault("mundo", mundo)
    screen.fill(COLOR_SEPARADOR)

    for indice, jugador in enumerate(jugadores):
        if indice >= len(viewports):
            break
        vista = viewports[indice]
        _dibujar_vista(screen, vista, mundo, jugadores, jugador, zonas, mostrar_hitboxes,
                       aliens, escondites, extras)

        # Lo de la interfaz va después del mundo pero sigue recortado al
        # viewport: si el ciudadano abre una tarea, el candidato no la ve ni se
        # le congela su mitad.
        clip_previo = screen.get_clip()
        screen.set_clip(vista)
        render_escondido(screen, vista, jugador)
        render_tension(screen, vista, jugador)
        render_hud(screen, vista, jugador, segundos_restantes)
        render_pista_zona(screen, vista, jugador)
        if jugador.panel is not None and jugador.panel.get("tipo") == "habilidades":
            render_panel_habilidades(screen, vista, jugador)
        else:
            render_panel(screen, vista, jugador)
        render_mensaje(screen, vista, jugador)
        render_pulso(screen, vista, jugador)
        dibujo_roles.render_minimapa(screen, vista, jugador, extras)
        mision_dibujo.render_progreso(screen, vista, jugador)
        render_minijuego(screen, vista, jugador)
        render_tutorial(screen, vista, jugador, extras.get("tutorial"))
        dibujar_susto(screen, vista, jugador)
        screen.set_clip(clip_previo)

    _dibujar_separadores(screen, viewports)
    render_evento(screen, extras.get("eventos"))
    if mostrar_hitboxes:
        _dibujar_leyenda(screen, mundo, jugadores)
    else:
        _dibujar_pista(screen)


def _dibujar_pista(screen):
    """Recordatorio de las teclas del prototipo, abajo a la derecha."""
    font = fuente("small")
    texto = "[H] hitboxes   [B] arbol del alien   [L] luz   [TAB] ver el ABB   [ESC] menu"
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


def _dibujar_vista(screen, vista, mundo, jugadores, dueño, zonas, mostrar_hitboxes,
                   aliens=(), escondites=(), extras=None):
    camara = mundo.camara(dueño.hitbox.center, vista.width, vista.height)
    # Si lo acaban de atrapar, su mitad de la pantalla tiembla un instante.
    camara = camara.move(*temblor(dueño, pygame.time.get_ticks()))

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

    offset = (camara.x - vista.x, camara.y - vista.y)

    for escondite in escondites:
        if escondite["rect"].inflate(0, 120).colliderect(camara):
            _dibujar_escondite(screen, escondite, offset, dueño)
    tiempo_ms = pygame.time.get_ticks()
    if extras:
        mision_dibujo.dibujar_piso(screen, offset, camara, dueño, extras.get("mision"), tiempo_ms)
        dibujo_roles.dibujar_piso(screen, offset, camara, dueño, extras, tiempo_ms)

    if extras:
        puertas.dibujar(screen, offset, camara, extras.get("puertas_dobles", ()),
                        extras.get("compuertas", ()), tiempo_ms)
        dibujar_cajas(screen, offset, camara, extras.get("eventos"), tiempo_ms)

    # Los conos de visión van en el piso, debajo de todos los personajes.
    for alien in aliens:
        alien.dibujar_vision(screen, offset)

    # Jugadores y aliens juntos, ordenados por Y para que el de adelante tape
    # al de atrás.
    for jugador in sorted(list(jugadores) + list(aliens), key=lambda j: j.hitbox.bottom):
        jugador.dibujar(screen, offset)
        if mostrar_hitboxes:
            # Hitboxes del personaje: la de colisión y la de interacción.
            interaccion = getattr(jugador, "interactable_hitbox", None)
            if interaccion is not None:
                pygame.draw.rect(screen, COLOR_INTERACCION,
                                 _a_pantalla(interaccion, vista, camara), 1)
            pygame.draw.rect(screen, COLOR_COLISION,
                             _a_pantalla(jugador.hitbox, vista, camara), 2)

    # Oscuridad: encima del mundo y de los personajes, debajo de los avisos.
    # Con [H] se apaga para poder revisar las hitboxes.
    eventos = (extras or {}).get("eventos")
    if (extras or {}).get("oscuridad") and not mostrar_hitboxes:
        oscuridad.dibujar(screen, vista, camara, dueño, jugadores)
        dibujar_brillo_caja(screen, offset, dueño, eventos, tiempo_ms)
        centro = dueño.hitbox.center
        for alien in aliens:
            if (abs(alien.centro[0] - centro[0]) + abs(alien.centro[1] - centro[1])
                    <= DISTANCIA_OJOS * 1.4):
                alien.dibujar_ojos(screen, offset)
    for alien in aliens:
        alien.dibujar_senal(screen, offset)
    _dibujar_ruido(screen, offset, dueño)

    if extras:
        mision_dibujo.dibujar_encima(screen, offset, camara, extras.get("mision"), tiempo_ms)
        dibujo_roles.dibujar_encima(screen, offset, camara, dueño, extras, tiempo_ms)
        dibujo_roles.dibujar_flechas(screen, vista, camara, dueño, extras)

    screen.set_clip(clip_previo)


def _dibujar_ruido(screen, offset, dueño):
    """El anillo de ruido del jugador: si un alien queda adentro, lo oye.

    Celeste cuando va en sigilo, para que se note que la tecla sirve.
    """
    if (getattr(dueño, "preso", None) is not None or not hasattr(dueño, "radio_ruido")
            or not getattr(dueño, "puede_moverse", True)):
        return
    centro = (dueño.hitbox.centerx - offset[0], dueño.hitbox.centery - offset[1])
    radio = int(dueño.radio_ruido)
    sigilo = getattr(dueño, "sigilo", False)
    if sigilo:
        color = (110, 220, 255)
    elif dueño.pulso > 70:
        color = (240, 90, 80)
    else:
        color = (150, 160, 190)
    pygame.draw.circle(screen, color, centro, radio, 1)
    if sigilo:
        pygame.draw.circle(screen, color, centro, max(4, radio - 4), 1)


def _envolver(texto, f, ancho):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if f.size(prueba)[0] <= ancho or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def render_tutorial(screen, vista, jugador, tutorial):
    """El paso del tutorial de este jugador, abajo del centro de su vista."""
    if tutorial is None or not tutorial.activo or not getattr(jugador, "puede_moverse", True):
        return   # los puestos sin mando todavía no se mueven: no hay qué enseñarles
    datos = tutorial.texto(jugador)
    if datos is None:
        return
    paso, total, texto = datos
    pequena = vista.height < 500
    f = fuente_de_tamano(15 if pequena else 18)
    f_chica = fuente_de_tamano(12 if pequena else 14)
    ancho = min(vista.width - 40, 600)
    lineas = _envolver(texto, f, ancho - 32)
    alto = 40 + len(lineas) * f.get_linesize() + f_chica.get_linesize()
    caja = pygame.Rect(0, 0, ancho, alto)
    if pequena:
        # Con 3 o 4 jugadores abajo no cabe: ahí van el pulso, la pista y la
        # barra de progreso. Se pone arriba, debajo del HUD y los mensajes; en
        # la fila de arriba, además, debajo del cartel de la IA (y=100..152).
        caja.midtop = (vista.centerx, vista.y + (160 if vista.top == 0 else 92))
    else:
        caja.midtop = (vista.centerx, vista.centery + vista.height // 7)
    fondo = pygame.Surface(caja.size, pygame.SRCALPHA)
    fondo.fill((12, 14, 30, 225))
    screen.blit(fondo, caja.topleft)
    pygame.draw.rect(screen, (90, 220, 230), caja, 2, border_radius=6)
    titulo = f_chica.render(f"TUTORIAL  {paso}/{total}   ·   los aliens despiertan en "
                            f"{tutorial.segundos} s", True, (90, 220, 230))
    screen.blit(titulo, (caja.x + 16, caja.y + 10))
    y = caja.y + 14 + f_chica.get_linesize()
    for linea in lineas:
        screen.blit(f.render(linea, True, (240, 242, 255)), (caja.x + 16, y))
        y += f.get_linesize()
    pie = f_chica.render(f"[{jugador.nombre_tecla('habilidad')}] saltar", True, (150, 156, 190))
    screen.blit(pie, (caja.right - pie.get_width() - 14, caja.bottom - pie.get_height() - 8))


def render_evento(screen, eventos):
    """Aviso arriba al centro mientras dura un evento aleatorio."""
    if eventos is None:
        return
    texto = eventos.texto()
    if texto is None:
        return
    color = eventos.color()
    f = fuente_de_tamano(18)
    img = f.render(texto, True, color)
    # Debajo del cartel de la IA (y=100..152): más arriba chocaba con los
    # mensajes de cada jugador. No coincide con el tutorial (no hay eventos
    # mientras dura), que con 3 o 4 jugadores usa este mismo lugar.
    caja = img.get_rect(midtop=(screen.get_width() // 2, 160)).inflate(28, 10)
    fondo = pygame.Surface(caja.size, pygame.SRCALPHA)
    fondo.fill((10, 8, 20, 220))
    screen.blit(fondo, caja.topleft)
    if (pygame.time.get_ticks() // 400) % 2:
        pygame.draw.rect(screen, color, caja, 2, border_radius=4)
    screen.blit(img, img.get_rect(center=caja.center))


def _dibujar_escondite(screen, escondite, offset, dueño):
    """Casillero provisional (falta el arte): una caja de metal con rendijas."""
    entrada = escondite["rect"]
    caja = pygame.Rect(0, 0, 50, 78)
    caja.midbottom = (entrada.centerx - offset[0], entrada.top + 6 - offset[1])

    mio = escondite["ocupante"] is dueño
    cerca = getattr(dueño, "escondite_cerca", None) is escondite
    revisado = escondite.get("revisado_por") is not None

    pygame.draw.rect(screen, (10, 12, 20), caja.move(3, 3), border_radius=4)
    pygame.draw.rect(screen, (78, 96, 120), caja, border_radius=4)
    borde = (236, 70, 60) if revisado else (255, 214, 64) if (cerca or mio) else (34, 40, 58)
    pygame.draw.rect(screen, borde, caja, 3 if (cerca or mio or revisado) else 2, border_radius=4)
    for i in range(4):
        y = caja.y + 12 + i * 7
        pygame.draw.line(screen, (34, 40, 58), (caja.x + 12, y), (caja.right - 12, y), 2)
    pygame.draw.circle(screen, (200, 205, 220), (caja.right - 10, caja.centery + 8), 3)

    if cerca or mio:
        texto = "Escondido" if mio else escondite["nombre"]
        etiqueta = fuente("small").render(texto, True, (255, 214, 64))
        sombra = fuente("small").render(texto, True, COLOR_SOMBRA)
        pos = (caja.centerx - etiqueta.get_width() // 2, caja.y - etiqueta.get_height() - 4)
        screen.blit(sombra, (pos[0] + 2, pos[1] + 2))
        screen.blit(etiqueta, pos)


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
