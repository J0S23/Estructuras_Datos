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
    """Aviso de 'presiona X para ...' sobre una zona, un escondite o adentro."""
    if jugador.ocupado or getattr(jugador, "minijuego", None) is not None:
        return
    tecla = jugador.nombre_tecla('interactuar')
    if getattr(jugador, "escondido", False):
        texto = f"[{tecla}] Salir del escondite"
    elif jugador.zona_cerca is not None:
        texto = f"[{tecla}] {jugador.zona_cerca['nombre']}"
    elif getattr(jugador, "estacion_cerca", None) is not None:
        estacion = jugador.estacion_cerca
        accion = "Usar terminal" if estacion["tipo"] == "terminal" else "Reparar panel"
        texto = f"[{tecla}] {accion}"
    elif getattr(jugador, "escondite_cerca", None) is not None:
        texto = f"[{tecla}] Esconderse"
    else:
        return
    f = _fuente_para(vista)
    etiqueta = f.render(texto, True, COLOR_TITULO)
    caja = etiqueta.get_rect()
    caja.centerx = vista.centerx
    # Bien arriba del borde: abajo a la izquierda va el pulso, y en la mitad
    # inferior de la pantalla también la pista de teclas.
    caja.bottom = vista.bottom - 96

    fondo = pygame.Surface((caja.width + 24, caja.height + 12), pygame.SRCALPHA)
    fondo.fill((14, 15, 28, 225))
    screen.blit(fondo, (caja.x - 12, caja.y - 6))
    pygame.draw.rect(screen, COLOR_BORDE, (caja.x - 12, caja.y - 6,
                                           caja.width + 24, caja.height + 12), 2)
    screen.blit(etiqueta, caja.topleft)


# -- Pulso ----------------------------------------------------------------------

COLOR_PULSO_CALMA = (96, 200, 120)
COLOR_PULSO_ALERTA = (255, 196, 64)
COLOR_PULSO_PANICO = (236, 70, 60)

# El borde rojo del viewport se cachea por tamaño: armarlo cuesta, y el
# tamaño del viewport solo cambia al alternar F11.
_cache_vineta = {}


def _color_pulso(pulso):
    if pulso < 45:
        return COLOR_PULSO_CALMA
    if pulso < 72:
        return COLOR_PULSO_ALERTA
    return COLOR_PULSO_PANICO


def _intensidad_latido(fase):
    """Qué tan "lleno" está el corazón en esta fase del latido (0 a 1).

    Un latido real son dos golpes seguidos (pum-pum) y una pausa; esto lo
    imita con dos picos al principio de cada ciclo.
    """
    if fase < 0.12:
        return 1 - abs(fase - 0.06) / 0.06
    if 0.18 < fase < 0.28:
        return 0.6 * (1 - abs(fase - 0.23) / 0.05)
    return 0.0


def _dibujar_corazon(screen, centro, tamano, color):
    cx, cy = centro
    r = max(3, int(tamano * 0.3))
    pygame.draw.circle(screen, color, (int(cx - r * 0.85), int(cy - r * 0.3)), r)
    pygame.draw.circle(screen, color, (int(cx + r * 0.85), int(cy - r * 0.3)), r)
    pygame.draw.polygon(screen, color, [
        (cx - r * 1.8, cy - r * 0.05),
        (cx + r * 1.8, cy - r * 0.05),
        (cx, cy + r * 1.9),
    ])


def render_pulso(screen, vista, jugador):
    """Corazón que late al ritmo del pulso y la barra, abajo a la izquierda."""
    f = _fuente_para(vista)
    color = _color_pulso(jugador.pulso)
    golpe = _intensidad_latido(jugador.fase_latido)

    ancho_barra = max(110, min(200, vista.width // 5))
    alto_barra = max(10, f.get_linesize() // 2)
    x = vista.x + 16
    base = vista.bottom - 16
    if vista.bottom >= screen.get_height() - 2:
        base -= 26   # deja libre la pista de teclas de abajo de la pantalla

    fondo = pygame.Rect(x - 8, base - alto_barra - f.get_linesize() - 18,
                        ancho_barra + 64, alto_barra + f.get_linesize() + 26)
    capa = pygame.Surface(fondo.size, pygame.SRCALPHA)
    capa.fill((14, 15, 28, 205))
    screen.blit(capa, fondo.topleft)

    tamano = 26 + golpe * 8
    _dibujar_corazon(screen, (x + 16, fondo.centery), tamano, color)

    texto = f.render(f"{jugador.latidos_por_minuto} lpm", True, COLOR_TEXTO)
    screen.blit(texto, (x + 40, fondo.y + 6))

    barra = pygame.Rect(x + 40, base - alto_barra - 2, ancho_barra, alto_barra)
    pygame.draw.rect(screen, (40, 42, 64), barra)
    lleno = barra.copy()
    lleno.width = int(barra.width * jugador.pulso / 100)
    pygame.draw.rect(screen, color, lleno)
    pygame.draw.rect(screen, COLOR_BORDE, barra, 1)

    if jugador.visto:
        aviso = f.render("¡TE VEN!", True, COLOR_PULSO_PANICO)
        screen.blit(aviso, (texto.get_width() + x + 52, fondo.y + 6))


def _vineta(tamano):
    """Borde rojo que se desvanece hacia el centro, para un viewport."""
    if tamano not in _cache_vineta:
        ancho, alto = tamano
        capa = pygame.Surface(tamano, pygame.SRCALPHA)
        grosor = max(24, min(ancho, alto) // 6)
        for i in range(grosor):
            alfa = int(170 * (1 - i / grosor) ** 2)
            pygame.draw.rect(capa, (200, 20, 30, alfa), (i, i, ancho - 2 * i, alto - 2 * i), 1)
        _cache_vineta[tamano] = capa
    return _cache_vineta[tamano]


def render_tension(screen, vista, jugador):
    """Bordes rojos que laten cuando el pulso está alto."""
    if jugador.pulso < 55:
        return
    fuerza = (jugador.pulso - 55) / 45
    golpe = _intensidad_latido(jugador.fase_latido)
    alfa = int(255 * min(1.0, fuerza * (0.55 + 0.45 * golpe)))
    if alfa <= 0:
        return
    capa = _vineta(vista.size)
    capa.set_alpha(alfa)
    screen.blit(capa, vista.topleft)


# -- Escondites y minijuego ---------------------------------------------------------

COLOR_AMENAZA = (236, 70, 60)
COLOR_ZONA_VERDE = (96, 200, 120)
_cache_escondido = {}


def render_escondido(screen, vista, jugador):
    """Adentro del escondite: todo oscuro salvo una rendija a la altura de los ojos."""
    if not getattr(jugador, "escondido", False):
        return
    if vista.size not in _cache_escondido:
        capa = pygame.Surface(vista.size, pygame.SRCALPHA)
        capa.fill((4, 5, 10, 205))
        alto_rendija = max(40, vista.height // 7)
        centro = vista.height // 2
        for i in range(alto_rendija):
            # La rendija se aclara hacia el centro.
            d = abs(i - alto_rendija / 2) / (alto_rendija / 2)
            alfa = int(205 * d ** 2)
            pygame.draw.line(capa, (4, 5, 10, alfa), (0, centro - alto_rendija // 2 + i),
                             (vista.width, centro - alto_rendija // 2 + i))
        _cache_escondido[vista.size] = capa
    screen.blit(_cache_escondido[vista.size], vista.topleft)


def render_minijuego(screen, vista, jugador):
    """La barra de timing y, al lado, la de cuánto le falta al alien para entrar."""
    juego = getattr(jugador, "minijuego", None)
    if juego is None:
        return
    f = _fuente_para(vista)
    ancho = max(260, min(480, vista.width - 60))
    alto = f.get_linesize() * 3 + 74
    panel = pygame.Rect(0, 0, ancho, alto)
    panel.centerx = vista.centerx
    panel.bottom = vista.bottom - 96

    capa = pygame.Surface(panel.size, pygame.SRCALPHA)
    capa.fill(COLOR_FONDO)
    screen.blit(capa, panel.topleft)
    borde = COLOR_BORDE
    if juego.destello_ms > 0:
        borde = COLOR_ZONA_VERDE if juego.destello == "acierto" else COLOR_AMENAZA
    pygame.draw.rect(screen, borde, panel, 3 if juego.destello_ms > 0 else 2)

    titulo = f.render("¡Un alien revisa tu escondite!", True, COLOR_AMENAZA)
    screen.blit(titulo, (panel.x + 14, panel.y + 10))
    tecla = jugador.nombre_tecla("interactuar")
    pista = f.render(f"[{tecla}] cuando la aguja esté en verde", True, COLOR_TEXTO)
    screen.blit(pista, (panel.x + 14, panel.y + 10 + f.get_linesize()))

    # Barra de timing.
    ancho_lateral = 30
    barra = pygame.Rect(panel.x + 14, panel.y + 22 + f.get_linesize() * 2,
                        panel.width - 28 - ancho_lateral - 18, 26)
    pygame.draw.rect(screen, (40, 42, 64), barra)
    inicio, fin = juego.zona
    verde = pygame.Rect(barra.x + int(inicio * barra.width), barra.y,
                        max(2, int((fin - inicio) * barra.width)), barra.height)
    pygame.draw.rect(screen, COLOR_ZONA_VERDE, verde)
    pygame.draw.rect(screen, COLOR_BORDE, barra, 2)
    x_aguja = barra.x + int(juego.aguja * barra.width)
    pygame.draw.rect(screen, (250, 250, 255), (x_aguja - 3, barra.y - 6, 6, barra.height + 12))

    calma = f.render(f"{jugador.latidos_por_minuto} lpm", True, _color_pulso(jugador.pulso))
    screen.blit(calma, (barra.x, barra.bottom + 8))

    # Barra lateral: el alien está por entrar. Se llena de abajo hacia arriba.
    f_chica = fuente_de_tamano(max(10, f.get_height() - 5))
    etiqueta = f_chica.render("ALIEN", True, COLOR_AMENAZA)
    lateral = pygame.Rect(barra.right + 18, panel.y + 12, ancho_lateral,
                          panel.height - 30 - etiqueta.get_height())
    pygame.draw.rect(screen, (40, 42, 64), lateral)
    alto_lleno = int(lateral.height * juego.amenaza / 100)
    lleno = pygame.Rect(lateral.x, lateral.bottom - alto_lleno, lateral.width, alto_lleno)
    pygame.draw.rect(screen, COLOR_AMENAZA, lleno)
    pygame.draw.rect(screen, COLOR_BORDE, lateral, 2)
    screen.blit(etiqueta, (lateral.centerx - etiqueta.get_width() // 2, lateral.bottom + 6))
