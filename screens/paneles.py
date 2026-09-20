"""Paneles que se dibujan DENTRO del viewport de un jugador.

La partida es local y en pantalla dividida, así que una tarea no puede abrirse
como una pantalla que tape todo: mientras el ciudadano lee una publicación, el
candidato tiene que poder seguir caminando por su mitad. Por eso estos paneles
se dibujan recortados al viewport de su dueño y nada más.

Un panel es un diccionario, no una clase: lo arma `App.py` (que es quien sabe
del ABB y de los árboles) y aquí solo se dibuja. Campos que entiende:

    tipo      "opciones" | "resultado" | "habilidades" | "aviso"
    titulo    encabezado del panel
    cuerpo    lista de líneas de texto (se parten solas si no caben)
    opciones  lista de dicts con "texto" y opcionalmente "detalle"/"bloqueada"
    pie       línea de ayuda de teclas
"""

import pygame

from fuentes import fuente_de_tamano


COLOR_FONDO = (22, 24, 42, 238)
COLOR_BORDE = (120, 132, 190)
COLOR_TITULO = (255, 214, 64)
COLOR_TEXTO = (240, 242, 252)
COLOR_TENUE = (168, 176, 214)
COLOR_SELECCION = (255, 214, 64)
COLOR_SELECCION_FONDO = (52, 57, 92)
COLOR_BLOQUEADA = (104, 108, 132)
COLOR_INFO = (245, 170, 120)

MARGEN = 18


def partir_lineas(texto, f, ancho_max):
    """Parte un párrafo en líneas que quepan en `ancho_max`."""
    palabras = texto.split()
    if not palabras:
        return [""]
    lineas, actual = [], palabras[0]
    for palabra in palabras[1:]:
        prueba = actual + " " + palabra
        if f.size(prueba)[0] <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    lineas.append(actual)
    return lineas


def _fuente_para(vista):
    """Tamaño de letra proporcional al viewport.

    Con dos jugadores cada mitad es ancha; con cuatro, cada cuarto es chico y
    el mismo texto no cabe. Se escoge según el ancho disponible.
    """
    px = max(12, min(20, vista.width // 36))
    return fuente_de_tamano(px)


def _maquetar(panel, f, ancho_texto):
    """Reparte el contenido del panel en líneas y devuelve el alto que pide.

    Devuelve (bloques, alto). `bloques` es la lista de líneas ya partidas, que
    se reutiliza al dibujar para no partir el texto dos veces.
    """
    bloques = []
    if panel.get("titulo"):
        bloques.append(("titulo", panel["titulo"]))
    for parrafo in panel.get("cuerpo", []):
        if parrafo == "":
            bloques.append(("espacio", ""))
        else:
            bloques += [("texto", linea) for linea in partir_lineas(parrafo, f, ancho_texto)]

    paso = f.get_linesize() + 2
    opciones = panel.get("opciones", [])
    alto = MARGEN * 2 + len(bloques) * paso
    if opciones:
        alto += paso  # espacio antes de las opciones

    lineas_opcion = []
    for opcion in opciones:
        lineas = partir_lineas(opcion["texto"], f, ancho_texto - 8)
        lineas_opcion.append(lineas)
        alto += paso * len(lineas) + 6
        if opcion.get("detalle"):
            alto += paso
    if panel.get("pie"):
        alto += paso + 6
    return bloques, lineas_opcion, alto


def render_panel(screen, vista, jugador):
    """Dibuja el panel abierto del jugador dentro de su viewport.

    La letra se encoge hasta que el contenido cabe. Antes el alto se recortaba
    con `min(alto, vista.height - 40)` y el sobrante quedaba fuera de la caja,
    tapado por el recorte: en la práctica se perdían opciones sin avisar.
    """
    panel = jugador.panel
    if panel is None:
        return

    ancho = min(int(vista.width * 0.88), 720)
    ancho_texto = ancho - MARGEN * 2
    alto_max = vista.height - 40

    base = _fuente_para(vista)
    f = base
    bloques, lineas_opcion, alto = _maquetar(panel, f, ancho_texto)
    if alto > alto_max:
        for px in range(base.get_height() - 1, 10, -1):
            f = fuente_de_tamano(px)
            bloques, lineas_opcion, alto = _maquetar(panel, f, ancho_texto)
            if alto <= alto_max:
                break

    paso = f.get_linesize() + 2
    caja = pygame.Rect(0, 0, ancho, min(alto, alto_max))
    caja.center = vista.center

    fondo = pygame.Surface(caja.size, pygame.SRCALPHA)
    fondo.fill(COLOR_FONDO)
    screen.blit(fondo, caja.topleft)
    pygame.draw.rect(screen, COLOR_BORDE, caja, 3)

    clip_previo = screen.get_clip()
    screen.set_clip(caja)

    y = caja.y + MARGEN
    for clase, texto in bloques:
        if clase == "titulo":
            screen.blit(f.render(texto, True, COLOR_TITULO), (caja.x + MARGEN, y))
        elif clase == "texto":
            screen.blit(f.render(texto, True, COLOR_TEXTO), (caja.x + MARGEN, y))
        y += paso

    opciones = panel.get("opciones", [])
    if opciones:
        y += paso

    for i, opcion in enumerate(opciones):
        seleccionada = (i == jugador.cursor)
        bloqueada = opcion.get("bloqueada", False)
        lineas = lineas_opcion[i]

        alto_fila = paso * len(lineas) + (paso if opcion.get("detalle") else 0) + 4
        fila = pygame.Rect(caja.x + MARGEN - 6, y - 3, ancho - MARGEN * 2 + 12, alto_fila)
        if seleccionada:
            pygame.draw.rect(screen, COLOR_SELECCION_FONDO, fila)
            pygame.draw.rect(screen, COLOR_SELECCION, fila, 2)

        color = COLOR_BLOQUEADA if bloqueada else (
            COLOR_SELECCION if seleccionada else COLOR_TEXTO)
        for j, linea in enumerate(lineas):
            marca = ("> " if seleccionada else "  ") if j == 0 else "  "
            screen.blit(f.render(marca + linea, True, color), (caja.x + MARGEN, y))
            y += paso

        if opcion.get("detalle"):
            screen.blit(f.render("    " + opcion["detalle"], True, COLOR_TENUE),
                        (caja.x + MARGEN, y))
            y += paso
        y += 6

    if panel.get("pie"):
        pie = f.render(panel["pie"], True, COLOR_TENUE)
        screen.blit(pie, (caja.x + MARGEN, caja.bottom - MARGEN - pie.get_height()))

    screen.set_clip(clip_previo)


def render_hud(screen, vista, jugador, segundos_restantes):
    """Barra superior del viewport: rol, puntos, objetivo y reloj."""
    f = _fuente_para(vista)
    lineas = 3 if jugador.info else 2
    alto_barra = f.get_linesize() * lineas + 14

    barra = pygame.Surface((vista.width, alto_barra), pygame.SRCALPHA)
    barra.fill((14, 15, 28, 205))
    screen.blit(barra, vista.topleft)

    x = vista.x + 12
    y = vista.y + 6
    titulo = f"{jugador.rol}  ·  {jugador.controles_nombre}"
    screen.blit(f.render(titulo, True, COLOR_TEXTO), (x, y))

    puntos = f.render(f"{jugador.puntos} pts", True, COLOR_TITULO)
    screen.blit(puntos, (vista.right - puntos.get_width() - 12, y))

    y += f.get_linesize()
    objetivo = partir_lineas(jugador.objetivo, f, vista.width - 120)[0]
    screen.blit(f.render(objetivo, True, COLOR_TENUE), (x, y))

    reloj = f.render(_formato_reloj(segundos_restantes), True, COLOR_TEXTO)
    screen.blit(reloj, (vista.right - reloj.get_width() - 12, y))

    # Línea propia del rol (el ciudadano ve aquí cuántas cadenas dudosas
    # siguen circulando, según la búsqueda por rango del ABB).
    if jugador.info:
        y += f.get_linesize()
        screen.blit(f.render(jugador.info, True, COLOR_INFO), (x, y))


def _formato_reloj(segundos):
    segundos = max(0, int(segundos))
    return f"{segundos // 60}:{segundos % 60:02d}"


def render_mensaje(screen, vista, jugador):
    """Mensajito flotante de feedback, debajo del HUD."""
    if not jugador.mensaje:
        return
    f = _fuente_para(vista)
    etiqueta = f.render(jugador.mensaje, True, jugador.mensaje_color)
    caja = etiqueta.get_rect()
    caja.centerx = vista.centerx
    caja.y = vista.y + f.get_linesize() * 2 + 24

    fondo = pygame.Surface((caja.width + 20, caja.height + 10), pygame.SRCALPHA)
    fondo.fill((14, 15, 28, 215))
    screen.blit(fondo, (caja.x - 10, caja.y - 5))
    screen.blit(etiqueta, caja.topleft)


def render_pista_zona(screen, vista, jugador):
    """Aviso de 'presiona X para ...' cuando el jugador está sobre una zona."""
    if jugador.zona_cerca is None or jugador.ocupado:
        return
    zona = jugador.zona_cerca
    f = _fuente_para(vista)
    texto = f"[{jugador.nombre_tecla('interactuar')}] {zona['nombre']}"
    etiqueta = f.render(texto, True, COLOR_TITULO)
    caja = etiqueta.get_rect()
    caja.centerx = vista.centerx
    caja.bottom = vista.bottom - 42

    fondo = pygame.Surface((caja.width + 24, caja.height + 12), pygame.SRCALPHA)
    fondo.fill((14, 15, 28, 225))
    screen.blit(fondo, (caja.x - 12, caja.y - 6))
    pygame.draw.rect(screen, COLOR_BORDE, (caja.x - 12, caja.y - 6,
                                           caja.width + 24, caja.height + 12), 2)
    screen.blit(etiqueta, caja.topleft)
