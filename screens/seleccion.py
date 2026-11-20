"""Las dos pantallas previas a la partida: cuántos juegan y quién es quién.

Hay dos pasos:

1. **Cantidad**: 2, 3 o 4. Ese número decide en cuántas partes se corta la
   pantalla, así que se pregunta antes que nada.
2. **Roles**: la pantalla ya se ve partida y cada jugador escoge el suyo desde
   su propia sección, con sus propias teclas. Dos no pueden repetir rol: el que
   ya está tomado se ve tachado y no se puede confirmar.

La sección de cada jugador se dibuja con el mismo `calcular_viewports` de la
partida, así que desde la selección ya se ve qué trozo de pantalla le va a
tocar a cada uno.
"""

import math
import os

import pygame

from data.roles import ROLES, MINIMO_JUGADORES, MAXIMO_JUGADORES
from juego.fuentes import fuente_de_tamano
from juego.mandos import nombre_boton, tipo_de, PUESTOS_CON_MANDO
from screens.paneles import render_texto_mando


COLOR_FONDO = (26, 28, 48)
COLOR_TITULO = (255, 214, 64)
COLOR_TEXTO = (245, 246, 252)
COLOR_TENUE = (168, 176, 214)
COLOR_BORDE = (120, 132, 190)
COLOR_SELECCION_FONDO = (52, 57, 92)
COLOR_TOMADO = (104, 108, 132)
COLOR_LISTO = (96, 188, 118)

MARGEN = 18

# Franja de arriba reservada para el aviso de "faltan N por elegir". Las
# secciones que tocan el borde superior empiezan su contenido por debajo, o el
# aviso se monta encima del título del jugador de la derecha.
ALTO_AVISO = 34


# --------------------------------------------------------------------------
# Paso 1: cuántos juegan
# --------------------------------------------------------------------------

def render_cantidad(screen, seleccionado):
    """Menú de 2, 3 o 4 jugadores: una tarjeta por opción con el dibujo de
    cómo queda partida la pantalla. `seleccionado` es el índice en OPCIONES.
    Devuelve los rects de las tarjetas (para el mouse)."""
    from screens import estilo
    estilo.fondo(screen)
    ancho, alto = screen.get_size()
    e = max(0.7, min(1.6, min(ancho / 1280, alto / 720)))

    f_titulo = int(max(26, min(48, 40 * e)))
    f = fuente_de_tamano(max(15, min(26, int(20 * e))))
    f_grande = fuente_de_tamano(max(18, min(34, int(28 * e))))
    f_chica = fuente_de_tamano(max(12, min(20, int(15 * e))))

    y_titulo = int(alto * 0.17)
    estilo.titulo(screen, "¿CUÁNTOS JUEGAN?", (ancho // 2, y_titulo), f_titulo)
    estilo.texto(screen, "Con teclado o con mando, cada uno con su parte de la pantalla.", f,
                 (ancho // 2, y_titulo + int(52 * e)), estilo.COLOR_TENUE, "midtop")

    # Tres tarjetas lado a lado (en una pantalla angosta, una debajo de otra).
    n = len(OPCIONES)
    sep = int(26 * e)
    ancho_tarjeta = min(int(300 * e), (ancho - 80 - sep * (n - 1)) // n)
    en_fila = ancho_tarjeta >= 190
    if en_fila:
        # Alta lo justo para el dibujo, el nombre y dos renglones.
        alto_tarjeta = int(ancho_tarjeta * 0.56 + f_grande.get_linesize() + f_chica.get_linesize() * 2
                           + 44 * e)
        x = ancho // 2 - (ancho_tarjeta * n + sep * (n - 1)) // 2
        arriba = y_titulo + int(52 * e) + f.get_linesize()
        y = max(arriba + int(30 * e), (arriba + alto - 70 - alto_tarjeta) // 2)
        cajas = [pygame.Rect(x + i * (ancho_tarjeta + sep), y, ancho_tarjeta, alto_tarjeta) for i in range(n)]
    else:
        ancho_tarjeta = min(int(ancho * 0.8), 560)
        alto_tarjeta = int(min(130 * e, (alto * 0.55 - sep * (n - 1)) / n))
        y = int(alto * 0.33)
        cajas = [pygame.Rect(ancho // 2 - ancho_tarjeta // 2, y + i * (alto_tarjeta + sep), ancho_tarjeta,
                             alto_tarjeta) for i in range(n)]

    rects = []
    for i, (cantidad, caja) in enumerate(zip(OPCIONES, cajas)):
        elegido = i == seleccionado
        color = estilo.COLOR_JUGADOR[(cantidad - 2) % 4] if not elegido else estilo.COLOR_ORO
        estilo.tarjeta(screen, caja, elegido, color)
        rects.append(caja)
        if en_fila:
            dibujo = pygame.Rect(0, 0, int(caja.w * 0.64), int(caja.w * 0.4))
            dibujo.midtop = (caja.centerx, caja.y + int(caja.w * 0.08))
            estilo.icono_pantalla(screen, dibujo, cantidad, elegido)
            y_texto = dibujo.bottom + int(caja.w * 0.07)
            estilo.texto(screen, f"{cantidad} jugadores", f_grande, (caja.centerx, y_texto),
                         estilo.COLOR_ORO if elegido else estilo.COLOR_TEXTO, "midtop")
            from screens.paneles import partir_lineas
            yy = y_texto + f_grande.get_linesize() + 6
            for renglon in partir_lineas(DESCRIPCION[cantidad], f_chica, caja.w - 32):
                estilo.texto(screen, renglon, f_chica, (caja.centerx, yy), estilo.COLOR_TENUE, "midtop")
                yy += f_chica.get_linesize()
        else:
            dibujo = pygame.Rect(0, 0, int(caja.h * 1.2), int(caja.h * 0.72))
            dibujo.midleft = (caja.x + 20, caja.centery)
            estilo.icono_pantalla(screen, dibujo, cantidad, elegido)
            x = dibujo.right + 20
            estilo.texto(screen, f"{cantidad} jugadores", f_grande, (x, caja.centery - f_grande.get_linesize() // 2 - 6),
                         estilo.COLOR_ORO if elegido else estilo.COLOR_TEXTO, "midleft")
            estilo.texto(screen, DESCRIPCION[cantidad], f_chica, (x, caja.centery + f_chica.get_linesize() // 2 + 4),
                         estilo.COLOR_TENUE, "midleft")

    estilo.pie(screen, "[W/S] o flechas para elegir    [ENTER] continuar    [ESC] volver al menú", alto - 40)
    return rects


OPCIONES = list(range(MINIMO_JUGADORES, MAXIMO_JUGADORES + 1))

DESCRIPCION = {
    2: "pantalla partida en dos, lado a lado",
    3: "tres cuadros y el panel del equipo",
    4: "pantalla partida en cuatro",
}


# --------------------------------------------------------------------------
# Paso 1.5: la dificultad (data/dificultad.py)
# --------------------------------------------------------------------------

COLOR_DIFICULTAD = {
    "facil": (96, 210, 120),
    "normal": (255, 214, 64),
    "dificil": (245, 110, 100),
    "inteligente": (190, 150, 255),
}


# Qué tan duro es cada una (rombitos de 4) y un ícono.
NIVEL_DIFICULTAD = {"facil": 1, "normal": 2, "dificil": 3, "inteligente": 0}


def render_dificultad(screen, seleccionado):
    """Las dificultades en columna (tarjetas) y, al lado, qué trae la elegida."""
    from data.dificultad import DIFICULTADES
    from screens.paneles import partir_lineas
    from screens import estilo
    estilo.fondo(screen)
    ancho, alto = screen.get_size()
    e = max(0.7, min(1.6, min(ancho / 1280, alto / 720)))
    f = fuente_de_tamano(max(15, min(26, int(20 * e))))
    f_grande = fuente_de_tamano(max(17, min(32, int(25 * e))))

    y_titulo = int(alto * 0.14)
    estilo.titulo(screen, "DIFICULTAD", (ancho // 2, y_titulo), int(max(26, min(48, 40 * e))))
    estilo.texto(screen, "Qué tan dura se pone la nave. Se puede cambiar en cada partida.", f,
                 (ancho // 2, y_titulo + int(52 * e)), estilo.COLOR_TENUE, "midtop")

    lado_a_lado = ancho >= 900
    ancho_lista = min(int(ancho * (0.34 if lado_a_lado else 0.7)), int(420 * e))
    alto_opcion = f_grande.get_linesize() + int(22 * e)
    sep = int(12 * e)
    total_lista = len(DIFICULTADES) * alto_opcion + (len(DIFICULTADES) - 1) * sep
    if lado_a_lado:
        ancho_detalle = min(int(ancho * 0.44), int(560 * e))
        x_lista = ancho // 2 - (ancho_lista + int(30 * e) + ancho_detalle) // 2
        arriba = y_titulo + int(52 * e) + f.get_linesize()
        y = max(arriba + int(36 * e), (arriba + alto - 70 - total_lista) // 2)
    else:
        x_lista = ancho // 2 - ancho_lista // 2
        y = y_titulo + int(52 * e) + f.get_linesize() + int(24 * e)
    rects = []
    for i, d in enumerate(DIFICULTADES):
        elegido = i == seleccionado
        color = COLOR_DIFICULTAD.get(d["clave"], COLOR_TITULO)
        caja = pygame.Rect(x_lista, y, ancho_lista, alto_opcion)
        estilo.tarjeta(screen, caja, elegido, color)
        rects.append(caja)
        estilo.texto(screen, d["nombre"], f_grande, (caja.x + 24, caja.centery),
                     color if elegido else estilo.COLOR_TEXTO, "midleft")
        nivel = NIVEL_DIFICULTAD.get(d["clave"], 0)
        if nivel:
            estilo.medidor(screen, (caja.right - int(58 * e), caja.centery), nivel, 3,
                           color if elegido else (110, 116, 160), max(4, int(6 * e)))
        else:
            # Inteligente: una flechita que sube y baja.
            t = pygame.time.get_ticks() if elegido else 0
            cx, cy = caja.right - int(58 * e), caja.centery + int(4 * math.sin(t / 300))
            k = max(5, int(8 * e))
            c = color if elegido else (110, 116, 160)
            pygame.draw.polygon(screen, c, [(cx - k, cy + 2), (cx, cy - k), (cx + k, cy + 2)])
            pygame.draw.polygon(screen, c, [(cx - k, cy + 6), (cx, cy + k + 4), (cx + k, cy + 6)], 2)
        y += alto_opcion + sep

    # Qué trae la elegida, en su panel.
    d = DIFICULTADES[seleccionado]
    color = COLOR_DIFICULTAD.get(d["clave"], COLOR_BORDE)
    if lado_a_lado:
        caja = pygame.Rect(x_lista + ancho_lista + int(30 * e), rects[0].y, ancho_detalle,
                           rects[-1].bottom - rects[0].y)
    else:
        caja = pygame.Rect(ancho // 2 - min(int(ancho * 0.8), 720) // 2, y + 8, min(int(ancho * 0.8), 720), 0)
    renglones = partir_lineas(d["descripcion"], f, caja.w - 48)
    if not lado_a_lado:
        caja.h = len(renglones) * f.get_linesize() + f_grande.get_linesize() + int(50 * e)
    estilo.panel(screen, caja, color)
    yy = caja.y + int(18 * e)
    estilo.texto(screen, d["nombre"], f_grande, (caja.x + 24, yy), color)
    yy += f_grande.get_linesize() + int(10 * e)
    pygame.draw.line(screen, tuple(c // 2 for c in color), (caja.x + 24, yy - 4), (caja.right - 24, yy - 4), 1)
    for renglon in renglones:
        if yy + f.get_linesize() > caja.bottom - 10:
            break
        estilo.texto(screen, renglon, f, (caja.x + 24, yy), estilo.COLOR_TEXTO)
        yy += f.get_linesize()

    estilo.pie(screen, "[W/S] o flechas para elegir    [ENTER] continuar    [ESC] volver", alto - 40)
    return rects


# --------------------------------------------------------------------------
# Paso 2: qué rol juega cada uno
# --------------------------------------------------------------------------

BOTON_ESQUEMA = ["E", "Enter", "A", "A"]     # con qué se toma cada control


def _boton_esquema(esquema, accion="interactuar"):
    """El botón para tomar el control: en los mandos, el de ese mando
    (A en Xbox, Cruz en PlayStation)."""
    if esquema in PUESTOS_CON_MANDO:
        return nombre_boton(accion, tipo_de(esquema))
    return BOTON_ESQUEMA[esquema]


def render_controles(screen, esquemas, nombres, libres, conectados, volver="volver a la dificultad"):
    """Cada jugador escoge su control presionando su botón de aceptar.

    `esquemas`: el de cada jugador (None = todavía no); `nombres`: el nombre
    de cada esquema; `libres`: los que se pueden escoger; `conectados`: si
    cada esquema de mando tiene un mando conectado.
    """
    from screens import estilo
    estilo.fondo(screen)
    ancho, alto = screen.get_size()
    e = max(0.7, min(1.6, min(ancho / 1280, alto / 720)))
    f = fuente_de_tamano(max(15, min(24, int(19 * e))))
    f_grande = fuente_de_tamano(max(17, min(30, int(23 * e))))
    f_chica = fuente_de_tamano(max(13, min(19, int(15 * e))))
    t = pygame.time.get_ticks()

    y_titulo = int(alto * 0.13)
    estilo.titulo(screen, "¿CON QUÉ JUEGA CADA UNO?", (ancho // 2, y_titulo), int(max(24, min(46, 38 * e))))
    y = y_titulo + int(50 * e)
    for linea in ("Cada jugador presiona el botón de su control, en orden.",
                  "Presiónalo otra vez para soltarlo. Dos no pueden usar el mismo."):
        estilo.texto(screen, linea, f_chica, (ancho // 2, y), estilo.COLOR_TENUE, "midtop")
        y += f_chica.get_linesize() + 2

    # Una tarjeta por jugador: el que sigue late, los listos en verde.
    ancho_caja = min(int(ancho * 0.56), int(620 * e))
    alto_caja = f_grande.get_linesize() + int(20 * e)
    y += int(26 * e)
    siguiente = esquemas.index(None) if None in esquemas else None
    for jugador, esquema in enumerate(esquemas):
        caja = pygame.Rect(0, 0, ancho_caja, alto_caja)
        caja.midtop = (ancho // 2, y)
        propio = estilo.COLOR_JUGADOR[jugador % 4]
        if esquema is not None:
            estilo.tarjeta(screen, caja, False, COLOR_LISTO)
            derecha, color = nombres[esquema], COLOR_LISTO
            # Una palomita.
            cx, cy = caja.right - int(26 * e), caja.centery
            k = max(5, int(7 * e))
            pygame.draw.lines(screen, COLOR_LISTO, False, [(cx - k, cy), (cx - k // 3, cy + k * 2 // 3), (cx + k, cy - k)], 3)
            derecha_x = cx - k - int(14 * e)
        elif jugador == siguiente:
            estilo.tarjeta(screen, caja, True, propio)
            derecha = "presiona tu botón" + "." * (1 + (t // 400) % 3)
            color = estilo.COLOR_ORO
            derecha_x = caja.right - int(22 * e)
        else:
            estilo.tarjeta(screen, caja, False, propio, apagada=True)
            derecha, color = "esperando", COLOR_TOMADO
            derecha_x = caja.right - int(22 * e)
        estilo.texto(screen, f"Jugador {jugador + 1}", f_grande, (caja.x + int(26 * e), caja.centery),
                     propio if esquema is not None or jugador == siguiente else COLOR_TOMADO, "midleft")
        if derecha.startswith("presiona"):
            # Los puntitos no deben mover el texto: se ancla por la izquierda.
            estilo.texto(screen, derecha, f, (derecha_x - f.size("presiona tu botón...")[0], caja.centery),
                         color, "midleft")
        else:
            estilo.texto(screen, derecha, f, (derecha_x, caja.centery), color, "midright")
        y += alto_caja + int(10 * e)

    # Los controles: cuál está libre, tomado o sin conectar.
    y += int(26 * e)
    n = len(nombres)
    sep = int(14 * e)
    ancho_ficha = min(int(220 * e), (ancho - 60 - sep * (n - 1)) // max(1, n))
    alto_icono = int(ancho_ficha * 0.3)
    alto_ficha = alto_icono + f.get_linesize() + f_chica.get_linesize() + int(34 * e)
    alto_ficha = min(alto_ficha, alto - 70 - y)
    total = n * ancho_ficha + (n - 1) * sep
    x = (ancho - total) // 2
    for esquema, nombre in enumerate(nombres):
        ficha = pygame.Rect(x, y, ancho_ficha, alto_ficha)
        mando = esquema in PUESTOS_CON_MANDO
        if esquema in esquemas:
            dueño = esquemas.index(esquema)
            estado, color = f"Jugador {dueño + 1}", estilo.COLOR_JUGADOR[dueño % 4]
            estilo.tarjeta(screen, ficha, False, color, franja=False)
            pygame.draw.rect(screen, color, ficha, 2, border_radius=12)
        elif esquema in libres:
            estado, color = f"[{_boton_esquema(esquema)}] tomar", estilo.COLOR_PISTA
            estilo.tarjeta(screen, ficha, False, estilo.COLOR_NEON, franja=False)
        else:
            estado, color = "sin conectar", COLOR_TOMADO
            estilo.tarjeta(screen, ficha, False, COLOR_TOMADO, apagada=True, franja=False)
        icono = pygame.Rect(0, 0, int(ancho_ficha * 0.42), alto_icono)
        icono.midtop = (ficha.centerx, ficha.y + int(12 * e))
        tinta = color if esquema in esquemas else ((150, 200, 255) if esquema in libres else (70, 74, 100))
        estilo.icono_control(screen, icono, mando, tinta)
        yy = icono.bottom + int(8 * e)
        estilo.texto(screen, nombre, f, (ficha.centerx, yy), COLOR_TEXTO if esquema in libres or
                     esquema in esquemas else COLOR_TOMADO, "midtop")
        img = render_texto_mando(f_chica, estado, color)
        screen.blit(img, img.get_rect(midtop=(ficha.centerx, yy + f.get_linesize() + 2)))
        x += ancho_ficha + sep

    # El "volver" de cada mando conectado: "B", "Círculo" o "B/Círculo".
    botones = []
    for esquema in PUESTOS_CON_MANDO:
        if esquema < len(conectados) and conectados[esquema]:
            nombre = _boton_esquema(esquema, "volver")
            if nombre not in botones:
                botones.append(nombre)
    estilo.pie(screen, f"[ESC] o {'/'.join(botones) or 'B'}: {volver}", alto - 40, f_chica)


def render_roles(screen, viewports, seleccion, tomados=None, mensaje=None, listo=None):
    """Dibuja la selección de rol de cada jugador en su propia sección.

    `seleccion` es una lista con un dict por jugador: cursor (índice del rol
    sobre el que está), listo (si ya confirmó) y rol (el nombre confirmado);
    "numero" (opcional) es su número de jugador si no es el de la lista.
    En red (cliente.Sesion): `tomados` son los roles ya confirmados por
    TODOS (también los de la otra laptop) y `mensaje` el aviso de arriba.
    """
    from screens import estilo
    estilo.fondo(screen)

    if tomados is None:
        tomados = {s["rol"] for s in seleccion if s["listo"]}
    for indice, vista in enumerate(viewports):
        if indice >= len(seleccion):
            break
        # Solo las secciones pegadas al borde superior ceden espacio al aviso.
        tope = ALTO_AVISO if vista.top < ALTO_AVISO else 0
        _seccion_jugador(screen, vista, seleccion[indice].get("numero", indice), seleccion[indice],
                         tomados - ({seleccion[indice]["rol"]} if seleccion[indice]["listo"] else set()),
                         tope)

    if len(viewports) == 3:
        # El cuarto cuadro: ahí va el panel del equipo en la partida.
        from screens.partida import rect_panel_global
        libre = rect_panel_global(*screen.get_size())
        f_libre = fuente_de_tamano(max(12, min(18, libre.width // 40)))
        estilo.icono_pantalla(screen, pygame.Rect(0, 0, libre.w // 4, libre.h // 4).move(
            libre.centerx - libre.w // 8, libre.centery - libre.h // 6), 3)
        estilo.texto(screen, "Aquí irá el panel del equipo", f_libre,
                     (libre.centerx, libre.centery + libre.h // 8), COLOR_TOMADO, "midtop")

    _separadores(screen, viewports)

    f = fuente_de_tamano(max(13, min(20, screen.get_width() // 80)))
    faltan = sum(1 for s in seleccion if not s["listo"])
    if mensaje is not None:
        color = COLOR_LISTO if listo else COLOR_TENUE
    elif faltan:
        mensaje = f"Faltan {faltan} por elegir" if faltan > 1 else "Falta uno por elegir"
        color = COLOR_TENUE
    else:
        mensaje = "Todos listos. Empezando…"
        color = COLOR_LISTO
    # Arriba y no abajo: con cuatro jugadores el borde inferior lo ocupan las
    # pistas de teclas de los dos de abajo, y el aviso se les montaba encima.
    etiqueta = f.render(mensaje, True, color)
    caja = etiqueta.get_rect(center=(screen.get_width() // 2, ALTO_AVISO // 2))
    pastilla = caja.inflate(32, 10)
    fondo = pygame.Surface(pastilla.size, pygame.SRCALPHA)
    pygame.draw.rect(fondo, (12, 12, 28, 235), fondo.get_rect(), border_radius=pastilla.h // 2)
    screen.blit(fondo, pastilla.topleft)
    pygame.draw.rect(screen, estilo._mezclar(color, (20, 20, 40), 0.4), pastilla, 1, border_radius=pastilla.h // 2)
    screen.blit(etiqueta, caja)


_retratos = {}


def _retrato(rol, alto_max):
    """El personaje del rol, de frente y quieto, recortado y agrandado."""
    clave = (rol, alto_max)
    if clave not in _retratos:
        ruta = os.path.join("Imagenes", "Personajes", rol, f"{rol}_idle_south.png")
        imagen = None
        try:
            hoja = pygame.image.load(ruta).convert_alpha()
            lado = hoja.get_height()
            cuadro = hoja.subsurface((0, 0, min(lado, hoja.get_width()), lado))
            caja = cuadro.get_bounding_rect()
            recorte = cuadro.subsurface(caja).copy()
            escala = max(1, min(3, alto_max // max(1, recorte.get_height())))
            imagen = pygame.transform.scale(recorte, (recorte.get_width() * escala,
                                                      recorte.get_height() * escala))
        except (pygame.error, OSError, ValueError):
            imagen = None
        _retratos[clave] = imagen
    return _retratos[clave]


def _dibujar_retrato(screen, vista, rol, tope, color):
    """El personaje sobre una luz de su color, flotando despacito."""
    from screens import estilo
    from juego import efectos
    imagen = _retrato(rol, max(40, min(190, vista.height // 3)))
    if imagen is None:
        return
    x = vista.right - MARGEN - imagen.get_width()
    y = vista.y + tope + MARGEN + 6
    flota = int(3 * math.sin(pygame.time.get_ticks() / 500)) if efectos.ACTIVOS else 0
    estilo.pedestal(screen, (x + imagen.get_width() // 2, y + imagen.get_height() + 4),
                    int(imagen.get_width() * 0.9), color)
    screen.blit(imagen, (x, y + flota - 4))


def _seccion_jugador(screen, vista, indice, estado, tomados, tope=0):
    from screens import estilo
    f = fuente_de_tamano(max(12, min(20, vista.width // 34)))
    f_titulo = fuente_de_tamano(max(14, min(26, vista.width // 26)))
    paso = f.get_linesize() + 2
    propio = estilo.COLOR_JUGADOR[indice % 4]

    clip_previo = screen.get_clip()
    screen.set_clip(vista)

    y = vista.y + tope + MARGEN
    estilo.texto(screen, f"Jugador {indice + 1}", f_titulo, (vista.x + MARGEN, y),
                 COLOR_LISTO if estado["listo"] else propio)
    y += f_titulo.get_linesize()
    estilo.texto(screen, estado["controles"], f, (vista.x + MARGEN, y), COLOR_TENUE)
    y += paso + 10

    if estado["listo"]:
        _confirmado(screen, vista, f, y, estado)
        rol = next((r for r in ROLES if r["nombre"] == estado["rol"]), None)
        if rol is not None:
            _dibujar_retrato(screen, vista, rol["nombre"], tope, rol["color"])
        screen.set_clip(clip_previo)
        return

    # Las tarjetas dejan libre la columna del retrato.
    sobre_rol = ROLES[estado["cursor"]]
    imagen = _retrato(sobre_rol["nombre"], max(40, min(190, vista.height // 3)))
    derecha = vista.right - MARGEN - ((imagen.get_width() + 16) if imagen is not None else 0)
    ancho_fila = max(160, derecha - (vista.x + MARGEN))
    for i, rol in enumerate(ROLES):
        sobre = (i == estado["cursor"])
        ocupado = rol["nombre"] in tomados
        alto_fila = paso * 2 + 8
        fila = pygame.Rect(vista.x + MARGEN - 6, y - 4, ancho_fila + 12, alto_fila)
        estilo.tarjeta(screen, fila, sobre and not ocupado, rol["color"], apagada=ocupado, radio=10)
        if sobre and ocupado:
            pygame.draw.rect(screen, COLOR_TENUE, fila, 2, border_radius=10)
        if ocupado:
            nombre, color = f"{rol['nombre']} — ya lo tomaron", COLOR_TOMADO
        else:
            nombre, color = rol["nombre"], (rol["color"] if sobre else COLOR_TEXTO)
        estilo.texto(screen, nombre, f, (vista.x + MARGEN + 10, y), color)
        y += paso
        estilo.texto(screen, rol["resumen"], f, (vista.x + MARGEN + 10, y),
                     COLOR_TOMADO if ocupado else COLOR_TENUE)
        y += paso + 12

    _dibujar_retrato(screen, vista, sobre_rol["nombre"], tope, sobre_rol["color"])

    # Con espacio de sobra: el lema, el objetivo y su árbol de habilidades.
    abajo = vista.bottom - MARGEN - f.get_height() - 24
    if abajo - y > paso * 7 + 40:
        justo = int(f.get_linesize() * 3.5) + paso * 2 + 56
        _detalle_rol(screen, pygame.Rect(vista.x + MARGEN - 6, y + 4, vista.width - 2 * MARGEN + 12,
                                         min(abajo - y - 4, justo)), sobre_rol, f,
                     sobre_rol["nombre"] in tomados)

    pie = f"[{estado['tecla_mover']}] elegir   [{estado['tecla_ok']}] confirmar"
    _pie_seccion(screen, vista, pie, f)
    screen.set_clip(clip_previo)


def _detalle_rol(screen, caja, rol, f, ocupado):
    """El panel de abajo: lema, objetivo y el árbol de habilidades del rol
    (la raíz y sus dos hijos, unidos con líneas)."""
    from screens import estilo
    from screens.paneles import partir_lineas
    from data.habilidades import ARBOLES_POR_ROL
    color = rol["color"] if not ocupado else COLOR_TOMADO
    paso = f.get_linesize() + 2
    y = estilo.panel(screen, caja, color, rol["lema"], f)
    for renglon in partir_lineas(rol["objetivo"], f, caja.w - 36)[:2]:
        estilo.texto(screen, renglon, f, (caja.x + 18, y), COLOR_TEXTO)
        y += paso
    arbol = ARBOLES_POR_ROL.get(rol["nombre"])
    if arbol is None or caja.bottom - y < paso * 4:
        return
    y += 8

    def nodo(texto, centro, ancho_max):
        texto = texto if f.size(texto)[0] <= ancho_max - 16 else texto[:max(3, len(texto) * (ancho_max - 16)
                                                                          // max(1, f.size(texto)[0]) - 1)] + "…"
        r = pygame.Rect(0, 0, min(ancho_max, f.size(texto)[0] + 22), f.get_linesize() + 8)
        r.center = centro
        pygame.draw.rect(screen, estilo._mezclar((12, 12, 26), color, 0.22), r, border_radius=r.h // 2)
        pygame.draw.rect(screen, color, r, 1, border_radius=r.h // 2)
        estilo.texto(screen, texto, f, r.center, COLOR_TEXTO, "center", sombra=False)
        return r

    alto_nodo = f.get_linesize() + 8
    raiz = nodo(arbol["nombre"], (caja.centerx, y + alto_nodo // 2), caja.w - 40)
    hijos = arbol.get("hijos", [])
    if not hijos:
        return
    y_hijos = min(caja.bottom - alto_nodo // 2 - 12, raiz.bottom + alto_nodo + 6)
    ancho_hijo = (caja.w - 40) // len(hijos) - 10
    medio = (raiz.bottom + y_hijos - alto_nodo // 2) // 2
    pygame.draw.line(screen, color, raiz.midbottom, (raiz.centerx, medio), 1)
    for i, hijo in enumerate(hijos):
        cx = caja.x + 20 + (ancho_hijo + 10) * i + ancho_hijo // 2 + 5
        pygame.draw.line(screen, color, (raiz.centerx, medio), (cx, medio), 1)
        pygame.draw.line(screen, color, (cx, medio), (cx, y_hijos - alto_nodo // 2), 1)
        nodo(hijo["nombre"], (cx, y_hijos), ancho_hijo)


def _pie_seccion(screen, vista, cadena, f):
    from screens import estilo
    from juego.idioma import tr
    ancho = sum(f.size(trozo)[0] for trozo in tr(cadena).split("[")) + 60
    estilo.pie(screen, cadena, vista.bottom - MARGEN - f.get_height() // 2 - 4, f,
               x=vista.x + MARGEN + ancho // 2)


def _confirmado(screen, vista, f, y, estado):
    from screens import estilo
    paso = f.get_linesize() + 2
    rol = next((r for r in ROLES if r["nombre"] == estado["rol"]), None)
    if rol is None:
        return

    from screens.paneles import partir_lineas
    # El retrato va a la derecha: la caja usa lo que queda, y el objetivo se
    # parte en renglones para que no se salga (antes iba en uno solo).
    imagen = _retrato(rol["nombre"], max(40, min(190, vista.height // 3)))
    libre = vista.right - MARGEN - (imagen.get_width() + 16 if imagen is not None else 0)
    derecha = min(vista.x + int(vista.width * 0.62), libre)
    ancho = max(120, derecha - (vista.x + MARGEN))
    renglones = partir_lineas(rol["objetivo"], f, ancho - 24)
    caja = pygame.Rect(vista.x + MARGEN, y, ancho, paso * (2 + len(renglones)) + 16)
    estilo.tarjeta(screen, caja, False, rol["color"], radio=10)
    pygame.draw.rect(screen, COLOR_LISTO, caja, 2, border_radius=10)

    y += 10
    estilo.texto(screen, rol["nombre"], f, (caja.x + 14, y), rol["color"])
    y += paso
    for renglon in renglones:
        estilo.texto(screen, renglon, f, (caja.x + 14, y), COLOR_TEXTO)
        y += paso
    estilo.texto(screen, "Listo", f, (caja.x + 14, y), COLOR_LISTO)

    _pie_seccion(screen, vista, f"[{estado['tecla_ok']}] cambiar", f)


def _separadores(screen, viewports):
    """Mismo criterio que en la partida: el borde de cada sección, no líneas
    de punta a punta, que con tres jugadores partían en dos la de abajo."""
    from screens.partida import _dibujar_separadores
    _dibujar_separadores(screen, viewports, color=(18, 16, 30), grosor=4)
