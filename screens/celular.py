"""Dibujo del celular (NEXUS) y de lo que NEXUS pone en la pantalla.

- render_celular: el teléfono abierto, a la derecha del viewport del jugador.
  Se ve como una red social cualquiera (publicaciones, compartir, reportar);
  el grafo de nexus.py no se dibuja.
- render_confianza: la barra de confianza de la tripulación, UNA para todo el
  equipo, arriba al centro: verde (confían en ustedes) desde la izquierda,
  roja (en los aliens) desde la derecha y gris en medio; cada parte mide su %.
  La raya blanca marca cuánto verde hace falta para los planos.
- render_aviso_celular: en el HUD de cada uno, su tecla del celular y lo nuevo.
- dibujar_lugar: la flecha y el aro hacia el lugar que el jugador está
  investigando.
"""

import math
import zlib

import pygame

from juego.fuentes import fuente_de_tamano
from screens.paneles import partir_lineas
from data.nexus import NOMBRE_LUGAR, UMBRAL_PLANOS

COLOR_CARCASA = (18, 18, 26)
COLOR_PANTALLA = (238, 240, 247)
COLOR_TARJETA = (255, 255, 255)
COLOR_TARJETA_SEL = (226, 236, 255)
COLOR_BORDE_SEL = (70, 120, 230)
COLOR_TEXTO = (30, 32, 44)
COLOR_TENUE = (110, 116, 140)
COLOR_MARCA = (52, 108, 220)
COLOR_VERDE = (60, 190, 110)
COLOR_ROJO = (225, 70, 70)
COLOR_FOTO = (255, 236, 170)
COLOR_SOMBRA = (12, 11, 23)
COLOR_LUGAR = (90, 170, 255)

AVATARES = [(239, 108, 110), (99, 160, 234), (120, 200, 140), (240, 180, 80),
            (176, 120, 220), (90, 196, 200), (230, 130, 190), (150, 160, 180)]


def _avatar(screen, centro, radio, usuario, f):
    color = AVATARES[zlib.crc32(usuario.encode("utf-8")) % len(AVATARES)]
    pygame.draw.circle(screen, color, centro, radio)
    letra = usuario.lstrip("@")[:1].upper() or "?"
    img = f.render(letra, True, (255, 255, 255))
    screen.blit(img, img.get_rect(center=centro))


def _tiempo(ms):
    s = int(ms // 1000)
    if s < 60:
        return "ahora" if s < 5 else f"hace {s} s"
    return f"hace {s // 60} min"


# -- La barra de confianza ------------------------------------------------------------------

def _barra_ponderada(screen, rect, verde, rojo, umbral=UMBRAL_PLANOS):
    """Una sola barra: verde desde la izquierda, roja desde la derecha y gris en
    medio (los que no deciden). Cada parte mide lo que pesa en la tripulación.
    La raya blanca marca cuánto verde hace falta para los planos."""
    pygame.draw.rect(screen, (96, 100, 118), rect, border_radius=rect.height // 2)
    ancho_verde = int(rect.width * verde)
    ancho_rojo = int(rect.width * rojo)
    if ancho_verde > 0:
        pygame.draw.rect(screen, COLOR_VERDE, (rect.x, rect.y, ancho_verde, rect.height),
                         border_top_left_radius=rect.height // 2,
                         border_bottom_left_radius=rect.height // 2)
    if ancho_rojo > 0:
        pygame.draw.rect(screen, COLOR_ROJO, (rect.right - ancho_rojo, rect.y, ancho_rojo, rect.height),
                         border_top_right_radius=rect.height // 2,
                         border_bottom_right_radius=rect.height // 2)
    x = rect.x + int(rect.width * umbral)
    pygame.draw.line(screen, (255, 255, 255), (x, rect.y - 3), (x, rect.bottom + 2), 2)
    pygame.draw.rect(screen, (20, 20, 32), rect, 1, border_radius=rect.height // 2)


def _fuente_barra(ancho):
    return fuente_de_tamano(max(12, min(18, ancho // 105)))


def rect_confianza(screen, cantidad):
    """Dónde va la barra general: arriba al centro, justo debajo del HUD."""
    from screens.partida import calcular_viewports
    from screens.paneles import _fuente_para
    ancho, alto = screen.get_size()
    vista = calcular_viewports(ancho, alto, max(1, cantidad))[0]
    f = _fuente_para(vista)
    abajo_hud = vista.y + f.get_linesize() * 3 + 14
    f_barra = _fuente_barra(ancho)
    caja = pygame.Rect(0, 0, int(min(620, max(300, ancho * 0.36))), f_barra.get_linesize() * 2 + 18)
    caja.midtop = (ancho // 2, abajo_hud + 4)
    return caja


def desplazamiento_avisos(screen, cantidad, red):
    """Cuánto bajar el cartel de la IA y el del evento para no tapar la barra."""
    if red is None:
        return 0
    return max(0, rect_confianza(screen, cantidad).bottom + 8 - 100)


def render_confianza(screen, red, cantidad):
    """La confianza de la tripulación, una para todo el equipo, arriba al centro."""
    if red is None:
        return
    verde, rojo = red.barras()
    caja = rect_confianza(screen, cantidad)
    fondo = pygame.Surface(caja.size, pygame.SRCALPHA)
    fondo.fill((14, 15, 28, 225))
    screen.blit(fondo, caja.topleft)
    pygame.draw.rect(screen, (90, 100, 150), caja, 1, border_radius=8)

    f = _fuente_barra(screen.get_width())
    izq = f.render(f"Ustedes {int(verde * 100)}%", True, COLOR_VERDE)
    der = f.render(f"{int(rojo * 100)}% Aliens", True, COLOR_ROJO)
    alto_barra = max(12, f.get_height() - 4)
    barra = pygame.Rect(caja.x + izq.get_width() + 18,
                        caja.y + 6 + (f.get_linesize() - alto_barra) // 2,
                        caja.width - izq.get_width() - der.get_width() - 36, alto_barra)
    screen.blit(izq, (caja.x + 10, barra.centery - izq.get_height() // 2))
    screen.blit(der, (caja.right - der.get_width() - 10, barra.centery - der.get_height() // 2))
    _barra_ponderada(screen, barra, verde, rojo, getattr(red, "umbral_planos", UMBRAL_PLANOS))

    if red.planos:
        texto, color = "Confianza de la tripulación  ·  ¡planos listos!", COLOR_VERDE
    elif rojo > verde:
        texto, color = "Los aliens van ganando: están más rápidos y ven más", (245, 150, 140)
    else:
        texto, color = f"Confianza de la tripulación  ·  planos al {int(getattr(red, 'umbral_planos', UMBRAL_PLANOS) * 100)}%", \
            (190, 196, 230)
    img = f.render(texto, True, color)
    screen.blit(img, img.get_rect(midbottom=(caja.centerx, caja.bottom - 5)))


def render_aviso_celular(screen, vista, jugador, red):
    """En el HUD de cada uno: su tecla del celular y cuántas cosas nuevas tiene."""
    if red is None:
        return
    from screens.paneles import _fuente_para
    f_hud = _fuente_para(vista)
    izq = vista.x + 12 + f_hud.size(f"{jugador.rol}  ·  {jugador.controles_nombre}")[0] + 16
    der = vista.right - 12 - f_hud.size(f"{jugador.puntos} pts")[0] - 16
    f = fuente_de_tamano(max(11, min(15, vista.width // 60)))
    nuevas = red.sin_leer(jugador)
    texto = f"NEXUS [{jugador.nombre_tecla('celular')}]" + (f"  {nuevas} nuevo(s)" if nuevas else "")
    img = f.render(texto, True, (255, 214, 64) if nuevas else (170, 178, 214))
    if img.get_width() > der - izq:
        img = f.render(f"[{jugador.nombre_tecla('celular')}]" + (f" {nuevas}" if nuevas else ""),
                       True, (255, 214, 64) if nuevas else (170, 178, 214))
    x = izq + max(0, (der - izq - img.get_width()) // 2)
    screen.blit(img, (x, vista.y + 7))


# -- El lugar que investiga ------------------------------------------------------------------

def dibujar_lugar(screen, vista, camara, dueño, red, tiempo_ms):
    if red is None:
        return
    pub = red.investigando.get(dueño)
    if pub is None or pub.desmentida or pub.lugar is None:
        return
    x, y = pub.lugar
    if camara.collidepoint(x, y):
        centro = (int(x - camara.x + vista.x), int(y - camara.y + vista.y))
        radio = 30 + int(6 * math.sin(tiempo_ms / 200))
        pygame.draw.circle(screen, COLOR_LUGAR, centro, radio, 3)
        cam = pygame.Rect(0, 0, 22, 15)
        cam.center = centro
        pygame.draw.rect(screen, COLOR_LUGAR, cam, border_radius=3)
        pygame.draw.circle(screen, (255, 255, 255), centro, 4)
        return
    c = dueño.hitbox.center
    dx, dy = x - c[0], y - c[1]
    distancia = math.hypot(dx, dy) or 1
    ux, uy = dx / distancia, dy / distancia
    margen = 46
    mitad_w, mitad_h = vista.width / 2 - margen, vista.height / 2 - margen
    escala = min(mitad_w / abs(ux) if ux else 1e9, mitad_h / abs(uy) if uy else 1e9)
    px, py = vista.centerx + ux * escala, vista.centery + uy * escala
    angulo = math.atan2(uy, ux)
    tam = 16
    punta = (px + math.cos(angulo) * tam, py + math.sin(angulo) * tam)
    izq = (px + math.cos(angulo + 2.5) * tam, py + math.sin(angulo + 2.5) * tam)
    der = (px + math.cos(angulo - 2.5) * tam, py + math.sin(angulo - 2.5) * tam)
    pygame.draw.polygon(screen, COLOR_LUGAR, [punta, izq, der])
    pygame.draw.polygon(screen, COLOR_SOMBRA, [punta, izq, der], 2)


# -- El celular --------------------------------------------------------------------------------

def _marco(vista):
    """Rect del teléfono y de su pantalla, a la derecha del viewport."""
    arriba = vista.y + min(90, vista.height // 6)
    alto = vista.bottom - arriba - 12
    ancho = int(min(380, max(240, vista.width * 0.46), alto * 0.62 + 60))
    telefono = pygame.Rect(vista.right - ancho - 14, arriba, ancho, alto)
    pantalla = telefono.inflate(-16, -34)
    pantalla.y = telefono.y + 14
    return telefono, pantalla


def render_celular(screen, vista, jugador, red):
    panel = jugador.panel
    if panel is None or red is None:
        return
    telefono, pantalla = _marco(vista)
    pygame.draw.rect(screen, COLOR_SOMBRA, telefono.move(5, 5), border_radius=22)
    pygame.draw.rect(screen, COLOR_CARCASA, telefono, border_radius=22)
    pygame.draw.rect(screen, (70, 72, 92), telefono, 2, border_radius=22)
    pygame.draw.rect(screen, COLOR_PANTALLA, pantalla, border_radius=10)
    pygame.draw.circle(screen, (50, 52, 70), (telefono.centerx, telefono.bottom - 10), 4)

    tam = max(11, min(16, pantalla.width // 22))
    f = fuente_de_tamano(tam)
    fb = fuente_de_tamano(tam + 3)
    clip = screen.get_clip()
    screen.set_clip(pantalla.clip(clip) if clip else pantalla)

    # Encabezado: el nombre de la red y las barras.
    cab = pygame.Rect(pantalla.x, pantalla.y, pantalla.width, fb.get_linesize() + 34)
    pygame.draw.rect(screen, (24, 28, 52), cab, border_top_left_radius=10, border_top_right_radius=10)
    screen.blit(fb.render("NEXUS", True, (150, 200, 255)), (cab.x + 12, cab.y + 6))
    sub = {"feed": "Inicio", "post": "Publicación", "origen": "¿De dónde salió?",
           "ubicacion": "Publicar foto", "mensaje": ""}.get(panel.get("vista"), "")
    if sub:
        img = f.render(sub, True, (190, 196, 230))
        screen.blit(img, (cab.right - img.get_width() - 12, cab.y + 9))
    verde, rojo = red.barras()
    barra = pygame.Rect(cab.x + 12, cab.bottom - 20, cab.width - 24, 10)
    _barra_ponderada(screen, barra, verde, rojo, getattr(red, "umbral_planos", UMBRAL_PLANOS))

    cuerpo = pygame.Rect(pantalla.x + 8, cab.bottom + 8, pantalla.width - 16,
                         pantalla.bottom - cab.bottom - 8 - f.get_linesize() - 10)
    vista_cel = panel.get("vista")
    if vista_cel == "feed":
        _feed(screen, cuerpo, jugador, red, panel, f, fb)
    else:
        _detalle(screen, cuerpo, jugador, red, panel, f, fb)

    pie = (f"[{jugador.nombre_tecla('interactuar')}] elegir   "
           f"[{jugador.nombre_tecla('celular')}] {'cerrar' if vista_cel == 'feed' else 'atrás'}")
    img = f.render(pie, True, COLOR_TENUE)
    screen.blit(img, img.get_rect(midbottom=(pantalla.centerx, pantalla.bottom - 4)))
    screen.set_clip(clip)


def _tarjeta_feed(red, jugador, tipo, dato, f, ancho):
    """(lineas de texto, colores, extra) de una tarjeta del feed."""
    if tipo == "foto":
        lugar = NOMBRE_LUGAR.get(dato.rumor["lugar"], "el lugar")
        return {"titulo": "Tienes una foto para desmentir", "fondo": COLOR_FOTO,
                "autor": "@tu_camara",
                "lineas": partir_lineas(f"Foto de {lugar}. Publícala para frenar el rumor.",
                                        f, ancho)[:3], "marcas": []}
    pub = dato
    autor = red.via(jugador, pub) if pub.tipo in ("rumor", "trampa") else pub.autor
    usuario = red.usuario(autor)
    marcas = []
    if pub.tipo == "rumor" and pub.desmentida:
        marcas.append(("DESMENTIDO", COLOR_VERDE))
    if pub.tipo == "desmentido":
        marcas.append(("con foto", COLOR_MARCA))
    if pub.tipo == "testimonio":
        marcas.append(("rescatado", COLOR_VERDE))
    if pub.tipo == "trampa" and pub.reportada:
        marcas.append(("cuenta suplantada", COLOR_ROJO))
    if red.investigando.get(jugador) is pub:
        marcas.append(("investigando", COLOR_MARCA))
    if pub.id not in red.vistas[jugador] and pub.tipo != "normal":
        marcas.append(("nuevo", (230, 150, 40)))
    texto = pub.texto
    if pub.tipo == "compartido":
        texto = "Compartido: " + texto
    return {"titulo": None, "fondo": COLOR_TARJETA, "autor": usuario,
            "lineas": partir_lineas(texto, f, ancho)[:3], "marcas": marcas,
            "tiempo": _tiempo(pub.edad_ms)}


def _feed(screen, cuerpo, jugador, red, panel, f, fb):
    opciones = panel.get("opciones", [])
    if not opciones:
        img = f.render("Todavía no te ha llegado nada.", True, COLOR_TENUE)
        screen.blit(img, img.get_rect(center=cuerpo.center))
        return
    ancho_texto = cuerpo.width - 56
    tarjetas = [_tarjeta_feed(red, jugador, t, d, f, ancho_texto) for t, d in opciones]
    linea = f.get_linesize()
    alturas = [12 + linea * (1 + len(t["lineas"])) + (linea if t["marcas"] else 0) + 6
               for t in tarjetas]
    cursor = jugador.cursor % len(opciones)
    # Desde dónde se dibuja para que la seleccionada quede a la vista.
    inicio = 0
    while sum(alturas[inicio:cursor + 1]) + 6 * (cursor - inicio) > cuerpo.height and inicio < cursor:
        inicio += 1
    y = cuerpo.y
    for i in range(inicio, len(tarjetas)):
        t = tarjetas[i]
        rect = pygame.Rect(cuerpo.x, y, cuerpo.width, alturas[i])
        if rect.top > cuerpo.bottom:
            break
        sel = i == cursor
        fondo = COLOR_TARJETA_SEL if sel and t["fondo"] == COLOR_TARJETA else t["fondo"]
        pygame.draw.rect(screen, fondo, rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_BORDE_SEL if sel else (210, 214, 228), rect,
                         3 if sel else 1, border_radius=8)
        _avatar(screen, (rect.x + 20, rect.y + 22), 13, t["autor"], f)
        ty = rect.y + 6
        cabecera = t["titulo"] or t["autor"]
        screen.blit(f.render(cabecera, True, COLOR_TEXTO), (rect.x + 42, ty))
        if t.get("tiempo"):
            img = f.render(t["tiempo"], True, COLOR_TENUE)
            screen.blit(img, (rect.right - img.get_width() - 8, ty))
        ty += linea
        for texto in t["lineas"]:
            screen.blit(f.render(texto, True, COLOR_TEXTO), (rect.x + 42, ty))
            ty += linea
        x = rect.x + 42
        for texto, color in t["marcas"]:
            img = f.render(texto, True, (255, 255, 255))
            caja = img.get_rect(topleft=(x, ty + 2)).inflate(10, 2)
            pygame.draw.rect(screen, color, caja, border_radius=6)
            screen.blit(img, (caja.x + 5, caja.y + 1))
            x = caja.right + 6
        y = rect.bottom + 6


def _detalle(screen, cuerpo, jugador, red, panel, f, fb):
    vista = panel.get("vista")
    linea = f.get_linesize()
    y = cuerpo.y
    ancho = cuerpo.width - 16

    def parrafo(texto, color=COLOR_TEXTO, fuente=f):
        nonlocal y
        for renglon in partir_lineas(texto, fuente, ancho):
            screen.blit(fuente.render(renglon, True, color), (cuerpo.x + 8, y))
            y += fuente.get_linesize()
        y += 6

    if vista == "post":
        pub = panel["pub"]
        autor = red.via(jugador, pub) if pub.tipo in ("rumor", "trampa") else pub.autor
        usuario = red.usuario(autor)
        _avatar(screen, (cuerpo.x + 22, y + 18), 16, usuario, f)
        screen.blit(fb.render(usuario, True, COLOR_TEXTO), (cuerpo.x + 46, y + 8))
        y += 42
        parrafo(pub.texto)
        if pub.foto:
            parrafo("[Foto] " + pub.foto, COLOR_MARCA)
        if pub.tipo == "trampa":
            if pub.reportada:
                parrafo("Reportada: no la escribió su dueño.", COLOR_ROJO)
            elif autor != pub.autor:
                parrafo(f"{usuario} lo compartió.", COLOR_TENUE)
        if pub.tipo == "rumor":
            parrafo(f"Habla de {NOMBRE_LUGAR.get(pub.rumor['lugar'], 'un lugar de la nave')}.",
                    COLOR_TENUE)
            if pub.desmentida:
                parrafo("Alguien ya lo desmintió con una foto.", COLOR_VERDE)
            if autor != pub.autor:
                parrafo(f"{usuario} lo compartió. No dice de dónde lo sacó.", COLOR_TENUE)
    elif vista == "origen":
        camino = panel.get("camino") or []
        parrafo("Así te llegó:", COLOR_TENUE)
        for i, nodo in enumerate(camino):
            if nodo == red.nodo_de(jugador):
                nombre = "tú"
            else:
                nombre = red.usuario(nodo)
            nota = "  (lo publicó)" if i == 0 else ""
            parrafo(("  " * min(i, 6)) + ("> " if i else "") + nombre + nota,
                    COLOR_ROJO if i == 0 else COLOR_TEXTO)
        origen = panel.get("origen")
        pub = panel.get("pub")
        if pub is not None and pub.suplantada:
            parrafo(f"Publicado desde: dispositivo desconocido. Parece que alguien está "
                    f"usando la cuenta de {red.usuario(origen)}.", COLOR_ROJO)
        elif origen in red.grafo:
            parrafo(f"Lo empezó {red.usuario(origen)}. Los demás solo lo pasaron: "
                    "reportar a ellos no frena nada.", COLOR_TENUE)
        else:
            parrafo("La cuenta que lo empezó ya no existe.", COLOR_TENUE)
    elif vista == "ubicacion":
        rumor = panel["rumor"]
        parrafo("[Foto] " + rumor.rumor["foto"], COLOR_MARCA)
        parrafo("Tal cual: se ve dónde estás. Convence a más gente, pero el alien más "
                "cercano va a ir por ti.", COLOR_TEXTO)
        parrafo("Recortada: nadie sabe dónde estás. Convence a menos gente, pero es "
                "más seguro.", COLOR_TEXTO)
    elif vista == "mensaje":
        parrafo(panel.get("texto", ""), panel.get("color", COLOR_TEXTO), fb)
        puntos = panel.get("puntos", 0)
        if puntos:
            parrafo(f"{puntos:+d} puntos", panel.get("color", COLOR_TEXTO))

    # Opciones abajo.
    opciones = panel.get("opciones", [])
    alto_op = linea + 12
    y_op = max(y + 6, cuerpo.bottom - len(opciones) * (alto_op + 6))
    for i, (texto, _accion) in enumerate(opciones):
        rect = pygame.Rect(cuerpo.x, y_op, cuerpo.width, alto_op)
        sel = i == jugador.cursor % len(opciones)
        pygame.draw.rect(screen, COLOR_BORDE_SEL if sel else (220, 224, 236), rect, border_radius=8)
        img = f.render(texto, True, (255, 255, 255) if sel else COLOR_TEXTO)
        screen.blit(img, img.get_rect(center=rect.center))
        y_op += alto_op + 6
