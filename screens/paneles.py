"""Paneles que se dibujan DENTRO del viewport de un jugador.

La partida es local y en pantalla dividida, así que una tarea no puede abrirse
como una pantalla que tape todo: mientras uno lee una nota o usa una terminal,
los demás tienen que poder seguir caminando por su parte. Por eso estos paneles
se dibujan recortados al viewport de su dueño y nada más.

Un panel es un diccionario, no una clase: lo arma la lógica (juego/app.py, mision.py,
infiltrado.py...) y aquí solo se dibuja. Campos que entiende:

    tipo      "opciones" | "resultado" | "habilidades" | "aviso"
    titulo    encabezado del panel
    cuerpo    lista de líneas de texto (se parten solas si no caben)
    opciones  lista de dicts con "texto" y opcionalmente "detalle"/"bloqueada"
    pie       línea de ayuda de teclas
"""

import math

import pygame

from juego.fuentes import fuente_de_tamano


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
    partes = partir_lineas(jugador.objetivo, f, vista.width - 120)
    objetivo = partes[0] + ("..." if len(partes) > 1 else "")
    screen.blit(f.render(objetivo, True, COLOR_TENUE), (x, y))

    reloj = f.render(_formato_reloj(segundos_restantes), True, COLOR_TEXTO)
    screen.blit(reloj, (vista.right - reloj.get_width() - 12, y))

    # Línea propia del rol: la recarga de su habilidad y cosas así
    # (acciones_rol.linea_de_estado).
    if jugador.info:
        y += f.get_linesize()
        screen.blit(f.render(jugador.info, True, COLOR_INFO), (x, y))


def _formato_reloj(segundos):
    segundos = max(0, int(segundos))
    return f"{segundos // 60}:{segundos % 60:02d}"


def fila_vidas(vista, jugador, tapado=None):
    """La fila de debajo del HUD que comparten los corazones, el mensaje y el
    "Te sigue". Devuelve (rect de los corazones, tamaño de cada corazón).

    `tapado` es lo que ya ocupa esa altura en la pantalla (la barra de
    confianza, arriba al centro): si los corazones caerían debajo, se corren a
    la derecha de ella (pasa en la vista de la derecha cuando juegan 2 o 3)."""
    from entidades.jugador import VIDAS_INICIALES
    f = _fuente_para(vista)
    lineas = 3 if jugador.info else 2
    tam = max(16, min(26, vista.width // 34))
    maximo = getattr(jugador, "vidas_max", VIDAS_INICIALES)
    rect = pygame.Rect(vista.x + 8, vista.y + f.get_linesize() * lineas + 14,
                       maximo * (tam + 6) + 10, tam + 12)
    if tapado is not None and rect.colliderect(tapado):
        rect.left = tapado.right + 10
    return rect, tam


def _tramos_libres(desde, hasta, ocupados):
    """Los pedazos de [desde, hasta] que no tocan ningún (inicio, fin) ocupado."""
    tramos = [(desde, hasta)]
    for a, z in ocupados:
        nuevos = []
        for t0, t1 in tramos:
            if z <= t0 or a >= t1:
                nuevos.append((t0, t1))
                continue
            if a > t0:
                nuevos.append((t0, a))
            if z < t1:
                nuevos.append((z, t1))
        tramos = nuevos
    return tramos


def render_mensaje(screen, vista, jugador, tapado=None):
    """Mensajito flotante de feedback, debajo del HUD."""
    if not jugador.mensaje:
        return
    f = _fuente_para(vista)
    lineas = 3 if jugador.info else 2
    y = vista.y + f.get_linesize() * lineas + 20
    # Esa fila la comparte con los corazones (render_vidas) y, en las vistas
    # de arriba, con la barra de confianza. El mensaje va centrado en el
    # pedazo libre más ancho, achicando un poco la letra si hace falta.
    ocupados = []
    corazones = None
    if getattr(jugador, "vidas", None) is not None:
        corazones, _ = fila_vidas(vista, jugador, tapado)
        ocupados.append((corazones.left - 8, corazones.right + 8))
    fila = pygame.Rect(vista.x + 8, y - 4, vista.width - 16, f.get_height() + 8)
    if tapado is not None and fila.colliderect(tapado):
        ocupados.append((tapado.left - 8, tapado.right + 8))
    t0, t1 = max(_tramos_libres(fila.left, fila.right, ocupados),
                 key=lambda t: t[1] - t[0], default=(fila.left, fila.left))
    disponible = t1 - t0 - 20
    minimo = max(12, f.get_height() - 4)
    for px in range(f.get_height(), minimo - 1, -1):
        etiqueta = fuente_de_tamano(px).render(jugador.mensaje, True, jugador.mensaje_color)
        if etiqueta.get_width() <= disponible:
            caja = etiqueta.get_rect(centerx=(t0 + t1) // 2, centery=y + f.get_height() // 2)
            _caja_mensaje(screen, [etiqueta], caja)
            return
    # No cabe en esa fila: va debajo de los corazones, partido en renglones,
    # y sin meterse debajo de la barra ni del cartel de la IA (que va justo
    # debajo de la barra, al centro).
    y2 = (corazones.bottom if corazones is not None else y + f.get_height()) + 10
    ocupados = []
    if tapado is not None:
        ocupados.append((tapado.left - 40, tapado.right + 40))   # el cartel es más ancho
    t0, t1 = max(_tramos_libres(vista.x + 8, vista.right - 8, ocupados),
                 key=lambda t: t[1] - t[0], default=(vista.x + 8, vista.right - 8))
    renglones = partir_lineas(jugador.mensaje, f, max(80, t1 - t0 - 20))
    imgs = [f.render(r, True, jugador.mensaje_color) for r in renglones]
    caja = pygame.Rect(0, 0, max(i.get_width() for i in imgs), len(imgs) * f.get_linesize())
    caja.midtop = ((t0 + t1) // 2, y2)
    _caja_mensaje(screen, imgs, caja)


def _caja_mensaje(screen, imgs, caja):
    fondo = pygame.Surface((caja.width + 20, caja.height + 10), pygame.SRCALPHA)
    fondo.fill((14, 15, 28, 215))
    screen.blit(fondo, (caja.x - 10, caja.y - 5))
    paso = caja.height // max(1, len(imgs))
    for k, img in enumerate(imgs):
        screen.blit(img, img.get_rect(midtop=(caja.centerx, caja.y + k * paso)))


def render_pista_zona(screen, vista, jugador):
    """Aviso de 'presiona X para ...' sobre una zona, un escondite o adentro."""
    if jugador.ocupado or getattr(jugador, "minijuego", None) is not None:
        return
    tecla = jugador.nombre_tecla('interactuar')
    if getattr(jugador, "preso", None) is not None:
        texto = "Encerrado: espera a que te saquen"
    elif getattr(jugador, "escondido", False):
        texto = f"[{tecla}] Salir del escondite"
    elif getattr(jugador, "pista_mision", None):
        texto = f"[{tecla}] {jugador.pista_mision}"
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
        # Solo los bordes: el centro es transparente y mezclarlo cada cuadro
        # era lo más caro del dibujo (una capa del tamaño de la vista).
        tiras = []
        for r in ((0, 0, ancho, grosor), (0, alto - grosor, ancho, grosor),
                  (0, grosor, grosor, alto - 2 * grosor),
                  (ancho - grosor, grosor, grosor, alto - 2 * grosor)):
            rect = pygame.Rect(r)
            if rect.width > 0 and rect.height > 0:
                tiras.append((capa.subsurface(rect).copy(), rect.topleft))
        _cache_vineta[tamano] = tiras
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
    for tira, (dx, dy) in _vineta(vista.size):
        tira.set_alpha(alfa)
        screen.blit(tira, (vista.x + dx, vista.y + dy))


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


# -- Vidas -------------------------------------------------------------------------

COLOR_VIDA = (236, 64, 82)
COLOR_VIDA_VACIA = (60, 40, 52)


def dibujar_corazon(screen, centro, tam, lleno, color=COLOR_VIDA):
    """Un corazón de `tam` px de ancho: dos círculos y un triángulo."""
    cx, cy = centro
    r = max(2, tam // 4)
    relleno = color if lleno else COLOR_VIDA_VACIA
    for dx in (-r, r):
        pygame.draw.circle(screen, relleno, (cx + dx, cy - r // 2), r)
    pygame.draw.polygon(screen, relleno, [(cx - 2 * r, cy - r // 3), (cx + 2 * r, cy - r // 3),
                                          (cx, cy + int(r * 1.9))])
    borde = (255, 230, 235) if lleno else (120, 90, 100)
    # Contorno: los dos lóbulos y la punta.
    pygame.draw.arc(screen, borde, (cx - 2 * r, cy - r // 2 - r, 2 * r, 2 * r), 0.3, 3.4, 1)
    pygame.draw.arc(screen, borde, (cx, cy - r // 2 - r, 2 * r, 2 * r), -0.3, 2.85, 1)
    pygame.draw.line(screen, borde, (cx - 2 * r, cy - r // 3), (cx, cy + int(r * 1.9)), 1)
    pygame.draw.line(screen, borde, (cx + 2 * r, cy - r // 3), (cx, cy + int(r * 1.9)), 1)
    if lleno:
        pygame.draw.circle(screen, (255, 200, 210), (cx - r, cy - r), max(1, r // 3))


def render_vidas(screen, vista, jugador, tapado=None):
    """Las vidas del jugador: corazones arriba a la izquierda, debajo del HUD
    (a la derecha de la barra de confianza si caerían debajo de ella). El que
    se acaba de perder (o de recuperar) parpadea un momento."""
    from entidades.jugador import VIDAS_INICIALES
    vidas = getattr(jugador, "vidas", None)
    if vidas is None:
        return
    rect, tam = fila_vidas(vista, jugador, tapado)
    fondo = pygame.Surface(rect.size, pygame.SRCALPHA)
    fondo.fill((14, 15, 28, 170))
    screen.blit(fondo, rect.topleft)
    x = rect.x + 6 + tam // 2
    y = rect.centery
    parpadeo = getattr(jugador, "vida_cambio_ms", 0) > 0 and (pygame.time.get_ticks() // 120) % 2
    for i in range(getattr(jugador, "vidas_max", VIDAS_INICIALES)):
        lleno = i < vidas
        if parpadeo and i == vidas:      # el que se acaba de perder
            dibujar_corazon(screen, (x + i * (tam + 6), y), tam, True, (255, 240, 240))
            continue
        dibujar_corazon(screen, (x + i * (tam + 6), y), tam, lleno)


def render_eliminado(screen, vista, jugador):
    """Si el jugador ya no tiene vidas, su mitad de la pantalla lo dice."""
    if not getattr(jugador, "eliminado", False):
        return
    capa = pygame.Surface(vista.size, pygame.SRCALPHA)
    capa.fill((20, 6, 10, 170))
    screen.blit(capa, vista.topleft)
    f = _fuente_para(vista)
    from juego.fuentes import fuente_de_tamano
    grande = fuente_de_tamano(max(24, min(48, vista.width // 14)))
    titulo = grande.render("ELIMINADO", True, COLOR_VIDA)
    screen.blit(titulo, titulo.get_rect(center=(vista.centerx, vista.centery - grande.get_linesize())))
    for i, (texto, color) in enumerate((("Te atraparon 3 veces.", COLOR_TEXTO),
                                         ("Tus compañeros siguen: ¡ánimo desde afuera!", COLOR_TENUE))):
        img = f.render(texto, True, color)
        screen.blit(img, img.get_rect(center=(vista.centerx, vista.centery + i * (f.get_linesize() + 6))))


# -- Inventario ------------------------------------------------------------------------

def _icono_objeto(screen, tipo, centro, tam):
    """Dibujitos de los objetos: pieza (engranaje), decodificador (chip) y kit
    (llave inglesa)."""
    from screens.mision_dibujo import COLOR_CONSUMIBLE
    cx, cy = centro
    if tipo == "pieza":
        color = (255, 170, 50)
        for i in range(6):
            a = i * math.pi / 3
            pygame.draw.circle(screen, color, (int(cx + math.cos(a) * tam * 0.32),
                                               int(cy + math.sin(a) * tam * 0.32)), max(2, tam // 7))
        pygame.draw.circle(screen, color, (cx, cy), int(tam * 0.3))
        pygame.draw.circle(screen, (40, 30, 10), (cx, cy), max(2, tam // 8))
    elif tipo == "decodificador":
        color = COLOR_CONSUMIBLE["decodificador"]
        chip = pygame.Rect(0, 0, int(tam * 0.6), int(tam * 0.6))
        chip.center = centro
        for i in range(3):
            x = chip.x + 3 + i * (chip.width - 6) // 2
            pygame.draw.line(screen, color, (x, chip.y - 4), (x, chip.bottom + 3), 2)
            y = chip.y + 3 + i * (chip.height - 6) // 2
            pygame.draw.line(screen, color, (chip.x - 4, y), (chip.right + 3, y), 2)
        pygame.draw.rect(screen, (24, 30, 50), chip)
        pygame.draw.rect(screen, color, chip, 2)
    elif tipo == "kit":
        color = COLOR_CONSUMIBLE["kit"]
        caja = pygame.Rect(0, 0, int(tam * 0.8), int(tam * 0.55))
        caja.midbottom = (cx, cy + tam // 3)
        pygame.draw.rect(screen, color, caja, border_radius=3)
        asa = pygame.Rect(0, 0, int(tam * 0.36), int(tam * 0.3))
        asa.midbottom = (cx, caja.y + 2)
        pygame.draw.rect(screen, color, asa, 2, border_radius=3)
        pygame.draw.line(screen, (30, 60, 40), (caja.x + 3, caja.centery), (caja.right - 4, caja.centery), 2)
    elif tipo.startswith("prueba_"):
        from screens.infiltrado_dibujo import icono_prueba
        icono_prueba(screen, tipo, centro, tam)


NOMBRE_OBJETO = {"pieza": ("Pieza", "Piezas"),
                 "decodificador": ("Decodificador", "Decodificadores"),
                 "kit": ("Kit de herramientas", "Kits de herramientas"),
                 # Las pruebas del infiltrado (data/infiltrado.py).
                 "prueba_audio": ("Audio interceptado", "Audios interceptados"),
                 "prueba_expediente": ("Expediente", "Expedientes"),
                 "prueba_captura": ("Captura de cámara", "Capturas de cámara")}


def render_inventario(screen, vista, jugador):
    """Lo que lleva el jugador, en un cuadrito abajo a la derecha de su vista:
    una fila por objeto, con su dibujito y "x3 Piezas"."""
    if getattr(jugador, "eliminado", False):
        return
    objetos = []
    if getattr(jugador, "piezas", 0) > 0:
        objetos.append(("pieza", jugador.piezas))
    inventario = getattr(jugador, "objetos", {})
    for tipo in ("decodificador", "kit", "prueba_audio", "prueba_expediente", "prueba_captura"):
        cantidad = inventario.get(tipo, 0) if hasattr(inventario, "get") else int(tipo in inventario)
        if cantidad > 0:
            objetos.append((tipo, cantidad))
    f = fuente_de_tamano(max(11, min(15, vista.width // 60)))
    tam = max(18, min(26, vista.width // 40))
    titulo = f.render("Inventario", True, COLOR_TENUE)
    textos = [f.render(f"x{n} {NOMBRE_OBJETO[t][n > 1]}", True, COLOR_TEXTO) for t, n in objetos]
    ancho = max([titulo.get_width()] + [tam + 8 + t.get_width() for t in textos] + [80]) + 16
    fila = max(tam, f.get_linesize()) + 4
    alto = titulo.get_height() + 10 + max(1, len(objetos)) * fila
    caja = pygame.Rect(0, 0, ancho, alto)
    margen_abajo = 12
    if vista.bottom >= screen.get_height() - 2:
        margen_abajo = 40        # deja libre la línea de teclas de abajo
    caja.bottomright = (vista.right - 12, vista.bottom - margen_abajo)
    fondo = pygame.Surface(caja.size, pygame.SRCALPHA)
    fondo.fill((14, 15, 28, 205))
    screen.blit(fondo, caja.topleft)
    pygame.draw.rect(screen, (70, 76, 110), caja, 1, border_radius=4)
    screen.blit(titulo, (caja.x + 8, caja.y + 4))
    y = caja.y + titulo.get_height() + 8
    if not objetos:
        vacio = f.render("vacío", True, (110, 116, 150))
        screen.blit(vacio, (caja.x + 8, y))
        return
    for (tipo, _), texto in zip(objetos, textos):
        centro = (caja.x + 8 + tam // 2, y + fila // 2)
        _icono_objeto(screen, tipo, centro, tam)
        screen.blit(texto, (caja.x + 8 + tam + 8, y + (fila - texto.get_height()) // 2))
        y += fila
