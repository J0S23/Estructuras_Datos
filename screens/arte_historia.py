"""El arte de la historia de los niños: los niños, sus cápsulas de cristal y
las imágenes que el equipo vaya mandando.

Todo se dibuja en pixel art chiquito (como los sprites de PixelLab) y se
agranda con nearest: así combina con el mapa y los personajes. Si existe
una imagen en Imagenes/Historia/ con el nombre que se pide, se usa esa en vez
del dibujo (ver `imagen`): para cambiar un dibujo por el de Anny basta con
poner el archivo ahí (la lista de nombres está en Imagenes/Historia/LEEME.md).
"""

import math
import os
import random

import pygame

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(_RAIZ, "Imagenes", "Historia")
_cache = {}


def _guardar(clave, armar):
    img = _cache.get(clave)
    if img is None and clave not in _cache:
        if len(_cache) > 220:
            _cache.clear()
        img = _cache[clave] = armar()
    return img


def imagen(nombre, alto=None, ancho=None):
    """Imagenes/Historia/<nombre>.png (recortada a lo que tiene dibujo y
    escalada con nearest a `alto` o `ancho`), o None si no está."""
    def armar():
        ruta = os.path.join(CARPETA, nombre + ".png")
        if not os.path.isfile(ruta) or pygame.display.get_surface() is None:
            return None
        try:
            img = pygame.image.load(ruta).convert_alpha()
        except pygame.error:
            return None
        caja = img.get_bounding_rect()
        if caja.width and caja.height:
            img = img.subsurface(caja).copy()
        if alto:
            img = pygame.transform.scale(img, (max(1, round(img.get_width() * alto / img.get_height())), int(alto)))
        elif ancho:
            img = pygame.transform.scale(img, (int(ancho), max(1, round(img.get_height() * ancho / img.get_width()))))
        return img
    return _guardar(("img", nombre, alto, ancho), armar)


def hay(nombre):
    return os.path.isfile(os.path.join(CARPETA, nombre + ".png"))


def oscurecer(color, k):
    return tuple(max(0, min(255, int(c * k))) for c in color[:3])


# -- Los niños ----------------------------------------------------------------------------
# Cada uno: piel, pelo (color y peinado), ropa de arriba y de abajo, y algo
# suyo. El 0 es la niña de la cinemática (pijama morado, con el celular).
NINOS = [
    {"piel": (198, 140, 104), "pelo": (44, 30, 32), "peinado": "largo", "arriba": (150, 96, 200),
     "abajo": (120, 74, 170), "patron": "estrellas", "extra": "celular"},
    {"piel": (232, 186, 150), "pelo": (96, 62, 38), "peinado": "corto", "arriba": (236, 236, 240),
     "abajo": (40, 52, 96), "extra": "corbata"},
    {"piel": (240, 204, 172), "pelo": (226, 194, 104), "peinado": "coletas", "arriba": (236, 120, 160),
     "abajo": (70, 80, 130)},
    {"piel": (122, 82, 56), "pelo": (24, 18, 18), "peinado": "rizado", "arriba": (80, 170, 110),
     "abajo": (60, 84, 140)},
    {"piel": (176, 118, 86), "pelo": (30, 22, 24), "peinado": "trenzas", "arriba": (236, 236, 240),
     "abajo": (120, 40, 52), "falda": True},
    {"piel": (230, 182, 150), "pelo": (150, 104, 60), "peinado": "rapado", "arriba": (110, 150, 220),
     "abajo": (110, 150, 220), "patron": "rayas"},
    {"piel": (240, 196, 168), "pelo": (184, 82, 42), "peinado": "bob", "arriba": (232, 140, 60),
     "abajo": (70, 64, 90), "extra": "pecas"},
    {"piel": (156, 104, 72), "pelo": (28, 22, 22), "peinado": "corto", "arriba": (246, 206, 48),
     "abajo": (40, 70, 160), "extra": "camiseta"},
    {"piel": (212, 160, 122), "pelo": (60, 40, 30), "peinado": "corto", "arriba": (96, 168, 90),
     "abajo": (96, 168, 90), "patron": "puntos", "bajito": True},
    {"piel": (112, 72, 52), "pelo": (70, 44, 30), "peinado": "largo", "arriba": (236, 236, 240),
     "abajo": (180, 40, 50), "falda": True},
]
ANCHO_NINO, ALTO_NINO = 15, 30
CONTORNO = (22, 22, 32)


def nino(i, despierto=False, mira="frente"):
    """El niño `i` (de NINOS) en pixel art, 15x30, con los ojos cerrados
    (dormido en su cápsula) o abiertos. Imagenes/Historia/nino_<i>.png lo
    reemplaza."""
    propia = imagen(f"nino_{i}")
    if propia is not None:
        return propia
    return _guardar(("nino", i, despierto, mira), lambda: _armar_nino(NINOS[i % len(NINOS)], despierto))


def _armar_nino(d, despierto):
    s = pygame.Surface((ANCHO_NINO, ALTO_NINO), pygame.SRCALPHA)
    piel, pelo, arriba, abajo = d["piel"], d["pelo"], d["arriba"], d["abajo"]
    sombra_piel = oscurecer(piel, 0.82)
    baja = 2 if d.get("bajito") else 0
    px = s.set_at

    def rect(color, x, y, w, h):
        pygame.draw.rect(s, color, (x, y + baja, w, h))

    peinado = d.get("peinado")
    # Pelo de atrás (largo: cae hasta los hombros; flota un poco).
    if peinado in ("largo", "trenzas"):
        rect(pelo, 3, 3, 9, 10)
        if peinado == "trenzas":
            rect(pelo, 2, 9, 2, 7)
            rect(pelo, 11, 9, 2, 7)
            rect(oscurecer(pelo, 1.5), 2, 15, 2, 1)
            rect(oscurecer(pelo, 1.5), 11, 15, 2, 1)
    if peinado == "coletas":
        rect(pelo, 1, 3, 2, 5)
        rect(pelo, 12, 3, 2, 5)
    # Cabeza.
    rect(piel, 4, 3, 7, 7)
    rect(piel, 3, 4, 9, 5)
    rect(sombra_piel, 10, 5, 2, 4)
    # Pelo de arriba.
    if peinado == "rapado":
        rect(oscurecer(pelo, 0.9), 4, 2, 7, 2)
    elif peinado == "rizado":
        for x, y in ((3, 2), (5, 1), (7, 1), (9, 1), (11, 2), (3, 4), (11, 4), (4, 1), (10, 1)):
            rect(pelo, x, y, 2, 2)
        rect(pelo, 4, 2, 7, 2)
    else:
        rect(pelo, 4, 1, 7, 3)
        rect(pelo, 3, 2, 9, 2)
        if peinado == "bob":
            rect(pelo, 3, 3, 2, 6)
            rect(pelo, 10, 3, 2, 6)
        elif peinado in ("largo", "trenzas"):
            rect(pelo, 3, 3, 2, 4)
            rect(pelo, 10, 3, 2, 4)
        else:
            rect(pelo, 3, 3, 1, 2)
            rect(pelo, 11, 3, 1, 2)
        rect(oscurecer(pelo, 1.35), 5, 1, 3, 1)          # brillo del pelo
    # Cara: ojos (cerrados: rayitas), boca.
    ojo = (40, 30, 34)
    if despierto:
        px((5, 6 + baja), ojo)
        px((9, 6 + baja), ojo)
        px((5, 5 + baja), (250, 250, 250))
        px((9, 5 + baja), (250, 250, 250))
    else:
        rect(ojo, 5, 6, 2, 1)
        rect(ojo, 8, 6, 2, 1)
    px((7, 8 + baja), oscurecer(piel, 0.62))
    if d.get("extra") == "pecas":
        px((4, 7 + baja), oscurecer(piel, 0.75))
        px((10, 7 + baja), oscurecer(piel, 0.75))
    # Cuello y cuerpo.
    rect(sombra_piel, 6, 10, 3, 1)
    rect(arriba, 4, 11, 7, 8)
    rect(oscurecer(arriba, 0.82), 9, 11, 2, 8)
    # Brazos (flotando, un poco separados) y manos.
    rect(arriba, 2, 11, 2, 6)
    rect(arriba, 11, 11, 2, 6)
    rect(oscurecer(arriba, 0.8), 12, 11, 1, 6)
    rect(piel, 2, 17, 2, 2)
    rect(piel, 11, 17, 2, 2)
    patron = d.get("patron")
    if patron == "estrellas":
        for x, y in ((5, 12), (8, 14), (5, 16), (9, 17), (2, 13)):
            px((x, y + baja), (250, 236, 150))
    elif patron == "rayas":
        for y in (12, 14, 16, 18):
            rect((240, 240, 248), 4, y, 7, 1)
            rect((240, 240, 248), 2, y, 2, 1)
            rect((240, 240, 248), 11, y, 2, 1)
    elif patron == "puntos":
        for x, y in ((5, 13), (8, 12), (6, 16), (9, 16)):
            px((x, y + baja), (60, 110, 60))
    extra = d.get("extra")
    if extra == "corbata":
        rect((190, 40, 50), 7, 11, 1, 5)
    if extra == "camiseta":
        rect((40, 70, 160), 4, 11, 7, 1)          # el cuello azul de la camiseta
        rect((200, 40, 50), 7, 14, 1, 1)
    # Abajo: falda o pantalón, piernas y zapatos.
    if d.get("falda"):
        rect(abajo, 4, 19, 7, 3)
        rect(oscurecer(abajo, 0.8), 9, 19, 2, 3)
        rect(piel, 5, 22, 2, 4)
        rect(piel, 8, 22, 2, 4)
        rect((236, 236, 240), 5, 25, 2, 2)
        rect((236, 236, 240), 8, 25, 2, 2)
    else:
        rect(abajo, 4, 19, 3, 7)
        rect(abajo, 8, 19, 3, 7)
        rect(oscurecer(abajo, 0.8), 10, 19, 1, 7)
    rect((50, 44, 52), 4, 26, 3, 2)
    rect((50, 44, 52), 8, 26, 3, 2)
    if extra == "celular":
        # El celular en la mano (la pantalla todavía prendida).
        rect((30, 30, 40), 12, 16, 3, 4)
        rect((150, 220, 255), 13, 17, 1, 2)
    # Contorno oscuro, como los sprites del juego.
    mascara = pygame.mask.from_surface(s)
    contorno = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    for x in range(ANCHO_NINO):
        for y in range(ALTO_NINO):
            if mascara.get_at((x, y)):
                continue
            if any(0 <= x + dx < ANCHO_NINO and 0 <= y + dy < ALTO_NINO and mascara.get_at((x + dx, y + dy))
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                contorno.set_at((x, y), (*CONTORNO, 255))
    contorno.blit(s, (0, 0))
    return contorno


def nino_grande(i, escala, despierto=False):
    base = nino(i, despierto)
    return _guardar(("nino_g", i, escala, despierto, id(base)),
                    lambda: pygame.transform.scale(base, (int(base.get_width() * escala),
                                                          int(base.get_height() * escala))))


# -- La cápsula de cristal -----------------------------------------------------------------
# Sale de la "cápsula de energía" de Anny (Imagenes/Objetos/OBJ-039): su tapa
# de arriba y la de abajo, con el vidrio estirado para que quepa un niño y
# el líquido de color verde (la luz verde de la cinemática).
ARCHIVO_CAPSULA = "OBJ-039_Capsula_de_energia.png"
CIAN = (51, 191, 224)
BLANCO_RAYO = (232, 234, 231)
VERDE = (78, 214, 128)
FILA_VIDRIO = 30         # la fila de la hoja (ya recortada) que se repite
ESTIRAR = 22             # cuántas filas de vidrio se agregan


def _base_capsula():
    def armar():
        ruta = os.path.join(_RAIZ, "Imagenes", "Objetos", ARCHIVO_CAPSULA)
        if not os.path.isfile(ruta) or pygame.display.get_surface() is None:
            return None
        hoja = pygame.image.load(ruta).convert_alpha()
        hoja = hoja.subsurface(hoja.get_bounding_rect()).copy()
        w, h = hoja.get_size()
        alto = h + ESTIRAR
        s = pygame.Surface((w, alto), pygame.SRCALPHA)
        s.blit(hoja, (0, 0), pygame.Rect(0, 0, w, FILA_VIDRIO))
        fila = hoja.subsurface(pygame.Rect(0, FILA_VIDRIO, w, 1)).copy()
        for k in range(ESTIRAR + 1):
            s.blit(fila, (0, FILA_VIDRIO + k))
        s.blit(hoja, (0, FILA_VIDRIO + ESTIRAR + 1), pygame.Rect(0, FILA_VIDRIO + 1, w, h - FILA_VIDRIO - 1))
        # El rayo blanco del vidrio y el cian, a verde (con el borde más oscuro).
        vidrio = pygame.mask.Mask((w, alto))
        for x in range(w):
            for y in range(alto):
                c = s.get_at((x, y))
                if c.a == 0:
                    continue
                rgb = (c.r, c.g, c.b)
                if rgb == BLANCO_RAYO and FILA_VIDRIO - 10 < y < FILA_VIDRIO + ESTIRAR + 16:
                    rgb = CIAN
                if rgb == CIAN:
                    s.set_at((x, y), (*VERDE, 255))
                    vidrio.set_at((x, y))
        return s, vidrio
    return _guardar(("capsula_base",), armar)


def capsula(i, escala, apagada=False):
    """La cápsula con el niño `i` adentro, a `escala` (px del mundo por px).
    Imagenes/Historia/capsula.png (vacía, con el vidrio transparente)
    reemplaza la de Anny estirada. None si no hay ni una ni otra.
    `apagada`: sin luz (el líquido turbio y oscuro, el niño casi no se ve;
    Imagenes/Historia/capsula_apagada.png la reemplaza si el equipo la manda)."""
    if apagada:
        return _guardar(("capsula_apagada", i, escala), lambda: _apagar(capsula(i, escala), i))

    def armar():
        propia = imagen("capsula")
        if propia is not None:
            s = propia.copy()
            vidrio = None
        else:
            base = _base_capsula()
            if base is None:
                return None
            s, vidrio = base[0].copy(), base[1]
        w, h = s.get_size()
        # El niño, flotando en el centro del vidrio.
        chico = nino(i)
        if vidrio is not None:
            caja = vidrio.get_bounding_rects()
            caja = max(caja, key=lambda r: r.width * r.height) if caja else pygame.Rect(9, 22, 22, 44)
        else:
            caja = pygame.Rect(int(w * 0.22), int(h * 0.3), int(w * 0.56), int(h * 0.5))
        destino = chico.get_rect(center=(caja.centerx, caja.centery + 1))
        capa = pygame.Surface((w, h), pygame.SRCALPHA)
        capa.blit(chico, destino)
        if vidrio is not None:
            # Solo se ve a través del vidrio.
            recorte = vidrio.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
            capa.blit(recorte, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        capa.fill((176, 255, 204, 228), special_flags=pygame.BLEND_RGBA_MULT)   # bajo el líquido
        s.blit(capa, (0, 0))
        if vidrio is not None:
            # Brillo del vidrio (a la izquierda) y sombra (a la derecha).
            for y in range(caja.top + 2, caja.bottom - 2):
                for x, color in ((caja.left + 2, (210, 255, 225, 150)), (caja.left + 3, (210, 255, 225, 90)),
                                 (caja.right - 2, (10, 60, 40, 120))):
                    if vidrio.get_at((x, y)):
                        s.set_at((x, y), _sobre(s.get_at((x, y)), color))
        return pygame.transform.scale(s, (int(w * escala), int(h * escala)))
    return _guardar(("capsula", i, escala), armar)


def _apagar(img, i):
    """La misma cápsula, sin luz: todo lo verde (el líquido, la luz de
    arriba) se vuelve gris oscuro y turbio, y lo de adentro casi no se ve."""
    if img is None:
        return None
    propia = imagen("capsula_apagada")
    if propia is not None:
        return pygame.transform.scale(propia, img.get_size())
    s = img.copy()
    w, h = s.get_size()
    azar = random.Random(i * 31 + 7)
    vidrio = vidrio_de_capsula_px(img)
    for x in range(w):
        for y in range(h):
            c = s.get_at((x, y))
            if c.a == 0:
                continue
            if c.g > c.r + 30 and c.g > c.b + 10:
                # Lo que era verde: gris verdoso, oscuro (más arriba, más oscuro).
                v = 0.22 + 0.14 * (c.g / 255)
                s.set_at((x, y), (int(46 * v + 18), int(60 * v + 20), int(58 * v + 20), c.a))
            elif vidrio is not None and vidrio.collidepoint(x, y):
                # El niño, adentro: apenas una sombra.
                gris = (c.r + c.g + c.b) // 3
                s.set_at((x, y), (gris // 4 + 16, gris // 4 + 20, gris // 4 + 20, c.a))
    if vidrio is not None:
        # Condensación: rayitas claras que bajan por el vidrio.
        for _ in range(max(3, vidrio.width // 7)):
            x = azar.randint(vidrio.left + 2, vidrio.right - 3)
            y0 = azar.randint(vidrio.top, vidrio.bottom - 8)
            for y in range(y0, min(vidrio.bottom, y0 + azar.randint(6, 22))):
                c = s.get_at((x, y))
                s.set_at((x, y), (min(255, c.r + 22), min(255, c.g + 26), min(255, c.b + 26), c.a))
    return s


def vidrio_de_capsula_px(img):
    """El rect del vidrio en `img` (una cápsula ya escalada)."""
    base = _base_capsula()
    if base is None:
        return None
    rects = base[1].get_bounding_rects()
    if not rects:
        return None
    r = max(rects, key=lambda q: q.width * q.height)
    k = img.get_width() / max(1, base[0].get_width())
    return pygame.Rect(int(r.x * k), int(r.y * k), int(r.width * k), int(r.height * k))


def vidrio_de_capsula(escala):
    """El rect del vidrio (en px de la cápsula ya escalada), para las burbujas."""
    def armar():
        base = _base_capsula()
        if base is None:
            return None
        rects = base[1].get_bounding_rects()
        if not rects:
            return None
        r = max(rects, key=lambda q: q.width * q.height)
        return pygame.Rect(int(r.x * escala), int(r.y * escala), int(r.width * escala), int(r.height * escala))
    return _guardar(("vidrio", escala), armar)


def _sobre(fondo, color):
    a = color[3] / 255
    return (int(fondo.r * (1 - a) + color[0] * a), int(fondo.g * (1 - a) + color[1] * a),
            int(fondo.b * (1 - a) + color[2] * a), fondo.a)


def capsula_rota(i, escala):
    """La cápsula `i` con el vidrio reventado: el líquido se fue, adentro
    oscuro y vacío, con picos de vidrio en el borde de arriba y de abajo."""
    def armar():
        img = capsula(i, escala)
        if img is None:
            return None
        s = img.copy()
        v = vidrio_de_capsula_px(img)
        if v is None:
            return s
        azar = random.Random(i * 97 + 5)
        w, h = s.get_size()
        # El borde de arriba y el de abajo, mellados: el vidrio que quedó.
        picos_arriba = [max(1, int(azar.uniform(0.04, 0.3) * v.height)) for _ in range(v.width)]
        picos_abajo = [max(1, int(azar.uniform(0.02, 0.16) * v.height)) for _ in range(v.width)]
        for k in range(1, v.width - 1):          # (que no sean ruido: picos)
            picos_arriba[k] = (picos_arriba[k - 1] + picos_arriba[k] + picos_arriba[k + 1]) // 3
        for x in range(v.left, v.right):
            k = x - v.left
            for y in range(v.top, v.bottom):
                c = s.get_at((x, y))
                if c.a == 0:
                    continue
                if y < v.top + picos_arriba[k] or y >= v.bottom - picos_abajo[k]:
                    # Vidrio: claro, un poco verde.
                    s.set_at((x, y), (150, 210, 190, 200))
                else:
                    # Adentro: oscuro, con un poco de humedad que brilla.
                    hondo = (y - v.top) / max(1, v.height)
                    s.set_at((x, y), (int(14 + 10 * hondo), int(24 + 16 * hondo), int(24 + 12 * hondo), 255))
        # Gotas del líquido que quedan escurriendo.
        for _ in range(max(3, v.width // 6)):
            x = azar.randint(v.left + 2, v.right - 3)
            y0 = azar.randint(v.top + v.height // 3, v.bottom - 6)
            for y in range(y0, min(v.bottom, y0 + azar.randint(3, 9))):
                s.set_at((x, y), (70, 170, 110, 255))
        return s
    return _guardar(("capsula_rota", i, escala), armar)


def grietas(i, golpes, ancho, alto):
    """Las grietas del vidrio tras `golpes` martillazos (líneas desde el punto
    del golpe), en una capa transparente de ancho x alto."""
    def armar():
        capa = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        azar = random.Random(i * 13 + 3)
        for g in range(golpes):
            cx = ancho * azar.uniform(0.3, 0.7)
            cy = alto * azar.uniform(0.3, 0.7)
            for _ in range(5 + 3 * g):
                angulo = azar.uniform(0, 2 * math.pi)
                x, y = cx, cy
                largo = azar.uniform(0.2, 0.55) * max(ancho, alto) * (0.6 + 0.3 * g)
                pasos = 4
                for _ in range(pasos):
                    angulo += azar.uniform(-0.6, 0.6)
                    nx = x + math.cos(angulo) * largo / pasos
                    ny = y + math.sin(angulo) * largo / pasos
                    pygame.draw.line(capa, (235, 255, 245, 220), (x, y), (nx, ny), 2)
                    x, y = nx, ny
            pygame.draw.circle(capa, (255, 255, 255, 230), (int(cx), int(cy)), 3 + g)
        return capa
    return _guardar(("grietas", i, golpes, ancho, alto), armar)


# El martillo del baúl de la prisión (pixel art, 16x16).
MARTILLO_PX = [
    "......KKKKKK....",
    ".....KSSSSSSK...",
    "....KSWWSSSSSK..",
    "....KSSSSSSSSK..",
    "....KDDDDDDDDK..",
    ".....KKKKMKKK...",
    ".........MHK....",
    "........KHHK....",
    ".......KHhK.....",
    "......KHhK......",
    ".....KHhK.......",
    "....KHhK........",
    "...KHhK.........",
    "..KHhK..........",
    "..KGGK..........",
    "...KK...........",
]
COLORES_MARTILLO = {"K": (24, 20, 28), "S": (168, 176, 190), "W": (236, 240, 246), "D": (102, 108, 124),
                    "M": (70, 74, 86), "H": (176, 112, 60), "h": (122, 72, 36), "G": (60, 120, 200)}


def martillo(alto=16):
    """El martillo, a `alto` px (sin suavizar)."""
    def armar():
        propia = imagen("martillo")
        if propia is not None:
            return pygame.transform.scale(propia, (alto, alto))
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        for y, fila in enumerate(MARTILLO_PX):
            for x, c in enumerate(fila):
                if c in COLORES_MARTILLO:
                    s.set_at((x, y), COLORES_MARTILLO[c])
        return pygame.transform.scale(s, (alto, alto))
    return _guardar(("martillo", alto), armar)


# -- Las pistas del Acto 2 -------------------------------------------------------------------

def pista(tipo):
    """La mochila, el zapato o el dibujo, en pixel art (o Imagenes/Historia/<tipo>.png)."""
    propia = imagen(tipo, alto=None)
    if propia is not None:
        return propia
    return _guardar(("pista", tipo), lambda: _armar_pista(tipo))


def _armar_pista(tipo):
    if tipo == "mochila":
        s = pygame.Surface((14, 14), pygame.SRCALPHA)
        rojo, oscuro = (206, 64, 70), (140, 36, 46)
        pygame.draw.rect(s, (30, 26, 34), (2, 1, 10, 13), border_radius=3)
        pygame.draw.rect(s, rojo, (3, 2, 8, 11), border_radius=2)
        pygame.draw.rect(s, oscuro, (9, 3, 2, 9))
        pygame.draw.rect(s, (236, 196, 80), (4, 8, 6, 3))           # bolsillo amarillo
        pygame.draw.rect(s, (30, 26, 34), (4, 8, 6, 3), 1)
        s.set_at((5, 4), (250, 240, 120))                            # llavero
        s.set_at((6, 5), (120, 200, 255))
        pygame.draw.line(s, (30, 26, 34), (5, 0), (8, 0))
        return s
    if tipo == "zapato":
        s = pygame.Surface((12, 7), pygame.SRCALPHA)
        pygame.draw.rect(s, (24, 22, 30), (0, 1, 12, 6), border_radius=2)
        pygame.draw.rect(s, (90, 160, 230), (1, 2, 7, 3))
        pygame.draw.rect(s, (90, 160, 230), (1, 2, 10, 2))
        pygame.draw.rect(s, (240, 240, 244), (1, 5, 10, 1))          # suela
        s.set_at((4, 2), (250, 250, 250))                            # cordones
        s.set_at((6, 2), (250, 250, 250))
        return s
    # El dibujo: una hoja con crayones (la casa, la familia, la luz verde).
    s = pygame.Surface((14, 11), pygame.SRCALPHA)
    pygame.draw.rect(s, (40, 36, 40), (0, 0, 14, 11))
    pygame.draw.rect(s, (246, 242, 230), (1, 1, 12, 9))
    pygame.draw.polygon(s, (220, 70, 60), [(2, 5), (4, 3), (6, 5)])  # techo
    pygame.draw.rect(s, (230, 170, 60), (2, 5, 4, 4))
    for x, c in ((8, (60, 90, 200)), (10, (200, 80, 160)), (12, (60, 90, 200))):
        s.set_at((x, 7), c)
        s.set_at((x, 8), c)
        s.set_at((x, 6), (230, 190, 150))
    pygame.draw.line(s, (80, 220, 120), (10, 1), (8, 5))               # la luz verde
    pygame.draw.line(s, (80, 220, 120), (11, 1), (12, 5))
    s.set_at((11, 1), (60, 200, 90))
    return s
