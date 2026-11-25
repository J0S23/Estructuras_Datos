"""El dibujo de la sala oculta de los niños (la lógica: misiones/sala_secreta.py).

- La puerta: la del marco dorado de la Bahía. Al abrirse se destraba (tres
  luces que pasan de rojo a verde, una línea que la recorre, el marco que
  brilla), suelta la presión y se parte en dos hacia los lados, con la luz
  verde de adentro saliendo por la rendija (`_puerta`, `_luz_puerta`). La
  pared y el marco se quedan; el pedazo de pared de encima de la puerta
  (`dibujar_dintel`) va delante de los personajes: se pasa por debajo.
- Lo de adentro (el pasillo y la sala) NO se pinta en el mapa: se arma una
  vez aparte (`pintura`, con los colores y baldosas del mapa, las paredes
  unidas en las esquinas) y se dibuja solo en la vista de quien cruzó la
  puerta (`dibujar_revelado`, se aparece a medida que se mete). Desde
  afuera tampoco se ve a los que están adentro (`oculto`).
- `dibujar_piso`: la puerta, las pistas del Acto 2 (mochila, zapato,
  dibujo) con su brillo y el celular del piso de la sala.
- `erguidos`: las cápsulas de cristal con los niños, con su monitor (las
  apagadas, sin luz y con la línea plana; la que se apaga, parpadeando; las
  que rompe el martillo, con grietas y después reventadas), los niños que ya
  sacaron (caminando a la cápsula si ganó "liberar") y el baúl de la prisión
  (su teclado; abierto, con el martillo adentro).
- `dibujar_luces`: la luz verde de las cápsulas, la de la puerta, la del
  Biomante que intenta regenerar y, con la alarma, las balizas rojas.
- `render_vista_alarma`, `render_alarma`, `render_voto`, `render_celular_nino`:
  la alarma (como el gif de la "alerta sísmica" de Campo), el viñeteado rojo
  de cada vista, el menú de la votación y el celular con los mensajes de la
  mamá.

Todo sale del estado de la sala (estado, estado_ms, quedan_ms, votos,
apagadas...): en red el cliente lo dibuja igual.
"""

import math
import random

import pygame

from data.historia import ABRIR_PARED_MS, VOTACION, DESENLACE_MS, CELULAR_NINO, REGENERAR, SE_APAGA
from juego import efectos, cache_dibujo
from juego.fuentes import fuente_de_tamano
from juego.idioma import tr
from screens import arte_historia as arte

# Los colores del mapa (MapaFinal: la Bahía).
PISO = (73, 78, 94)
LINEA_CLARA = (104, 110, 128)
LINEA_OSCURA = (62, 66, 81)
SOMBRAS = [(38, 40, 52), (45, 48, 60), (53, 56, 70), (60, 64, 78)]
NEGRO = (5, 5, 10)
AMARILLO = (188, 165, 119)
MARRON = (109, 103, 87)
OSCURO = (21, 22, 34)
VERDE = (88, 226, 140)
# Las capas de la pared, del borde del piso hacia afuera (21 px = 63 del mundo).
ANILLOS = [NEGRO] + [AMARILLO] * 2 + [MARRON] + [LINEA_CLARA] * 6 + [OSCURO] * 7 + [LINEA_CLARA] * 4 + [NEGRO]
CARA_SALA = 30           # alto de la pared del fondo (px del mapa sin escalar)
CARA_PASILLO = 12
BALDOSA = 20
ESCALA_CAPSULA = 2.5
ESCALA_PISTA = 4

LARGO_HAZ, ANCHO_HAZ, COLOR_HAZ = 300, 96, (120, 18, 14)

# La puerta al abrirse (fracciones de ABRIR_PARED_MS): hasta T_PARTE se
# destraba; de ahí a T_ABIERTA se parte en dos; luego, el destello.
T_PARTE = 0.25
T_ABIERTA = 0.8

_estado_visto = {}       # id(sala) -> (estado, estado_ms visto, ms del último polvo/golpe)
_cache = {}


def _suave(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


# -- Quién ve lo de adentro ---------------------------------------------------------------

def zonas_ocultas(sala):
    """Lo que no se ve desde afuera (px del mundo): los pasillos de arriba
    de la pared y la sala (el primero cruza la pared: lo tapa el dintel)."""
    return list(sala.pasillos[1:]) + [sala.sala]


def revelado(sala, jugador):
    """0..1: cuánto ve `jugador` de lo de adentro. Se va apareciendo
    mientras cruza la puerta (por debajo del dintel) y del todo ya arriba."""
    if (sala is None or not sala.activa or sala.sala is None or jugador is None
            or sala.estado == "cerrada" or not sala.pasillos):
        return 0.0
    c = jugador.hitbox.center
    if any(z.collidepoint(c) for z in zonas_ocultas(sala)):
        return 1.0
    cruce = sala.pasillos[0]
    if cruce.collidepoint(c):
        arranque = sala.puerta.top + 34
        return max(0.0, min(1.0, (arranque - c[1]) / max(1, arranque - cruce.top)))
    return 0.0


def oculto(sala, dueño, rect):
    """¿`rect` (un personaje) está adentro y `dueño` todavía no cruzó?"""
    if sala is None or not sala.activa or sala.sala is None:
        return False
    c = rect.center
    if not any(z.collidepoint(c) for z in zonas_ocultas(sala)):
        return False
    return revelado(sala, dueño) < 0.5


# -- Lo de adentro, pintado aparte (una vez por mundo) ----------------------------------------

def pintura(mundo, sala):
    """(region, imagen, partes): el pasillo y la sala en px del mundo, con
    lo que se pega de la imagen (`partes`, sin tocar la Bahía). False si no
    se pudo armar (el servidor sin pantalla)."""
    hecha = mundo.__dict__.get("_sala_oculta_pintura")
    if hecha is None:
        try:
            hecha = _armar_pintura(mundo, sala)
        except (pygame.error, ImportError, ValueError):
            hecha = False
        mundo.__dict__["_sala_oculta_pintura"] = hecha
    return hecha


def _dilatar(m):
    """Crece la máscara un pixel para todos lados (también en diagonal)."""
    import numpy as np
    p = np.pad(m, 1)
    h, w = m.shape
    salida = np.zeros_like(m)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            salida |= p[dy:dy + h, dx:dx + w]
    return salida


def _armar_pintura(mundo, sala):
    import numpy as np
    from juego.salas_selladas import restar_todos
    from misiones.sala_secreta import no_pintar
    e = mundo.escala
    rects = list(sala.pasillos) + [sala.sala]
    grosor = len(ANILLOS) * e
    region = rects[0].inflate(2 * grosor, 2 * grosor)
    for r in rects[1:]:
        region.union_ip(r.inflate(2 * grosor, 2 * grosor))
    region.y -= CARA_SALA * e
    region.height += CARA_SALA * e
    region = region.clip(pygame.Rect(0, 0, mundo.ancho, mundo.alto))
    region.x -= region.x % e
    region.y -= region.y % e
    w, h = region.width // e, region.height // e
    region.size = (w * e, h * e)
    gx0, gy0 = region.x // e, region.y // e

    def n(rect):                                   # del mundo al lienzo
        return pygame.Rect((rect.x - region.x) // e, (rect.y - region.y) // e,
                           max(1, rect.width // e), max(1, rect.height // e))

    todo = pygame.Rect(0, 0, w, h)
    piso = np.zeros((h, w), bool)
    for r in rects:
        q = n(r).clip(todo)
        piso[q.top:q.bottom, q.left:q.right] = True
    # Las paredes de frente: encima de cada borde de arriba del piso (la de
    # la sala más alta). Por columnas: así las esquinas quedan unidas.
    sala_n = n(sala.sala)
    cara = np.zeros((h, w), bool)
    encima = np.zeros_like(piso)
    encima[1:] = piso[:-1]
    caras = []
    for y0, x in zip(*np.nonzero(piso & ~encima)):
        alto = CARA_SALA if (sala_n.left <= x < sala_n.right and y0 == sala_n.top) else CARA_PASILLO
        y1 = max(0, y0 - alto)
        cara[y1:y0, x] |= ~piso[y1:y0, x]
        caras.append((int(y0), alto, int(x)))
    hueco = piso | cara
    # Cada pixel de pared, a qué distancia está del hueco (los anillos).
    imagen = np.empty((h, w, 3), np.uint8)
    imagen[:] = NEGRO
    actual = hueco.copy()
    for d in range(1, len(ANILLOS) + 1):
        nuevo = _dilatar(actual)
        imagen[nuevo & ~actual] = ANILLOS[d - 1]
        actual = nuevo
    # Adentro del piso: a qué distancia de la pared (la sombra de los bordes).
    adentro = np.zeros((h, w), np.int16)
    actual = ~piso
    for d in range(1, 9):
        nuevo = _dilatar(actual)
        adentro[nuevo & ~actual] = d
        actual = nuevo
    lienzo = pygame.surfarray.make_surface(imagen.swapaxes(0, 1).copy())
    # Las paredes de frente, por tramos seguidos.
    caras.sort()
    tramo = None
    for y0, alto, x in caras + [(None, None, None)]:
        if tramo is not None and (y0, alto) == (tramo[0], tramo[1]) and x == tramo[3] + 1:
            tramo[3] = x
            continue
        if tramo is not None:
            ty, talto, tx0, tx1 = tramo
            r = pygame.Rect(tx0, ty - talto, tx1 - tx0 + 1, talto).clip(todo)
            if r.width > 0 and r.height > 0:
                _cara(lienzo, r, chica=talto < CARA_SALA)
        tramo = [y0, alto, x, x] if y0 is not None else None
    # El piso, en la misma grilla que la Bahía (las baldosas siguen igual).
    gx = np.broadcast_to((np.arange(w) + gx0)[None, :] % BALDOSA, (h, w))
    gy = np.broadcast_to((np.arange(h) + gy0)[:, None] % BALDOSA, (h, w))
    baldosas = np.empty((h, w, 3), np.uint8)
    baldosas[:] = PISO
    baldosas[gx == 0] = LINEA_CLARA
    baldosas[gy == 0] = LINEA_OSCURA
    baldosas[gy == 1] = LINEA_CLARA
    for k, color in enumerate(SOMBRAS):
        baldosas[adentro == k + 1] = color
    capa = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.surfarray.blit_array(capa, baldosas.swapaxes(0, 1).copy())
    alfa = pygame.surfarray.pixels_alpha(capa)
    alfa[:] = np.where(piso, 255, 0).swapaxes(0, 1).astype(np.uint8)
    del alfa
    lienzo.blit(capa, (0, 0))
    # Lucecitas verdes a los lados de los pasillos (como las de Motores), en
    # la misma grilla en los dos tramos: también donde doblan.
    puestas = []
    for r in sala.pasillos:
        q = n(r)
        if q.width >= q.height:
            puntos = [(x, y) for x in range(q.left, q.right) if (x + gx0) % 22 == 10
                      for y in (q.top + 5, q.bottom - 7)]
        else:
            puntos = [(x, y) for y in range(q.top, q.bottom) if (y + gy0) % 22 == 10
                      for x in (q.left + 5, q.right - 7)]
        for x, y in puntos:
            if not (0 <= x < w - 1 and 0 <= y < h - 1) or not piso[y, x]:
                continue
            if adentro[y, x] not in (6, 7) and adentro[y + 1, x + 1] not in (6, 7):
                continue
            if any(abs(x - px) + abs(y - py) < 12 for px, py in puestas):
                continue
            puestas.append((x, y))
            pygame.draw.rect(lienzo, (30, 70, 52), (x - 1, y - 1, 4, 4))
            pygame.draw.rect(lienzo, VERDE, (x, y, 2, 2))
    _detalles_sala(lienzo, sala_n, n(sala.pasillo), [n(c["base"]) for c in sala.capsulas])
    grande = pygame.transform.scale(lienzo, (w * e, h * e))
    if pygame.display.get_surface() is not None:
        grande = grande.convert()
    partes = [p.clip(region) for p in restar_todos([pygame.Rect(region)], no_pintar(mundo))]
    return region, grande, [p for p in partes if p.width > 0 and p.height > 0]


def dibujar_revelado(screen, fondo_offset, camara, sala, dueño):
    """Lo de adentro, en la vista de quien ya cruzó la puerta (encima del mapa)."""
    k = revelado(sala, dueño)
    if k <= 0:
        return
    hecha = pintura(sala.juego.mundo, sala)
    if not hecha:
        return
    region, img, partes = hecha
    if not region.colliderect(camara):
        return
    img.set_alpha(None if k >= 1 else int(255 * k) // 8 * 8)
    for parte in partes:
        vis = parte.clip(camara)
        if vis.width <= 0 or vis.height <= 0:
            continue
        screen.blit(img, (vis.x - fondo_offset[0], vis.y - fondo_offset[1]), vis.move(-region.x, -region.y))
def _cara(lienzo, rect, chica=False):
    """La pared vista de frente (la de arriba del piso): paneles, pantallas
    y tubos con el líquido verde."""
    sub = lienzo.subsurface(rect)
    sub.fill((58, 62, 78))
    for x in range(0, rect.width, 16):
        pygame.draw.line(sub, (44, 47, 60), (x, 0), (x, rect.height))
        pygame.draw.line(sub, (70, 74, 92), (x + 1, 0), (x + 1, rect.height))
    pygame.draw.rect(sub, (38, 40, 52), (0, 0, rect.width, 2))
    pygame.draw.rect(sub, LINEA_CLARA, (0, rect.height - 3, rect.width, 1))
    pygame.draw.rect(sub, AMARILLO, (0, rect.height - 2, rect.width, 1))
    pygame.draw.rect(sub, NEGRO, (0, rect.height - 1, rect.width, 1))
    if chica:
        return
    azar = random.Random(7)
    # Tubos verdes que bajan del techo (a las cápsulas).
    for x in range(12, rect.width - 8, 40):
        pygame.draw.rect(sub, (24, 30, 34), (x - 1, 2, 5, rect.height - 6))
        pygame.draw.rect(sub, (52, 140, 92), (x, 2, 3, rect.height - 6))
        pygame.draw.rect(sub, (130, 240, 170), (x, 2, 1, rect.height - 6))
    # Pantallas: perfiles de NEXUS de los niños, "desactivados".
    for k, x in enumerate(range(26, rect.width - 30, 64)):
        pantalla = pygame.Rect(x, 5, 30, 17)
        pygame.draw.rect(sub, NEGRO, pantalla.inflate(2, 2))
        pygame.draw.rect(sub, (14, 30, 24), pantalla)
        cara = arte.nino(k % len(arte.NINOS))
        mini = pygame.transform.scale(cara.subsurface((2, 0, 11, 11)), (9, 9))
        sub.blit(mini, (pantalla.x + 2, pantalla.y + 2))
        for j in range(3):
            largo = azar.randint(8, 15)
            pygame.draw.line(sub, (60, 150, 100), (pantalla.x + 13, pantalla.y + 4 + j * 3),
                             (pantalla.x + 13 + largo, pantalla.y + 4 + j * 3))
        pygame.draw.line(sub, (210, 70, 70), (pantalla.x + 2, pantalla.bottom - 3),
                         (pantalla.x + 27, pantalla.bottom - 3))          # "perfil eliminado"
    # La máquina del fondo, a la derecha (late con la luz: dibujar_luces).
    maquina = pygame.Rect(rect.width - 26, 3, 20, rect.height - 6)
    pygame.draw.rect(sub, NEGRO, maquina.inflate(2, 2))
    pygame.draw.rect(sub, (40, 44, 56), maquina)
    pygame.draw.rect(sub, (40, 160, 100), maquina.inflate(-8, -8))
    pygame.draw.rect(sub, (150, 255, 190), maquina.inflate(-14, -12))


def _detalles_sala(lienzo, piso, pasillo, bases):
    """Cables de las cápsulas al tronco del medio, la franja de peligro de la
    entrada y el piso un poco más verde bajo cada cápsula."""
    arriba = [b for b in bases if b.bottom < piso.centery]
    abajo = [b for b in bases if b.bottom >= piso.centery]
    medio = ((max(b.bottom for b in arriba) + min(b.top for b in abajo)) // 2
             if arriba and abajo else pasillo.centery)
    for b in bases:
        pygame.draw.ellipse(lienzo, (66, 84, 86), b.inflate(10, 6))
    # El tronco de cables por el medio, de la entrada a la máquina del fondo.
    for dy, color in ((-3, (26, 28, 36)), (-2, (64, 70, 86)), (2, (26, 28, 36)), (3, (64, 70, 86))):
        pygame.draw.line(lienzo, color, (piso.x + 30, medio + dy), (piso.right - 4, medio + dy))
    for b in bases:
        x = b.centerx
        y0 = b.bottom if b.centery < medio else b.top
        destino = medio - 4 if b.centery < medio else medio + 4
        pygame.draw.line(lienzo, (26, 28, 36), (x, y0), (x, destino), 2)
        pygame.draw.line(lienzo, (64, 70, 86), (x - 1, y0), (x - 1, destino))
    # Franja de peligro donde el pasillo entra a la sala.
    franja = pygame.Rect(piso.x - 1, pasillo.y, 5, pasillo.height)
    for y in range(franja.top, franja.bottom):
        for x in range(franja.left, franja.right):
            lienzo.set_at((x, y), (230, 190, 50) if (x + y) // 3 % 2 else (24, 22, 26))




# -- Una vez por cuadro: el polvo, las chispas, los golpes ---------------------------------------

def tick(sala):
    """Lo que se dispara por el estado (en los dos lados de la red): al
    abrirse la puerta, el golpe de la presión, el vapor, las chispas de la
    rendija y el temblor; los golpes de los aliens que llegan."""
    if sala is None or not sala.activa:
        return
    visto, visto_ms, ultimo = _estado_visto.get(id(sala), (None, 0, 0))
    ahora = pygame.time.get_ticks()
    ms = sala.estado_ms
    if sala.estado != visto:
        _estado_visto.clear()
        if sala.estado == "desenlace":
            efectos.golpe(*sala.sala.center, fuerza=12)
        _estado_visto[id(sala)] = (sala.estado, 0 if sala.estado == "abriendo" else ms, ahora)
        if sala.estado != "abriendo":
            return
        visto_ms = -1

    def paso(t):
        return visto_ms < t <= ms

    puerta = sala.puerta
    interior = _interior(puerta)
    if sala.estado == "abriendo":
        parte = ABRIR_PARED_MS * T_PARTE
        abierta = ABRIR_PARED_MS * T_ABIERTA
        if paso(parte * 0.8):
            efectos.golpe(*puerta.center, fuerza=4)
        if paso(parte):
            # Suelta la presión: vapor por abajo y a los lados, y un golpe.
            efectos.golpe(*puerta.center, fuerza=9)
            efectos.polvareda(pygame.Rect(interior.x, interior.bottom - 6, interior.width, 8), 36,
                              color=(196, 214, 210))
            for lado in (interior.left + 6, interior.right - 6):
                efectos.polvareda(pygame.Rect(lado - 6, interior.top, 12, interior.height), 10,
                                  color=(186, 206, 200))
        if parte < ms < abierta and ahora - ultimo > 150:
            k = _suave((ms - parte) / (abierta - parte))
            corre = int(k * (interior.width // 2 + 6))
            for x in (interior.centerx - corre, interior.centerx + corre):
                efectos.chispas(x, interior.top + random.randint(10, interior.height - 10), 3)
            ultimo = ahora
        if paso(abierta):
            efectos.golpe(*puerta.center, fuerza=7)
            efectos.destello(interior.centerx, interior.centery, (120, 255, 170), 26, 1.3)
    elif sala.estado == "votacion" and sala.cerca > 0.75 and ahora - ultimo > 420:
        # Ya casi llegan: retumba el pasillo.
        efectos.golpe(*sala.pasillo.center, fuerza=2 + 5 * sala.cerca)
        ultimo = ahora
    elif sala.estado == "desenlace" and not sala.a_la_capsula and ahora - ultimo > 300:
        efectos.golpe(*sala.sala.center, fuerza=9)
        ultimo = ahora
    _estado_visto[id(sala)] = (sala.estado, ms, ultimo)


# -- La puerta -------------------------------------------------------------------------------

def _interior(puerta):
    """Lo de adentro del marco dorado (la hoja de la puerta)."""
    return pygame.Rect(puerta.x + 6, puerta.y + 6, puerta.width - 15, puerta.height - 16)


def _hoja(mundo, interior):
    """La hoja de la puerta tal como está en el mapa (para partirla)."""
    clave = ("hoja", id(mundo), tuple(interior))
    img = _cache.get(clave)
    if img is None:
        img = _cache[clave] = mundo.imagen.subsurface(interior).copy()
    return img


def _boca(tam):
    """Lo que se ve por la puerta abierta: un pasillo que se mete en la
    oscuridad (el piso en perspectiva, las paredes, y al fondo la luz verde)."""
    clave = ("boca", tuple(tam))
    img = _cache.get(clave)
    if img is None:
        w, h = tam
        img = pygame.Surface((w, h))
        for y in range(h):
            k = y / max(1, h - 1)
            img.fill((int(4 + 10 * k), int(6 + 14 * k), int(10 + 14 * k)), (0, y, w, 1))
        # El piso: un trapecio que se va al fondo, con las juntas de las baldosas.
        fondo_y = int(h * 0.42)
        fondo = (int(w * 0.36), int(w * 0.64))
        for y in range(fondo_y, h):
            k = (y - fondo_y) / max(1, h - fondo_y)
            izq = int(fondo[0] * (1 - k))
            der = int(fondo[1] + (w - fondo[1]) * k)
            c = (int(20 + 40 * k), int(24 + 44 * k), int(32 + 50 * k))
            img.fill(c, (izq, y, max(1, der - izq), 1))
        for j in range(1, 6):                       # juntas de lado (cada vez más juntas)
            k = (j / 6) ** 1.8
            y = int(fondo_y + (h - fondo_y) * k)
            izq = int(fondo[0] * (1 - k))
            der = int(fondo[1] + (w - fondo[1]) * k)
            pygame.draw.line(img, (14, 16, 22), (izq, y), (der, y))
        for j in range(-3, 4):                      # juntas hacia el fondo
            x0 = w // 2 + j * w // 7
            x1 = w // 2 + j * (fondo[1] - fondo[0]) // 7
            pygame.draw.line(img, (16, 18, 24), (x0, h), (x1, fondo_y))
        # Las lucecitas verdes del piso, que se pierden al fondo.
        for j in range(5):
            k = 1 - (j / 5) ** 1.4
            y = int(fondo_y + (h - fondo_y) * k) - 3
            for lado in (-1, 1):
                x = int(w / 2 + lado * (w * 0.14 + (w * 0.36) * k))
                r = max(1, int(3 * k))
                pygame.draw.rect(img, (40, int(110 + 110 * k), 80), (x - r // 2, y, r, r))
        # El fondo: el resplandor verde de la sala (sube, al final del pasillo).
        for r in range(int(w * 0.32), 0, -2):
            k = 1 - r / (w * 0.32)
            pygame.draw.ellipse(img, (int(10 + 30 * k), int(30 + 90 * k), int(24 + 56 * k)),
                                (w // 2 - r, fondo_y - r // 2 - 6, 2 * r, r))
        # Sombra de los lados (la pared del marco, gruesa).
        for k in range(8):
            c = (8 + k * 2, 9 + k * 2, 14 + k * 2)
            pygame.draw.line(img, c, (k, 0), (k, h))
            pygame.draw.line(img, c, (w - 1 - k, 0), (w - 1 - k, h))
        _cache[clave] = img
    return img


def _puerta(screen, offset, sala):
    if sala.estado == "cerrada":
        return
    interior = _interior(sala.puerta)
    pos = interior.move(-offset[0], -offset[1])
    recorte = screen.get_clip()
    screen.set_clip(pos.clip(recorte))
    screen.blit(_boca(interior.size), pos)
    if sala.estado == "abriendo":
        t = sala.estado_ms
        parte = ABRIR_PARED_MS * T_PARTE
        abierta = ABRIR_PARED_MS * T_ABIERTA
        hoja = _hoja(sala.juego.mundo, interior)
        if t < parte:
            temblor = int(math.sin(t / 18) * 2) if t > parte * 0.55 else 0
            screen.blit(hoja, (pos.x + temblor, pos.y))
            _destrabar(screen, pos, t / parte)
        elif t < abierta:
            k = _suave((t - parte) / (abierta - parte))
            mitad = interior.width // 2
            corre = int(k * (mitad + 8))
            izq = hoja.subsurface((0, 0, mitad, interior.height))
            der = hoja.subsurface((mitad, 0, interior.width - mitad, interior.height))
            screen.blit(izq, (pos.x - corre, pos.y))
            screen.blit(der, (pos.x + mitad + corre, pos.y))
            _borde_peligro(screen, pygame.Rect(pos.x + mitad - corre - 5, pos.y, 5, pos.height))
            _borde_peligro(screen, pygame.Rect(pos.x + mitad + corre, pos.y, 5, pos.height))
    screen.set_clip(recorte)


def _destrabar(screen, pos, k):
    """La puerta se destraba: tres luces que pasan de rojo a verde y una
    línea que la recorre de arriba a abajo."""
    for j in range(3):
        luz = pygame.Rect(0, 0, 10, 10)
        luz.center = (pos.centerx + (j - 1) * 22, pos.top + 18)
        verde = k > 0.2 + j * 0.25
        pygame.draw.rect(screen, (10, 12, 16), luz.inflate(4, 4))
        pygame.draw.rect(screen, (90, 240, 150) if verde else (230, 60, 50), luz)
        pygame.draw.rect(screen, (220, 255, 230) if verde else (255, 190, 170), luz.inflate(-6, -6))
    y = pos.top + int(pos.height * min(1.0, k * 1.15))
    if y < pos.bottom:
        pygame.draw.line(screen, (150, 255, 200), (pos.left, y), (pos.right, y), 2)
        pygame.draw.line(screen, (60, 140, 100), (pos.left, y - 3), (pos.right, y - 3), 1)


def _borde_peligro(screen, rect):
    """El canto de cada hoja: franjas amarillas y negras."""
    for y in range(rect.top, rect.bottom, 6):
        pygame.draw.rect(screen, (230, 190, 50) if (y // 6) % 2 else (24, 22, 26),
                         (rect.x, y, rect.width, min(6, rect.bottom - y)))
    pygame.draw.line(screen, (240, 240, 250), rect.topleft, rect.bottomleft)


def dibujar_dintel(screen, offset, camara, sala):
    """La pared de encima de la puerta, delante de los personajes (los que
    cruzan pasan por debajo). Es el mismo pedazo del mapa."""
    if sala is None or not sala.activa or sala.dintel is None or not sala.dintel.colliderect(camara):
        return
    mundo = sala.juego.mundo
    clave = ("dintel", id(mundo), tuple(sala.dintel))
    img = _cache.get(clave)
    if img is None:
        img = _cache[clave] = mundo.imagen.subsurface(
            sala.dintel.clip(mundo.imagen.get_rect())).copy()
    screen.blit(img, (sala.dintel.x - offset[0], sala.dintel.y - offset[1]))


# -- En el piso ---------------------------------------------------------------------------

def dibujar_piso(screen, offset, camara, sala, tiempo_ms, dueño=None):
    if sala is None or not sala.activa:
        return
    if sala.puerta.inflate(200, 200).colliderect(camara):
        _puerta(screen, offset, sala)
    for pista in sala.pistas:
        x, y = pista["punto"]
        if not camara.inflate(200, 200).collidepoint(x, y):
            continue
        img = _pista(pista["tipo"])
        pos = img.get_rect(midbottom=(x - offset[0], y - offset[1] + 10))
        if not pista["encontrada"]:
            # Un halo en el piso que late (como el de las notas): algo para revisar.
            k = 0.5 + 0.5 * math.sin((tiempo_ms + hash(pista["tipo"]) % 997) / 330)
            radio = int(30 + 6 * k)
            halo = cache_dibujo.circulo(radio * 2, (255, 226, 140, int(40 + 40 * k) // 8 * 8), radio)
            screen.blit(halo, halo.get_rect(center=(pos.centerx, pos.bottom - 8)))
        efectos.sombra(screen, (pos.centerx, pos.bottom - 2), img.get_width() * 0.9, 90)
        screen.blit(img, pos)
        if not pista["encontrada"]:
            _destello(screen, (pos.right - 4, pos.top + 2), tiempo_ms + hash(pista["tipo"]) % 997)
    if sala.celular is not None and revelado(sala, dueño) >= 0.5:
        x, y = sala.celular
        if camara.inflate(100, 100).collidepoint(x, y):
            _celular_piso(screen, (x - offset[0], y - offset[1]), tiempo_ms)


def _pista(tipo):
    img = arte.pista(tipo)
    clave = ("pista_g", tipo, id(img))
    grande = _cache.get(clave)
    if grande is None:
        if img.get_height() > 40:                   # (una imagen del equipo ya viene grande)
            grande = img
        else:
            grande = pygame.transform.scale(img, (img.get_width() * ESCALA_PISTA, img.get_height() * ESCALA_PISTA))
        _cache[clave] = grande
    return grande


def _destello(screen, centro, t):
    """La estrellita que titila sobre lo que no han revisado."""
    fase = (t % 1400) / 1400
    if fase > 0.55:
        return
    k = math.sin(fase / 0.55 * math.pi)
    largo = int(3 + 8 * k)
    color = (255, 244, 180)
    x, y = centro
    pygame.draw.line(screen, color, (x - largo, y), (x + largo, y), 2)
    pygame.draw.line(screen, color, (x, y - largo), (x, y + largo), 2)
    pygame.draw.circle(screen, (255, 255, 255), centro, 2)


def _celular_encendido(tiempo_ms):
    """El celular del piso se prende cada tanto: le llega otro mensaje."""
    return (tiempo_ms % 4200) < 1500


def _celular_piso(screen, centro, tiempo_ms):
    """Un celular tirado boca arriba, con la pantalla rota; cada tanto se
    prende con otra notificación y vibra."""
    prendido = _celular_encendido(tiempo_ms)
    vibra = prendido and (tiempo_ms % 4200) < 500
    dx = (1 if (tiempo_ms // 40) % 2 else -1) if vibra else 0
    cuerpo = pygame.Rect(0, 0, 22, 38)
    cuerpo.center = (centro[0] + dx, centro[1])
    efectos.sombra(screen, (cuerpo.centerx, cuerpo.bottom), 30, 110)
    pygame.draw.rect(screen, (16, 16, 22), cuerpo, border_radius=4)
    pantalla = cuerpo.inflate(-6, -8)
    if prendido:
        pygame.draw.rect(screen, (196, 212, 236), pantalla)
        for j in range(3):
            pygame.draw.rect(screen, (70, 90, 130), (pantalla.x + 2, pantalla.y + 6 + j * 8, pantalla.width - 4, 5))
        pygame.draw.rect(screen, (230, 70, 70), (pantalla.x + 2, pantalla.y + 2, 4, 3))
    else:
        pygame.draw.rect(screen, (26, 28, 36), pantalla)
    # La grieta de la pantalla.
    pygame.draw.line(screen, (230, 236, 250) if prendido else (70, 74, 88),
                     (pantalla.left + 2, pantalla.top + 4), (pantalla.right - 3, pantalla.bottom - 6))
    pygame.draw.line(screen, (230, 236, 250) if prendido else (70, 74, 88),
                     (pantalla.centerx, pantalla.centery - 2), (pantalla.left + 1, pantalla.bottom - 3))
    pygame.draw.rect(screen, (60, 62, 74), cuerpo, 1, border_radius=4)


# -- Las cápsulas con los niños -----------------------------------------------------------

def _capsula_apagada(sala, i, tiempo_ms):
    """¿La cápsula `i` se dibuja apagada en este cuadro? (la que está
    fallando parpadea: cada vez más apagada)."""
    if i in sala.apagadas:
        return True
    if sala.fallando_ms > 0 and i == SE_APAGA.get("capsula"):
        k = sala.fallando_ms / max(1, SE_APAGA.get("dura_ms", 1))
        return random.Random(int(tiempo_ms // 70)).random() < 0.25 + 0.7 * k
    return False


ESCALA_NINO = 2.4


def erguidos(sala, camara, tiempo_ms, dueño=None):
    if sala is None or not sala.activa:
        return []
    from juego import decoracion
    lista = _erguido_baul(sala, camara, tiempo_ms)
    if sala.estado == "cerrada":
        return lista
    lista += _erguidos_ninos(sala, camara, tiempo_ms, dueño)
    if revelado(sala, dueño) < 0.5:
        return lista
    for i, capsula in enumerate(sala.capsulas):
        rota = sala.rota(i)
        apagada = not rota and _capsula_apagada(sala, i, tiempo_ms)
        img = arte.capsula_rota(capsula["nino"], ESCALA_CAPSULA) if rota else \
            arte.capsula(capsula["nino"], ESCALA_CAPSULA, apagada)
        if img is None:
            continue
        base = capsula["base"]
        rect = img.get_rect(midbottom=(base.centerx, base.bottom + 6))
        if not rect.inflate(40, 40).colliderect(camara):
            continue
        lista.append(decoracion.Erguido(
            base, rect, lambda screen, offset, c=capsula, r=rect, im=img, k=i, a=apagada: _dibujar_capsula(
                screen, offset, sala, k, c, r, im, a, tiempo_ms)))
    return lista


def _dibujar_capsula(screen, offset, sala, i, capsula, rect, img, apagada, tiempo_ms):
    temblor = capsula.get("temblor", 0)
    dx = int(math.sin(tiempo_ms / 18) * 4 * temblor / 320) if temblor else 0
    pos = rect.move(-offset[0] + dx, -offset[1])
    efectos.sombra(screen, (pos.centerx, pos.bottom - 6), pos.width * 0.8, 110)
    rota = sala.rota(i)
    if rota:
        # El charco del líquido que se salió.
        charco = _mancha(int(pos.width * 1.5), int(pos.width * 0.42), (40, 140, 90))
        screen.blit(charco, charco.get_rect(center=(pos.centerx + 6, pos.bottom - 4)), special_flags=pygame.BLEND_RGB_ADD)
    screen.blit(img, pos)
    golpes = capsula.get("golpes", 0)
    vidrio = arte.vidrio_de_capsula(ESCALA_CAPSULA)
    if golpes and not rota and vidrio is not None:
        grietas = arte.grietas(capsula["nino"], golpes, vidrio.width, vidrio.height)
        screen.blit(grietas, vidrio.move(pos.topleft))
    _monitor(screen, pos, sala, i, capsula, tiempo_ms)
    if temblor and vidrio is not None:
        # El martillazo: el martillo contra el vidrio y unas chispas.
        v = vidrio.move(pos.topleft)
        golpe = (v.left + 4, v.centery)
        martillo = arte.martillo(48)
        angulo = 40 * temblor / 320
        img_m = pygame.transform.rotate(martillo, -20 + angulo)
        screen.blit(img_m, img_m.get_rect(midright=(golpe[0] + 6, golpe[1] - 10)))
        azar = random.Random(int(tiempo_ms // 60) + i)
        for _ in range(6):
            a = azar.uniform(0, 2 * math.pi)
            r = azar.uniform(4, 20) * (1 - temblor / 320 + 0.3)
            pygame.draw.circle(screen, (230, 255, 240), (int(golpe[0] + math.cos(a) * r), int(golpe[1] + math.sin(a) * r)), 2)
    if rota:
        return
    if vidrio is None or not efectos.ACTIVOS or apagada:
        return
    v = vidrio.move(pos.topleft)
    semilla = capsula["nino"] * 53
    for k in range(5):
        alto = v.height - 8
        y = v.bottom - 4 - int((tiempo_ms * 0.035 + k * 41 + semilla) % alto)
        x = v.x + 6 + int((k * 13 + semilla) % max(1, v.width - 12))
        x += int(math.sin((tiempo_ms + k * 300) / 260) * 2)
        r = 2 if k % 2 else 3
        pygame.draw.circle(screen, (190, 255, 215), (x, y), r, 1)


def _erguidos_ninos(sala, camara, tiempo_ms, dueño):
    """Los niños que ya sacaron de su cápsula (de pie al lado, o caminando a la cápsula)."""
    from juego import decoracion
    lista = []
    for i, capsula in enumerate(sala.capsulas):
        donde = sala.posicion_nino(i)
        if donde is None:
            continue
        x, y, se_ve, mira = donde
        img = arte.nino_grande(capsula["nino"], ESCALA_NINO, despierto=True)
        if mira == "west":
            img = _volteado(img)
        alto = img.get_height()
        if mira is not None:
            y -= abs(math.sin(tiempo_ms / 90 + i)) * 4          # (caminando: rebota)
        else:
            y -= math.sin(tiempo_ms / 500 + i) * 1.2            # (quieto: respira)
        rect = img.get_rect(midbottom=(int(x), int(y)))
        pie = pygame.Rect(0, 0, 26, 12)
        pie.midbottom = (int(x), int(donde[1]))
        if not rect.inflate(40, 40).colliderect(camara) or oculto(sala, dueño, pie):
            continue
        if se_ve < 1:
            # Subiéndose a la cápsula: se va hundiendo en ella.
            img = img.subsurface((0, 0, img.get_width(), max(1, int(alto * se_ve)))).copy()
            img.set_alpha(int(255 * se_ve))
            rect = img.get_rect(midbottom=rect.midbottom)
        lista.append(decoracion.Erguido(
            pie, rect, lambda screen, offset, im=img, r=rect: (
                efectos.sombra(screen, (r.centerx - offset[0], r.bottom - offset[1] - 2), r.width * 0.9, 90),
                screen.blit(im, r.move(-offset[0], -offset[1])))))
    return lista


def _volteado(img):
    clave = ("volteado", id(img))
    hecho = _cache.get(clave)
    if hecho is None:
        hecho = _cache[clave] = pygame.transform.flip(img, True, False)
    return hecho


# -- El baúl de la prisión ------------------------------------------------------------------------

def _erguido_baul(sala, camara, tiempo_ms):
    baul = getattr(sala, "baul", None)
    if not baul or not baul["imagen"].colliderect(camara.inflate(60, 60)):
        return []
    from juego import decoracion
    rect = baul["imagen"]
    return [decoracion.Erguido(baul["rect"], rect,
                               lambda screen, offset: _dibujar_baul(screen, offset, baul, tiempo_ms))]


def _dibujar_baul(screen, offset, baul, tiempo_ms):
    rect = baul["imagen"].move(-offset[0], -offset[1])
    if baul["abierto"]:
        img = _baul_abierto(rect.size)
        if img is not None:
            screen.blit(img, img.get_rect(bottomleft=rect.bottomleft))
        if baul["con_martillo"]:
            # El martillo asomándose, con un brillito que pasa.
            m = arte.martillo(max(16, rect.width // 3))
            sitio = m.get_rect(midbottom=(rect.centerx + rect.width // 10, rect.y + int(rect.height * 0.39)))
            screen.blit(m, sitio)
            if (tiempo_ms // 140) % 12 == 0:
                brillo = _resplandor(14, (120, 120, 90))
                screen.blit(brillo, brillo.get_rect(center=sitio.topright), special_flags=pygame.BLEND_RGB_ADD)
    # El teclado del frente: rojo cerrado (parpadea), verde abierto.
    k = rect.width / 64
    teclado = pygame.Rect(0, 0, max(6, int(10 * k)), max(5, int(7 * k)))
    teclado.center = (rect.x + int(46 * k), rect.y + int(40 * k))
    pygame.draw.rect(screen, (24, 26, 34), teclado.inflate(2, 2), border_radius=2)
    pygame.draw.rect(screen, (46, 52, 66), teclado, border_radius=2)
    for fila in range(2):
        for col in range(3):
            pygame.draw.rect(screen, (120, 130, 150), (teclado.x + 2 + col * teclado.width // 3,
                                                       teclado.y + 2 + fila * teclado.height // 2, max(1, int(k)), max(1, int(k))))
    abierto = baul["abierto"]
    prendida = abierto or (tiempo_ms // 600) % 2 == 0
    color = (80, 240, 130) if abierto else (240, 60, 60)
    luz = (teclado.right + max(3, int(3 * k)), teclado.centery)
    if prendida:
        brillo = _resplandor(max(5, int(6 * k)), tuple(c // 3 for c in color))
        screen.blit(brillo, brillo.get_rect(center=luz), special_flags=pygame.BLEND_RGB_ADD)
    pygame.draw.circle(screen, color if prendida else (90, 30, 30), luz, max(2, int(1.6 * k)))


def _baul_abierto(tam):
    """El baúl de la decoración, con la tapa levantada y oscuro por dentro."""
    clave = ("baul_abierto", tam)
    if clave in _cache:
        return _cache[clave]
    import os
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "Imagenes", "Objetos", "OBJ-027_Caja_de_seguridad.png")
    try:
        src = pygame.image.load(ruta).convert_alpha()
    except (pygame.error, FileNotFoundError, OSError):
        _cache[clave] = None
        return None
    # En px de la hoja (64x64): la tapa va de la fila 8 a la 22; el cuerpo, de
    # la 23 abajo. Abierto tapa del todo la tapa cerrada de la decoración.
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    s.blit(src, (0, 23), pygame.Rect(0, 23, 64, 41))
    # Por dentro: la pared del fondo (oscura, más clara arriba) y el borde.
    for y in range(9, 26):
        k = (y - 9) / 16
        pygame.draw.line(s, (int(44 - 26 * k), int(48 - 28 * k), int(60 - 30 * k)), (4, y), (59, y))
    pygame.draw.rect(s, (24, 26, 34), (4, 9, 56, 17), 1)
    pygame.draw.line(s, (170, 176, 190), (4, 25), (59, 25))
    pygame.draw.line(s, (90, 96, 110), (4, 26), (59, 26))
    # La tapa, levantada hacia atrás: se ve por debajo (más corta y oscura).
    tapa = src.subsurface(pygame.Rect(0, 8, 64, 15)).copy()
    tapa = pygame.transform.flip(tapa, False, True)
    tapa = pygame.transform.scale(tapa, (64, 10))
    tapa.fill((120, 122, 138, 255), special_flags=pygame.BLEND_RGBA_MULT)
    s.blit(tapa, (0, 0))
    img = pygame.transform.scale(s, tam)
    _cache[clave] = img
    return img


def _monitor(screen, pos, sala, i, capsula, tiempo_ms):
    """El monitorcito de la base: el número del sujeto y su latido (en verde
    que corre; plano y gris en las apagadas; la que falla, a saltos y roja)."""
    pantalla = pygame.Rect(0, 0, 46, 17)
    pantalla.midbottom = (pos.centerx, pos.bottom - 16)
    pygame.draw.rect(screen, (12, 14, 18), pantalla.inflate(4, 4))
    pygame.draw.rect(screen, (6, 16, 12), pantalla)
    apagada = i in sala.apagadas
    fallando = sala.fallando_ms > 0 and i == SE_APAGA.get("capsula")
    regenerando = sala.regenera is not None and sala.regenera[0] == i
    color = (70, 80, 84) if apagada else ((240, 80, 70) if fallando else (90, 240, 150))
    medio = pantalla.centery + 3
    # El número del sujeto, arriba a la izquierda (en pixeles: la letra
    # del juego no cabe tan chica).
    _numero(screen, (pantalla.x + 2, pantalla.y + 2), capsula.get("sujeto", i + 1),
            (110, 120, 120) if apagada else (150, 220, 180))
    x0, x1 = pantalla.x + 14, pantalla.right - 2
    if apagada and not (regenerando and 0.45 < sala.regenera[1] / REGENERAR["ms"] < 0.55):
        pygame.draw.line(screen, color, (x0, medio), (x1, medio))
        return
    # La línea del latido: corre hacia la izquierda; cada latido, un pico.
    periodo = 700 if not fallando else 260 + (i * 37 + int(tiempo_ms // 260) * 53) % 300
    fase = (tiempo_ms + capsula["nino"] * 211) % periodo
    puntos = []
    for x in range(x0, x1):
        t = (fase - (x1 - x) * 12) % periodo
        y = medio
        if t < 40:
            y = medio - int(6 * math.sin(t / 40 * math.pi))
        elif 40 <= t < 60:
            y = medio + 2
        puntos.append((x, y))
    if len(puntos) > 1:
        pygame.draw.lines(screen, color, False, puntos)


_DIGITOS = ["111101101101111", "010110010010111", "111001111100111", "111001111001111", "101101111001001",
            "111100111001111", "111100111101111", "111001001001001", "111101111101111", "111101111001111"]


def _numero(screen, pos, n, color):
    """Un número con dígitos de 3x5 (de 2 px)."""
    x, y = pos
    for d in str(n):
        patron = _DIGITOS[int(d)]
        for k, bit in enumerate(patron):
            if bit == "1":
                screen.fill(color, (x + (k % 3), y + (k // 3) * 2, 1, 2))
        x += 4


# -- Luces (encima de la oscuridad) ---------------------------------------------------------

def _resplandor(radio, color):
    clave = ("resplandor", radio, color)
    img = _cache.get(clave)
    if img is None:
        img = pygame.Surface((radio * 2, radio * 2))
        img.fill((0, 0, 0))
        for r in range(radio, 0, -2):
            k = (1 - r / radio) ** 1.6
            pygame.draw.circle(img, tuple(int(c * k) for c in color), (radio, radio), r)
        _cache[clave] = img
    return img


def _mancha(ancho, alto, color):
    """Una mancha de luz ovalada (la que sale de la puerta al piso)."""
    clave = ("mancha", ancho, alto, color)
    img = _cache.get(clave)
    if img is None:
        img = pygame.Surface((ancho, alto))
        img.fill((0, 0, 0))
        for k in range(24, 0, -1):
            f = k / 24
            v = (1 - f) ** 1.5
            r = pygame.Rect(0, 0, int(ancho * f), int(alto * f))
            r.midtop = (ancho // 2, 0)
            pygame.draw.ellipse(img, tuple(int(c * v) for c in color), r)
        _cache[clave] = img
    return img


def _haz(largo, ancho, color):
    """Un haz de luz (para las balizas que giran), apuntando a la derecha."""
    clave = ("haz", largo, ancho, color)
    img = _cache.get(clave)
    if img is None:
        img = pygame.Surface((largo, ancho))
        img.fill((0, 0, 0))
        for x in range(largo):
            k = (1 - x / largo) ** 1.2
            medio = ancho / 2
            abre = 2 + (medio - 2) * (x / largo)
            for y in range(ancho):
                d = abs(y - medio) / max(1.0, abre)
                if d < 1:
                    v = k * (1 - d) ** 1.5
                    img.set_at((x, y), tuple(int(c * v) for c in color))
        _cache[clave] = img
    return img


def _haz_girado(largo, ancho, color, angulo):
    """Guardado de a 10 grados (36 imágenes chicas: girar 16 haces en cada
    cuadro con 4 jugadores costaba más que guardarlos)."""
    paso = int(round(angulo / 10)) % 36
    clave = ("haz_g", largo, ancho, color, paso)
    img = _cache.get(clave)
    if img is None:
        img = _cache[clave] = pygame.transform.rotate(_haz(largo, ancho, color), -paso * 10)
    return img


def precalentar(sala=None):
    """Lo que tarda en armarse (lo de adentro, los haces, los resplandores,
    las cápsulas): en la pantalla de carga y no en medio de la partida."""
    if pygame.display.get_surface() is None:
        return
    for angulo in range(0, 360, 10):
        _haz_girado(LARGO_HAZ, ANCHO_HAZ, COLOR_HAZ, angulo)
    _resplandor(120, (24, 70, 44))
    _resplandor(40, (200, 40, 30))
    for i in range(len(arte.NINOS)):
        arte.capsula(i, ESCALA_CAPSULA)
    if sala is not None and sala.activa:
        pintura(sala.juego.mundo, sala)
        for i in range(len(sala.capsulas)):
            arte.capsula(sala.capsulas[i]["nino"], ESCALA_CAPSULA, True)
        _boca(_interior(sala.puerta).size)


def _luz_puerta(screen, offset, sala, tiempo_ms):
    """La luz de la puerta: el marco que brilla mientras se destraba, la
    rendija verde que se abre y lo que sale al piso de la Bahía."""
    interior = _interior(sala.puerta)
    pos = interior.move(-offset[0], -offset[1])
    marco = sala.puerta.move(-offset[0], -offset[1])
    piso = (marco.centerx, marco.bottom - 4)
    if sala.estado == "abriendo":
        t = sala.estado_ms
        parte = ABRIR_PARED_MS * T_PARTE
        abierta = ABRIR_PARED_MS * T_ABIERTA
        if t < parte:
            k = 0.5 + 0.5 * math.sin(t / 55)
            color = (int(70 * k), int(56 * k), int(14 * k))
            for g in range(3):
                pygame.draw.rect(screen, color, marco.inflate(2 * g, 2 * g), 2,
                                 border_radius=6)
            return
        k = _suave((t - parte) / (abierta - parte))
        corre = int(k * (interior.width // 2 + 8))
        brillo = 1.0 if t < abierta else max(0.0, 1 - (t - abierta) / (ABRIR_PARED_MS - abierta))
        rendija = pygame.Rect(pos.centerx - corre, pos.top, max(2, 2 * corre), pos.height)
        fuerza = 0.35 + 0.65 * (1 - k) if t < abierta else 0.35 * brillo
        screen.fill((int(60 * fuerza), int(160 * fuerza), int(100 * fuerza)), rendija,
                    special_flags=pygame.BLEND_RGB_ADD)
        nucleo = pygame.Rect(pos.centerx - 2, pos.top, 4, pos.height)
        if t < abierta:
            screen.fill((140, 255, 200), nucleo.inflate(int(4 * (1 - k)), 0), special_flags=pygame.BLEND_RGB_ADD)
        mancha = _mancha(int(80 + 340 * k), int(60 + 120 * k), (40, 130, 80))
        screen.blit(mancha, mancha.get_rect(midtop=piso), special_flags=pygame.BLEND_RGB_ADD)
        if t >= abierta:
            flash = _resplandor(220, (int(70 * brillo), int(180 * brillo), int(120 * brillo)))
            screen.blit(flash, flash.get_rect(center=pos.center), special_flags=pygame.BLEND_RGB_ADD)
        return
    # Abierta: un resplandor tenue que respira.
    pulso = round((0.75 + 0.25 * math.sin(tiempo_ms / 700)) * 10) / 10
    mancha = _mancha(380, 170, tuple(int(c * pulso) for c in (22, 74, 46)))
    screen.blit(mancha, mancha.get_rect(midtop=piso), special_flags=pygame.BLEND_RGB_ADD)
    img = _resplandor(90, tuple(int(c * pulso) for c in (16, 60, 36)))
    screen.blit(img, img.get_rect(center=(pos.centerx, pos.top + pos.height // 3)),
                special_flags=pygame.BLEND_RGB_ADD)


def dibujar_luces(screen, vista, camara, offset, sala, tiempo_ms, dueño=None):
    if sala is None or not sala.activa or sala.estado == "cerrada" or not efectos.ACTIVOS:
        return
    recorte = screen.get_clip()
    screen.set_clip(vista.clip(recorte))
    if sala.puerta.inflate(800, 500).colliderect(camara):
        _luz_puerta(screen, offset, sala, tiempo_ms)
    adentro = revelado(sala, dueño) >= 0.5
    zona = sala.sala.union(sala.pasillo).inflate(400, 400)
    if not adentro or not zona.colliderect(camara):
        screen.set_clip(recorte)
        return
    pulso = round((0.75 + 0.25 * math.sin(tiempo_ms / 520)) * 10) / 10    # (pocos niveles: se guardan)
    # La luz verde de cada cápsula prendida.
    verde = tuple(int(c * pulso) for c in (24, 70, 44))
    for i, capsula in enumerate(sala.capsulas):
        if _capsula_apagada(sala, i, tiempo_ms):
            continue
        b = capsula["base"]
        centro = (b.centerx - offset[0], b.bottom - 90 - offset[1])
        img = _resplandor(120, verde)
        screen.blit(img, img.get_rect(center=centro), special_flags=pygame.BLEND_RGB_ADD)
    # El celular del piso, cuando se prende.
    if sala.celular is not None and _celular_encendido(tiempo_ms):
        img = _resplandor(46, (40, 52, 80))
        screen.blit(img, img.get_rect(center=(sala.celular[0] - offset[0], sala.celular[1] - offset[1])),
                    special_flags=pygame.BLEND_RGB_ADD)
    if sala.regenera is not None:
        _luz_regenera(screen, offset, sala)
    # La alarma: balizas rojas que giran (una en la sala, otra en el pasillo).
    if sala.estado == "votacion" or (sala.estado == "desenlace" and not sala.a_la_capsula):
        rapido = 1.0 + 1.5 * sala.cerca
        for k, (cx, cy) in enumerate(((sala.sala.centerx, sala.sala.top + 10),
                                      (sala.pasillo.centerx, sala.pasillo.top + 4))):
            centro = (cx - offset[0], cy - offset[1])
            angulo = (tiempo_ms * 0.18 * rapido + k * 90) % 360
            for extra in (0, 180):
                a = math.radians(angulo + extra)
                haz = _haz_girado(LARGO_HAZ, ANCHO_HAZ, COLOR_HAZ, angulo + extra)
                medio = (centro[0] + math.cos(a) * LARGO_HAZ / 2, centro[1] + math.sin(a) * LARGO_HAZ / 2)
                screen.blit(haz, haz.get_rect(center=(int(medio[0]), int(medio[1]))),
                            special_flags=pygame.BLEND_RGB_ADD)
            foco = _resplandor(40, (200, 40, 30))
            screen.blit(foco, foco.get_rect(center=centro), special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(screen, (255, 90, 70), centro, 7)
            pygame.draw.circle(screen, (255, 220, 200), centro, 3)
    screen.set_clip(recorte)


def _luz_regenera(screen, offset, sala):
    """El Biomante intenta regenerar una cápsula apagada: las chispas verdes
    giran hacia el vidrio, la cápsula titila una vez... y se apagan, grises."""
    i, ms = sala.regenera
    if i >= len(sala.capsulas):
        return
    k = ms / max(1, REGENERAR["ms"])
    b = sala.capsulas[i]["base"]
    cx, cy = b.centerx - offset[0], b.bottom - 95 - offset[1]
    azar = random.Random(i * 97)
    for j in range(16):
        fase = azar.random() * math.tau
        if k < 0.55:
            q = k / 0.55
            radio = 110 * (1 - q) + 14
            a = fase + q * 5
            x, y = cx + math.cos(a) * radio, cy + math.sin(a) * radio * 0.8
            color = (int(80 + 120 * q), 255, int(140 + 60 * q))
        else:
            q = (k - 0.55) / 0.45
            a = fase
            x = cx + math.cos(a) * (14 + 30 * q)
            y = cy + math.sin(a) * 10 + 90 * q * q
            g = int(160 * (1 - q))
            color = (g, g, g)
        if color[1] < 8:
            continue
        screen.fill(color, (int(x) - 1, int(y) - 1, 3, 3), special_flags=pygame.BLEND_RGB_ADD)
    if 0.45 < k < 0.6:
        img = _resplandor(120, (30, 90, 56))
        screen.blit(img, img.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_RGB_ADD)


# -- La alarma y la votación (interfaz) --------------------------------------------------------

def render_vista_alarma(screen, vista, sala):
    """Cada vista se tiñe de rojo con la alarma (más fuerte mientras más cerca
    vienen); en el desenlace, un destello."""
    if sala is None or not sala.activa or sala.estado not in ("votacion", "desenlace"):
        return
    t = pygame.time.get_ticks()
    if sala.estado == "desenlace" and sala.resultado == "liberar" and sala.fase_liberar == "capsula":
        pass                # (los aliens vuelven: el viñeteado rojo, como en la votación)
    elif sala.estado == "desenlace":
        k = 1 - min(1.0, sala.estado_ms / DESENLACE_MS)
        sale = sala.resultado in ("escapar", "liberar")
        color = (255, 255, 255) if sale else (160, 10, 10)
        alfa = int(150 * k * k) if sale else int(60 + 90 * (1 - k))
        if alfa > 0:
            screen.blit(cache_dibujo.capa(vista.size, (*color, alfa // 4 * 4)), vista.topleft)
        return
    late = 0.5 + 0.5 * math.sin(t / (260 - 120 * sala.cerca))
    nivel = int((70 + 185 * sala.cerca) * late) // 8 * 8
    if nivel > 0:
        for img, pos in _vineta(vista.size):
            img.set_alpha(min(255, nivel))
            screen.blit(img, (vista.x + pos[0], vista.y + pos[1]))


def _vineta(tam):
    """El borde rojo de la vista, en cuatro tiras (el centro no se toca: pegar
    toda la vista con alfa, cuatro veces por cuadro, era lo más caro de la
    alarma). Una por tamaño; la intensidad va con set_alpha."""
    clave = ("vineta", tuple(tam))
    tiras = _cache.get(clave)
    if tiras is None:
        w, h = tam
        chico = pygame.Surface((32, 18), pygame.SRCALPHA)
        for x in range(32):
            for y in range(18):
                d = max(abs(x - 15.5) / 16, abs(y - 8.5) / 9)
                a = int(170 * min(1.0, max(0.0, (d - 0.45) / 0.55)) ** 1.3)
                chico.set_at((x, y), (200, 20, 20, min(255, a)))
        entera = pygame.transform.smoothscale(chico, (w, h))
        bx, by = int(w * 0.24), int(h * 0.24)
        rects = [pygame.Rect(0, 0, w, by), pygame.Rect(0, h - by, w, by),
                 pygame.Rect(0, by, bx, h - 2 * by), pygame.Rect(w - bx, by, bx, h - 2 * by)]
        tiras = _cache[clave] = [(entera.subsurface(r).copy(), r.topleft) for r in rects]
    return tiras


def render_alarma(screen, sala, centro_x, arriba, ancho_max):
    """El cartel de la alarma, arriba en el medio (con lo global): como el
    gif de Campo. Devuelve su rect (o None)."""
    if sala is None or not sala.activa or sala.estado not in ("votacion", "desenlace"):
        return None
    if sala.estado == "desenlace" and (sala.a_la_capsula or sala.resultado == "liberar"):
        return None         # (ganó escapar o sacarlos: se apagó la alarma)
    t = pygame.time.get_ticks()
    e = max(0.6, min(1.25, screen.get_height() / 900))
    w = int(min(ancho_max, 360 * e))
    h = int(w * 0.5)
    caja = pygame.Rect(0, 0, w, h)
    caja.midtop = (centro_x, arriba + int(22 * e))
    quedan = sala.quedan_ms if sala.estado == "votacion" else 0
    segundos = int(math.ceil(quedan / 1000))
    urgente = segundos <= 5
    rojo_fondo = (52, 10, 12) if not urgente or (t // 250) % 2 else (78, 12, 14)
    # Parlantes a los lados, con sus ondas.
    for lado in (-1, 1):
        parlante = pygame.Rect(0, 0, int(28 * e), int(42 * e))
        parlante.center = (caja.centerx + lado * (caja.width // 2 + int(20 * e)), caja.centery)
        pygame.draw.rect(screen, (40, 38, 46), parlante, border_radius=4)
        pygame.draw.rect(screen, (90, 88, 100), parlante, 2, border_radius=4)
        for yy in range(parlante.top + 6, parlante.bottom - 4, 5):
            for xx in range(parlante.left + 5, parlante.right - 4, 5):
                pygame.draw.rect(screen, (20, 20, 24), (xx, yy, 2, 2))
        for k in range(3):
            fase = (t / 180 + k) % 3
            r = int((10 + fase * 9) * e)
            color = (230, 150, 60) if fase < 2.2 else (120, 70, 30)
            cx = parlante.centerx + lado * int(12 * e)
            arco = pygame.Rect(0, 0, r * 2, r * 2)
            arco.center = (cx, parlante.centery)
            inicio = -math.pi / 3 if lado > 0 else math.pi * 2 / 3
            pygame.draw.arc(screen, color, arco, inicio, inicio + math.pi * 2 / 3, max(2, int(3 * e)))
    # El panel.
    pygame.draw.rect(screen, (24, 22, 30), caja.inflate(int(10 * e), int(10 * e)), border_radius=6)
    pygame.draw.rect(screen, (96, 92, 108), caja.inflate(int(10 * e), int(10 * e)), 3, border_radius=6)
    pygame.draw.rect(screen, rojo_fondo, caja)
    for y in range(caja.top, caja.bottom, 3):                     # líneas de pantalla
        pygame.draw.line(screen, (rojo_fondo[0] + 10, 12, 14), (caja.left, y), (caja.right - 1, y))
    # La baliza de arriba.
    baliza = (caja.centerx, caja.top - int(14 * e))
    pygame.draw.rect(screen, (60, 58, 70), (baliza[0] - int(12 * e), caja.top - int(8 * e), int(24 * e), int(8 * e)))
    brillo = (t // 300) % 2 == 0
    pygame.draw.circle(screen, (255, 60, 50) if brillo else (150, 20, 20), baliza, int(11 * e))
    pygame.draw.circle(screen, (255, 200, 190), (baliza[0] - int(3 * e), baliza[1] - int(3 * e)), int(3 * e))
    if brillo and efectos.ACTIVOS:
        img = _resplandor(int(60 * e), (110, 20, 14))
        screen.blit(img, img.get_rect(center=baliza), special_flags=pygame.BLEND_RGB_ADD)
    # Título, número y barra.
    color_titulo = (245, 200, 90) if not urgente else (255, 120, 100)
    f_titulo = fuente_de_tamano(max(12, int(19 * e)))
    titulo = VOTACION["alarma"] + "  " + VOTACION["alarma_sub"]
    img = cache_dibujo.texto(f_titulo, titulo, color_titulo)
    if img.get_width() > caja.width - 16:
        img = cache_dibujo.texto(fuente_de_tamano(max(10, int(15 * e))), titulo, color_titulo)
    screen.blit(img, img.get_rect(midtop=(caja.centerx, caja.top + int(8 * e))))
    linea_y = caja.top + int(12 * e) + img.get_height()
    pygame.draw.line(screen, (150, 40, 30), (caja.left + 12, linea_y), (caja.right - 12, linea_y), 2)
    if sala.estado == "desenlace":
        numero = "¡YA!" if (t // 200) % 2 else ""
        color_num = (255, 80, 60)
    else:
        numero = f"{segundos:02d}"
        k = 1 - quedan / max(1, sala.total_ms)
        color_num = tuple(int(a + (b - a) * k) for a, b in zip((250, 214, 186), (255, 70, 60)))
    f_num = fuente_de_tamano(max(20, int(64 * e)))
    if numero:
        sombra = cache_dibujo.texto(f_num, numero, (40, 8, 8))
        img = cache_dibujo.texto(f_num, numero, color_num)
        centro = (caja.centerx, linea_y + (caja.bottom - linea_y) // 2 - int(6 * e))
        if urgente and sala.estado == "votacion":
            centro = (centro[0] + random.randint(-1, 1), centro[1])
        screen.blit(sombra, sombra.get_rect(center=(centro[0] + 3, centro[1] + 3)))
        screen.blit(img, img.get_rect(center=centro))
    barra = pygame.Rect(caja.left + int(18 * e), caja.bottom - int(16 * e), caja.width - int(36 * e), max(4, int(7 * e)))
    pygame.draw.rect(screen, (70, 20, 20), barra)
    lleno = barra.copy()
    lleno.width = int(barra.width * (quedan / max(1, sala.total_ms)))
    if lleno.width > 0:
        k = 1 - quedan / max(1, sala.total_ms)
        color_barra = tuple(int(a + (b - a) * k) for a, b in zip((240, 160, 50), (230, 50, 40)))
        pygame.draw.rect(screen, color_barra, lleno)
    # Cuántos ya votaron.
    votan = [v for v, puede in zip(sala.votos, sala.votantes) if puede]
    if votan and sala.estado == "votacion":
        f_chica = fuente_de_tamano(max(10, int(13 * e)))
        hechos = sum(1 for v in votan if v is not None)
        img = cache_dibujo.texto(f_chica, f"VOTOS {hechos}/{len(votan)}", (240, 200, 180))
        screen.blit(img, img.get_rect(topright=(caja.right - 8, caja.bottom + int(8 * e))))
    # Franja de peligro debajo.
    franja = pygame.Rect(caja.left - int(40 * e), caja.bottom + int(6 * e), caja.width + int(80 * e), max(4, int(6 * e)))
    _franja(screen, franja, t)
    return caja


def _franja(screen, rect, t):
    recorte = screen.get_clip()
    screen.set_clip(rect.clip(recorte))
    paso = max(6, rect.height * 2)
    corrido = (t // 40) % paso
    pygame.draw.rect(screen, (24, 22, 26), rect)
    for x in range(rect.left - paso * 2 + corrido, rect.right + paso, paso):
        pygame.draw.polygon(screen, (230, 180, 50), [(x, rect.bottom), (x + paso // 2, rect.bottom),
                                                    (x + paso // 2 + rect.height, rect.top), (x + rect.height, rect.top)])
    screen.set_clip(recorte)


def render_voto(screen, vista, jugador, sala):
    """El menú de la votación de este jugador: dos tarjetas (la cápsula y los
    niños), la escogida brilla; lo que ya votó lleva una palomita."""
    if sala is None or not sala.activa or sala.estado != "votacion":
        return
    from screens import estilo
    try:
        i = sala.juego.jugadores.index(jugador)
    except (ValueError, AttributeError):
        i = getattr(jugador, "puesto", 0)
    voto = sala.votos[i] if 0 <= i < len(sala.votos) else None
    e = max(0.62, min(1.3, min(vista.width / 900, vista.height / 520)))
    ancho = int(min(vista.width - 30, 620 * e))
    claves = list(getattr(sala, "claves", None) or [o["clave"] for o in VOTACION["opciones"]])
    from misiones.sala_secreta import opcion as datos_opcion
    alto = int(min(vista.height * 0.58, 270 * e))
    caja = pygame.Rect(0, 0, ancho, alto)
    # (por encima del pulso y las vidas, que van abajo a la izquierda)
    caja.midbottom = (vista.centerx, vista.bottom - min(int(74 * e), max(8, vista.height - alto - 70)))
    screen.blit(cache_dibujo.capa(caja.size, (10, 8, 18, 200)), caja.topleft)
    pygame.draw.rect(screen, (200, 60, 50), caja, 2, border_radius=10)
    f_titulo = fuente_de_tamano(max(14, int(24 * e)))
    titulo = cache_dibujo.texto(f_titulo, VOTACION["titulo"], (255, 230, 200))
    screen.blit(titulo, titulo.get_rect(midtop=(caja.centerx, caja.top + int(8 * e))))
    arriba = caja.top + int(14 * e) + titulo.get_height()
    tarjetas = []
    hueco = int(14 * e)
    tw = (caja.width - (len(claves) + 1) * hueco) // max(1, len(claves))
    th = caja.bottom - arriba - int(44 * e)
    f = fuente_de_tamano(max(12, int(17 * e)))
    f_chica = fuente_de_tamano(max(10, int(13 * e)))
    t = pygame.time.get_ticks()
    for k, clave in enumerate(claves):
        opcion = datos_opcion(clave)
        r = pygame.Rect(caja.left + hueco + k * (tw + hueco), arriba, tw, th)
        elegida = jugador.cursor % len(claves) == k
        color = {"escapar": (255, 214, 64), "liberar": (120, 200, 255)}.get(clave, (120, 240, 170))
        if elegida:
            r = r.move(0, -int(3 * e * (0.5 + 0.5 * math.sin(t / 200))))
        estilo.tarjeta(screen, r, elegido=elegida, color=color, franja=False)
        icono = _icono_opcion(opcion["clave"], max(30, int(r.height * 0.46)))
        if icono is not None:
            screen.blit(icono, icono.get_rect(midtop=(r.centerx, r.top + int(8 * e))))
        y = r.top + int(12 * e) + (icono.get_height() if icono is not None else 0)
        from screens.paneles import partir_lineas
        for linea in partir_lineas(opcion["texto"], f, r.width - 16)[:2]:
            img = cache_dibujo.texto(f, linea, (250, 250, 255) if elegida else (200, 204, 226))
            screen.blit(img, img.get_rect(midtop=(r.centerx, y)))
            y += f.get_linesize()
        for linea in partir_lineas(opcion["detalle"], f_chica, r.width - 16)[:2]:
            img = cache_dibujo.texto(f_chica, linea, (170, 176, 206))
            screen.blit(img, img.get_rect(midtop=(r.centerx, y)))
            y += f_chica.get_linesize()
        if voto == opcion["clave"]:
            sello = cache_dibujo.texto(f, "TU VOTO", (30, 20, 10))
            fondo = sello.get_rect(topright=(r.right - 6, r.top + 6)).inflate(10, 4)
            pygame.draw.rect(screen, color, fondo, border_radius=5)
            screen.blit(sello, sello.get_rect(center=fondo.center))
        tarjetas.append(r)
    izq = jugador.nombre_tecla("izquierda") if hasattr(jugador, "nombre_tecla") else "A"
    der = jugador.nombre_tecla("derecha") if hasattr(jugador, "nombre_tecla") else "D"
    ok = jugador.nombre_tecla("interactuar") if hasattr(jugador, "nombre_tecla") else "E"
    accion = "cambiar el voto" if voto else "votar"
    estilo.pie(screen, f"[{izq}] [{der}] escoger   [{ok}] {accion}", caja.bottom - int(30 * e),
               f=fuente_de_tamano(max(11, int(14 * e))), x=caja.centerx)
    nota = cache_dibujo.texto(f_chica, VOTACION["nota"], (190, 150, 150))
    if nota.get_width() > caja.width - 20:
        nota = pygame.transform.smoothscale(nota, (caja.width - 20, int(nota.get_height() * (caja.width - 20) / nota.get_width())))
    screen.blit(nota, nota.get_rect(midbottom=(caja.centerx, caja.bottom - int(4 * e))))


def _icono_opcion(clave, alto):
    cache = ("icono", clave, alto)
    img = _cache.get(cache)
    if img is None:
        if clave == "escapar":
            from juego import sprites_objetos
            img = sprites_objetos.imagen("nave_completa.png", alto=alto)
        elif clave == "liberar":
            # El martillo contra la cápsula, y el niño ya afuera.
            capsula = arte.capsula_rota(0, 1)
            nino = arte.nino(0, despierto=True)
            if capsula is not None:
                k = alto / capsula.get_height()
                cap = pygame.transform.scale(capsula, (max(1, int(capsula.get_width() * k)), alto))
                kn = alto * 0.62 / nino.get_height()
                chico = pygame.transform.scale(nino, (max(1, int(nino.get_width() * kn)),
                                                      max(1, int(nino.get_height() * kn))))
                img = pygame.Surface((cap.get_width() + chico.get_width() + 4, alto), pygame.SRCALPHA)
                img.blit(cap, (0, 0))
                img.blit(chico, chico.get_rect(bottomright=img.get_rect().bottomright))
                m = arte.martillo(max(16, alto // 2))
                img.blit(m, (cap.get_width() - m.get_width() // 2, alto // 6))
        else:
            capsula = arte.capsula(0, 1)
            if capsula is not None:
                img = pygame.transform.scale(capsula, (max(1, capsula.get_width() * alto // capsula.get_height()), alto))
        _cache[cache] = img
    return img


# -- El celular del piso (los mensajes de la mamá) -------------------------------------------------

def render_celular_nino(screen, vista, jugador):
    """El celular que estaba en el piso de la sala, en la mano: la pantalla
    bloqueada, con la batería en 1 % y los mensajes que nadie contestó."""
    from screens import cinematica
    t = pygame.time.get_ticks()
    alto = int(min(vista.height * 0.86, vista.width * 1.5, 640))
    centro = (vista.centerx, vista.centery - int(alto * 0.02))
    screen.blit(cache_dibujo.capa(vista.size, (4, 4, 10, 170)), vista.topleft)
    rect = cinematica.celular(screen, centro, alto, _pantalla_bloqueada, t)
    ok = jugador.nombre_tecla("interactuar") if hasattr(jugador, "nombre_tecla") else "E"
    f = fuente_de_tamano(max(11, int(alto * 0.03)))
    img = cache_dibujo.texto(f, f"[{ok}] {tr(CELULAR_NINO['cerrar'])}", (200, 204, 226))
    screen.blit(img, img.get_rect(midtop=(vista.centerx, min(vista.bottom - img.get_height() - 4, rect.bottom + 6))))


def _pantalla_bloqueada(sup, t):
    w, h = sup.get_size()
    for y in range(h):
        k = y / max(1, h - 1)
        sup.fill((int(20 + 16 * k), int(22 + 10 * k), int(44 + 20 * k)), (0, y, w, 1))
    f_chica = fuente_de_tamano(max(9, int(w * 0.05)))
    f_media = fuente_de_tamano(max(10, int(w * 0.06)))
    f_hora = fuente_de_tamano(max(20, int(w * 0.24)))
    blanco, tenue = (236, 238, 248), (170, 176, 204)
    # La batería, casi muerta (titila).
    bat = pygame.Rect(w - int(w * 0.17), int(w * 0.04), int(w * 0.1), int(w * 0.05))
    pygame.draw.rect(sup, tenue, bat, 1)
    pygame.draw.rect(sup, tenue, (bat.right, bat.centery - 2, 2, 4))
    if (t // 600) % 2:
        pygame.draw.rect(sup, (230, 60, 60), (bat.x + 2, bat.y + 2, 2, bat.height - 4))
    img = cache_dibujo.texto(f_chica, f"{CELULAR_NINO['bateria']}%", (230, 90, 90))
    sup.blit(img, img.get_rect(midright=(bat.left - 4, bat.centery)))
    # La hora y la fecha.
    y = int(h * 0.08)
    img = cache_dibujo.texto(f_hora, CELULAR_NINO["hora"], blanco)
    sup.blit(img, img.get_rect(midtop=(w // 2, y)))
    y += img.get_height()
    img = cache_dibujo.texto(f_media, tr(CELULAR_NINO["fecha"]), tenue)
    sup.blit(img, img.get_rect(midtop=(w // 2, y)))
    y += img.get_height() + int(h * 0.03)
    # Las notificaciones: las llamadas perdidas y los mensajes (el último arriba).
    margen = int(w * 0.06)
    tarjetas = [(tr("Teléfono"), tr(CELULAR_NINO["llamadas"]), True)]
    tarjetas += [(tr(CELULAR_NINO["contacto"]), tr(m), False) for m in reversed(CELULAR_NINO["mensajes"])]
    from screens.paneles import partir_lineas
    for k, (quien, texto, llamada) in enumerate(tarjetas):
        lineas = partir_lineas(texto, f_media, w - 2 * margen - int(w * 0.2))[:2]
        alto = int(w * 0.07) + len(lineas) * f_media.get_linesize() + int(w * 0.04)
        if y + alto > h - int(h * 0.04):
            # Las que no caben, apiladas ("y X más").
            resto = len(tarjetas) - k
            img = cache_dibujo.texto(f_chica, tr("y {} más").format(resto), tenue)
            sup.blit(img, img.get_rect(midtop=(w // 2, y)))
            break
        tarjeta = pygame.Rect(margen, y, w - 2 * margen, alto)
        fondo = pygame.Surface(tarjeta.size, pygame.SRCALPHA)
        pygame.draw.rect(fondo, (240, 242, 255, 46), fondo.get_rect(), border_radius=int(w * 0.04))
        sup.blit(fondo, tarjeta.topleft)
        icono = pygame.Rect(tarjeta.x + int(w * 0.03), tarjeta.y + int(w * 0.035), int(w * 0.1), int(w * 0.1))
        pygame.draw.rect(sup, (220, 70, 70) if llamada else (60, 190, 110), icono, border_radius=int(w * 0.025))
        if llamada:
            pygame.draw.arc(sup, blanco, icono.inflate(-6, -6), math.pi * 1.1, math.pi * 1.9, 2)
        else:
            pygame.draw.rect(sup, blanco, icono.inflate(-int(w * 0.04), -int(w * 0.05)), 1, border_radius=2)
        x = icono.right + int(w * 0.03)
        img = cache_dibujo.texto(f_media, quien, blanco)
        sup.blit(img, (x, tarjeta.y + int(w * 0.02)))
        hora = cache_dibujo.texto(f_chica, _hora_mensaje(k), tenue)
        sup.blit(hora, hora.get_rect(topright=(tarjeta.right - int(w * 0.03), tarjeta.y + int(w * 0.025))))
        yy = tarjeta.y + int(w * 0.02) + img.get_height()
        for linea in lineas:
            img = cache_dibujo.texto(f_media, linea, (214, 218, 236))
            sup.blit(img, (x, yy))
            yy += f_media.get_linesize()
        y = tarjeta.bottom + int(w * 0.025)


def _hora_mensaje(k):
    """La hora de cada notificación (de la más nueva a la más vieja)."""
    horas = ["3:12", "2:58", "1:40", "11:03", "9:47", "8:15"]
    return horas[k] if k < len(horas) else ""
