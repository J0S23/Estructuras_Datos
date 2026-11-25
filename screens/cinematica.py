"""Las cinemáticas de la historia de los niños (docs/historia.md).

- `Cinematica`: la de apertura, antes del menú (main.py). Cinco escenas y la
  frase "Allá arriba, la mentira también tiene cuenta." Cualquier tecla,
  botón o clic la salta. Desde el menú se vuelve a ver con [H].
- `dibujar_final` / `intro_final_ms`: las escenas de los finales de la sala
  oculta (screens/final.py las usa en vez de las de siempre cuando
  `mision.final` dice cuál fue).

Los escenarios se dibujan en un lienzo chiquito de 320x180 (pixel art) que
se agranda con nearest, como el mapa; los celulares, los textos y los
personajes van encima, a la resolución de la pantalla, para que se lean.
Los textos salen de data/historia.py. Si el equipo manda una imagen para una
escena (Imagenes/Historia/escena_<n>.png), se usa de fondo en vez del dibujo.

Todo sale del tiempo `t`: sin estado (salvo los sonidos, que suenan una vez).
"""

import math
import os
import random

import pygame

from data.historia import (CINEMATICA, FRASE_APERTURA, FRASE_APERTURA_MS, CHAT_ESCENA_1,
                           NOTIFICACION_FINAL, FINALES, FRASE_FINAL)
from juego.fuentes import fuente_de_tamano
from juego import cache_dibujo
from juego.idioma import tr
from screens import arte_historia as arte

BASE = (320, 180)
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cache = {}

# Los colores de NEXUS en el celular del juego (screens/celular.py).
NX_PANTALLA = (238, 240, 247)
NX_TARJETA = (255, 255, 255)
NX_TEXTO = (30, 32, 44)
NX_TENUE = (110, 116, 140)
NX_MARCA = (52, 108, 220)
NX_ROJO = (225, 70, 70)
NX_VERDE = (60, 190, 110)
AMARILLO_LUGAR = (255, 214, 120)


def _suave(t, inicio, duracion):
    if t <= inicio:
        return 0.0
    x = min(1.0, (t - inicio) / max(1, duracion))
    return 1 - (1 - x) ** 3


def _guardar(clave, armar):
    img = _cache.get(clave)
    if img is None:
        if len(_cache) > 160:
            _cache.clear()
        img = _cache[clave] = armar()
    return img


def _f(px):
    return fuente_de_tamano(max(10, int(px)))


# -- El lienzo de pixel art y cómo se pega en la pantalla ---------------------------------

class Lienzo:
    """El lienzo de 320x180 y dónde queda en la pantalla (`area`, `s`)."""

    def __init__(self, screen):
        w, h = screen.get_size()
        s = min(w / BASE[0], h / BASE[1])
        if s >= 1:
            s = max(1, int(s)) if abs(s - round(s)) < 0.02 or s > 3 else s
        self.s = s
        self.area = pygame.Rect(0, 0, int(BASE[0] * s), int(BASE[1] * s))
        self.area.center = (w // 2, h // 2)
        self.sup = _guardar(("lienzo",), lambda: pygame.Surface(BASE))
        self.screen = screen

    def p(self, x, y):
        """Un punto del lienzo en la pantalla."""
        return (int(self.area.x + x * self.s), int(self.area.y + y * self.s))

    def pegar(self):
        self.screen.fill((0, 0, 0))
        grande = pygame.transform.scale(self.sup, self.area.size)
        self.screen.blit(grande, self.area.topleft)


def _degradado(sup, rect, arriba, abajo):
    for y in range(rect.height):
        k = y / max(1, rect.height - 1)
        color = tuple(int(a + (b - a) * k) for a, b in zip(arriba, abajo))
        pygame.draw.line(sup, color, (rect.x, rect.y + y), (rect.right - 1, rect.y + y))


def _brillo(sup, centro, radio, color):
    """Luz que se suma (en el lienzo)."""
    img = _guardar(("brillo", radio, color), lambda: _armar_brillo(radio, color))
    sup.blit(img, img.get_rect(center=centro), special_flags=pygame.BLEND_RGB_ADD)


def _armar_brillo(radio, color):
    img = pygame.Surface((radio * 2, radio * 2))
    img.fill((0, 0, 0))
    for r in range(radio, 0, -1):
        k = (1 - r / radio) ** 1.8
        pygame.draw.circle(img, tuple(int(c * k) for c in color), (radio, radio), r)
    return img


def _estrellas(sup, rect, t, semilla, cuantas=40):
    azar = random.Random(semilla)
    for _ in range(cuantas):
        x = rect.x + azar.randrange(rect.width)
        y = rect.y + azar.randrange(rect.height)
        fase = azar.random() * 6.28
        v = 120 + int(100 * (0.5 + 0.5 * math.sin(t / 500 + fase)))
        sup.set_at((x, y), (v, v, min(255, v + 30)))


def _sprite(ruta, alto, voltear=False):
    """El primer cuadro de una hoja (cuadros cuadrados en fila), recortado y
    escalado a `alto` con nearest. None si no está."""
    def armar():
        completa = os.path.join(_RAIZ, ruta)
        if not os.path.isfile(completa) or pygame.display.get_surface() is None:
            return None
        hoja = pygame.image.load(completa).convert_alpha()
        lado = hoja.get_height()
        cuadro = hoja.subsurface(pygame.Rect(0, 0, min(lado, hoja.get_width()), lado)).copy()
        caja = cuadro.get_bounding_rect()
        cuadro = cuadro.subsurface(caja).copy()
        k = alto / max(1, cuadro.get_height())
        img = pygame.transform.scale(cuadro, (max(1, int(cuadro.get_width() * k)), int(alto)))
        return pygame.transform.flip(img, True, False) if voltear else img
    return _guardar(("sprite", ruta, int(alto), voltear), armar)


# -- Textos -------------------------------------------------------------------------------

def _escrito(texto, t, por_segundo=42):
    """Lo que ya se escribió de `texto` a los `t` ms (máquina de escribir)."""
    return texto[:max(0, int(t / 1000 * por_segundo))]


def _linea_narrada(textos, t, total, voz=None, voz_desde=0):
    """(índice, ms dentro de la línea, lo que dura la línea) del subtítulo
    que va a los `t` ms de un tramo de `total` ms, o None (todavía no).
    Con la narración grabada (`voz`, que empieza a los `voz_desde` ms), cada
    línea sale cuando Lucas la empieza a decir (juego/voces.cortes); si no,
    se reparten parejo, como antes."""
    from juego import voces
    if not textos:
        return None
    marcas = voces.cortes(voz, len(textos)) if voz else None
    if marcas is None:
        tramo = total / len(textos)
        k = min(len(textos) - 1, int(max(0, t) // tramo))
        return k, t - k * tramo, tramo
    inicios = [voz_desde + m for m in marcas]
    if t < inicios[0]:
        return None
    k = max(i for i, ini in enumerate(inicios) if t >= ini)
    fin = inicios[k + 1] if k + 1 < len(inicios) else max(total, inicios[k] + 1500)
    return k, t - inicios[k], fin - inicios[k]


def _subtitulo(screen, area, texto, t, duracion):
    """El texto de abajo (como un documental): entra escribiéndose y se va
    desvaneciendo al final."""
    if not texto or t < 0:
        return
    from screens.paneles import partir_lineas
    f = _f(max(16, area.height * 0.034))
    texto = tr(texto)                      # (en inglés: se escribe ya traducido)
    # (se escribe a 55 letras por segundo; si la línea dura poco, como cuando
    # la narra Lucas, más rápido: escrita entera a los 2/3 de su tiempo)
    visible = _escrito(texto, t, max(55, len(texto) * 1000 / max(1.0, duracion * 0.66)))
    alfa = int(255 * min(1.0, (duracion - t) / 400)) if t > duracion - 400 else 255
    if alfa <= 0:
        return
    lineas = partir_lineas(texto, f, int(area.width * 0.8))
    y = area.bottom - int(area.height * 0.06) - f.get_linesize() * len(lineas)
    quedan = len(visible)
    fondo = pygame.Rect(0, 0, int(area.width * 0.86), f.get_linesize() * len(lineas) + 18)
    fondo.midtop = (area.centerx, y - 9)
    screen.blit(cache_dibujo.capa(fondo.size, (0, 0, 0, min(150, alfa) // 10 * 10)), fondo.topleft)
    for linea in lineas:
        parte = linea[:max(0, quedan)]
        quedan -= len(linea) + 1
        if parte:
            img = f.render(parte, True, (245, 244, 238))
            sombra = f.render(parte, True, (10, 10, 16))
            x = area.centerx - f.size(linea)[0] // 2
            if alfa < 255:
                img.set_alpha(alfa)
                sombra.set_alpha(alfa)
            screen.blit(sombra, (x + 2, y + 2))
            screen.blit(img, (x, y))
        y += f.get_linesize()


def _lugar(screen, area, texto, t):
    """El letrero de arriba a la izquierda ("Una habitación a oscuras. 11:47 p. m.")."""
    if t < 200:
        return
    f = _f(max(14, area.height * 0.034))
    texto = tr(texto)
    visible = _escrito(texto, t - 200, 34)
    cursor = "_" if (t // 400) % 2 == 0 or len(visible) < len(texto) else ""
    img = f.render(visible + cursor, True, AMARILLO_LUGAR)
    sombra = f.render(visible + cursor, True, (8, 8, 12))
    pos = (area.x + int(area.width * 0.04), area.y + int(area.height * 0.05))
    screen.blit(sombra, (pos[0] + 2, pos[1] + 2))
    screen.blit(img, pos)


def _pie_saltar(screen, area, t):
    if t < 1200:
        return
    f = _f(max(12, area.height * 0.02))
    img = cache_dibujo.texto(f, "[ESC] saltar", (150, 152, 170))
    screen.blit(img, img.get_rect(bottomright=(area.right - 16, area.bottom - 10)))


def _vineta(screen, area):
    img = _guardar(("vineta_cine", area.size), lambda: _armar_vineta(area.size))
    screen.blit(img, area.topleft)


def _armar_vineta(tam):
    chico = pygame.Surface((32, 18), pygame.SRCALPHA)
    for x in range(32):
        for y in range(18):
            d = math.hypot((x - 15.5) / 16, (y - 8.5) / 9)
            chico.set_at((x, y), (0, 0, 0, int(200 * max(0.0, d - 0.55) ** 1.4)))
    return pygame.transform.smoothscale(chico, tam)


# -- El celular (con el marco de Anny) --------------------------------------------------------

def _marco(alto):
    def armar():
        ruta = os.path.join(_RAIZ, "Imagenes", "UI", "celular_marco.png")
        if not os.path.isfile(ruta):
            return None
        img = pygame.image.load(ruta).convert_alpha()
        k = alto / img.get_height()
        return pygame.transform.smoothscale(img, (int(img.get_width() * k), int(alto)))
    return _guardar(("marco", int(alto)), armar)


def celular(screen, centro, alto, pintar, t, inclinado=0):
    """Un celular con el marco del juego. `pintar(pantalla_surface, t)`
    dibuja lo de adentro. Devuelve el rect del teléfono."""
    marco = _marco(alto)
    ancho = marco.get_width() if marco is not None else int(alto * 0.5)
    rect = pygame.Rect(0, 0, ancho, int(alto))
    rect.center = centro
    from screens.celular import PANTALLA_MARCO
    izq, arr, der, aba = PANTALLA_MARCO
    pantalla = pygame.Rect(int(ancho * izq), int(alto * arr), int(ancho * (1 - izq - der)),
                           int(alto * (1 - arr - aba)))
    sup = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    if marco is None:
        pygame.draw.rect(sup, (18, 18, 26), sup.get_rect(), border_radius=int(ancho * 0.12))
    else:
        sup.blit(marco, (0, 0))
    contenido = pygame.Surface(pantalla.size)
    pintar(contenido, t)
    # Con las esquinas redondeadas, encima de la pantalla del marco.
    contenido = contenido.convert_alpha()
    contenido.blit(_esquinas(pantalla.size, int(pantalla.width * 0.07)), (0, 0),
                   special_flags=pygame.BLEND_RGBA_MULT)
    sup.blit(contenido, pantalla.topleft)
    if inclinado:
        sup = pygame.transform.rotate(sup, inclinado)
    # La luz del teléfono en la oscuridad.
    luz = _guardar(("luz_cel", rect.width), lambda: _armar_brillo(int(rect.width * 0.9), (34, 44, 70)))
    screen.blit(luz, luz.get_rect(center=centro), special_flags=pygame.BLEND_RGB_ADD)
    screen.blit(sup, sup.get_rect(center=centro))
    return rect


def _esquinas(tam, radio):
    def armar():
        m = pygame.Surface(tam, pygame.SRCALPHA)
        m.fill((0, 0, 0, 0))
        pygame.draw.rect(m, (255, 255, 255, 255), m.get_rect(), border_radius=radio)
        return m
    return _guardar(("esquinas", tuple(tam), radio), armar)


def _barra_estado(sup, hora="11:47"):
    w = sup.get_width()
    f = _f(max(10, w * 0.055))
    img = f.render(hora, True, NX_TEXTO)
    sup.blit(img, (int(w * 0.08), int(w * 0.03)))
    for k in range(3):
        pygame.draw.rect(sup, NX_TEXTO, (w - int(w * 0.25) + k * int(w * 0.05), int(w * 0.07) - k * 2,
                                         max(2, int(w * 0.03)), 4 + k * 2))
    return img.get_height() + int(w * 0.05)


def _cabecera(sup, y, nombre, color_avatar, verificado=True, letra=None):
    w = sup.get_width()
    alto = int(w * 0.17)
    pygame.draw.rect(sup, NX_TARJETA, (0, y, w, alto))
    pygame.draw.line(sup, (214, 218, 230), (0, y + alto), (w, y + alto))
    r = int(alto * 0.34)
    centro = (int(w * 0.12), y + alto // 2)
    pygame.draw.circle(sup, color_avatar, centro, r)
    if letra:
        f = _f(r * 1.2)
        img = f.render(letra, True, (255, 255, 255))
        sup.blit(img, img.get_rect(center=centro))
    f = _f(max(10, w * 0.06))
    img = f.render(nombre, True, NX_TEXTO)
    sup.blit(img, (centro[0] + r + 8, centro[1] - img.get_height() // 2))
    if verificado:
        cx = centro[0] + r + 14 + img.get_width()
        pygame.draw.circle(sup, NX_MARCA, (cx, centro[1]), max(4, int(w * 0.025)))
        pygame.draw.lines(sup, (255, 255, 255), False, [(cx - 3, centro[1]), (cx - 1, centro[1] + 2), (cx + 3, centro[1] - 2)], 2)
    return y + alto


def _corazon(sup, centro, r, color):
    """Un corazón dibujado (la letra del juego no trae el símbolo)."""
    x, y = centro
    pygame.draw.circle(sup, color, (x - r // 2, y - r // 4), r // 2 + 1)
    pygame.draw.circle(sup, color, (x + r // 2, y - r // 4), r // 2 + 1)
    pygame.draw.polygon(sup, color, [(x - r, y - r // 6), (x + r, y - r // 6), (x, y + r)])


def _me_gusta(sup, pos, f, likes, color=None):
    color = color or NX_ROJO
    alto = f.get_height()
    _corazon(sup, (pos[0] + alto // 2, pos[1] + alto // 2), max(3, alto // 3), color)
    sup.blit(f.render(str(likes), True, color), (pos[0] + alto + 4, pos[1]))


def _palomitas(sup, pos, tam, color):
    x, y = pos
    for dx in (0, tam // 2 + 1):
        pygame.draw.lines(sup, color, False, [(x + dx, y + tam // 2), (x + dx + tam // 3, y + tam),
                                              (x + dx + tam, y)], 2)


def _burbuja(sup, texto, y, propia, w_max, f, color=None):
    """Una burbuja del chat. Devuelve dónde termina."""
    from screens.paneles import partir_lineas
    w = sup.get_width()
    lineas = partir_lineas(texto, f, int(w_max))
    ancho = max(f.size(l)[0] for l in lineas) + 18
    alto = f.get_linesize() * len(lineas) + 12
    caja = pygame.Rect(0, y, ancho, alto)
    if propia:
        caja.right = w - 10
        fondo, letra = color or NX_MARCA, (255, 255, 255)
    else:
        caja.left = 10
        fondo, letra = (226, 228, 238), NX_TEXTO
    pygame.draw.rect(sup, fondo, caja, border_radius=12)
    yy = caja.y + 6
    for linea in lineas:
        sup.blit(f.render(linea, True, letra), (caja.x + 9, yy))
        yy += f.get_linesize()
    return caja.bottom + 8


# ===========================================================================================
# La cinemática de apertura
# ===========================================================================================

# El narrador (docs/guion_narrador.md): apertura_1..5 y apertura_frase en
# Audio/Narrador. Cada escena dura lo que su texto o, si su narración es más
# larga, lo que la narración (juego/voces.py): la voz y la imagen van juntas.
VOZ_ESCENA_DESDE_MS = 500        # la narración entra después del fundido
VOZ_FRASE_DESDE_MS = 300


def duraciones_apertura():
    """(ms de cada escena, ms de la frase), alargados si la narración es más larga."""
    from juego import voces
    escenas = [max(e["ms"], VOZ_ESCENA_DESDE_MS + voces.ms_en_pantalla(f"apertura_{i + 1}") + 300)
               for i, e in enumerate(CINEMATICA)]
    frase = max(FRASE_APERTURA_MS, VOZ_FRASE_DESDE_MS + voces.ms_en_pantalla("apertura_frase") + 700)
    return escenas, frase


class Cinematica:
    def __init__(self, sonar=None):
        self.t = 0
        self.terminada = False
        self.sonar = sonar or (lambda nombre, volumen=1.0: None)
        self._sonados = set()
        self.duraciones, self.ms_frase = duraciones_apertura()
        self.inicios = []
        t = 0
        for ms in self.duraciones:
            self.inicios.append(t)
            t += ms
        self.inicio_frase = t
        self.total = t + self.ms_frase
        self.sonidos = _sonidos_apertura(self.inicios, self.inicio_frase)
        # Las narraciones: (ms, archivo).
        self.voces = [(inicio + VOZ_ESCENA_DESDE_MS, f"apertura_{i + 1}") for i, inicio in enumerate(self.inicios)]
        self.voces.append((self.inicio_frase + VOZ_FRASE_DESDE_MS, "apertura_frase"))

    def actualizar(self, dt):
        if self.terminada:
            return
        antes = self.t
        self.t += dt
        for momento, nombre, volumen in self.sonidos:
            if momento <= self.t and momento not in self._sonados:
                self._sonados.add(momento)
                self.sonar(nombre, volumen)
        for momento, nombre in self.voces:
            if antes < momento <= self.t or (momento == 0 and antes == 0):
                _voz(nombre)
        if self.t >= self.total:
            self.terminada = True

    def saltar(self):
        self.terminada = True
        _callar()

    def escena(self):
        """(índice, t dentro de la escena); índice = len(CINEMATICA) es la frase."""
        for i in range(len(CINEMATICA) - 1, -1, -1):
            if self.t >= self.inicios[i]:
                if i == len(CINEMATICA) - 1 and self.t >= self.inicio_frase:
                    return len(CINEMATICA), self.t - self.inicio_frase
                return i, self.t - self.inicios[i]
        return 0, self.t

    def dibujar(self, screen):
        i, t = self.escena()
        if i >= len(CINEMATICA):
            _frase(screen, FRASE_APERTURA, t, self.ms_frase, ("mentira",))
            return
        datos = dict(CINEMATICA[i], ms=self.duraciones[i])
        lienzo = Lienzo(screen)
        propia = arte.imagen(f"escena_{i + 1}")
        anim = t
        if i == 0:
            anclas = _anclas_escena_1(self.duraciones[0])
            if anclas:
                anim = _interpolar(anclas, t)      # (al paso de la narración)
        ESCENAS[i](lienzo, anim, propia)
        area = lienzo.area
        # Fundido de entrada y salida de cada escena.
        _vineta(screen, area)
        _lugar(screen, area, datos["lugar"], t)
        linea = _linea_narrada(datos["textos"], t, datos["ms"], f"apertura_{i + 1}", VOZ_ESCENA_DESDE_MS)
        if linea is not None:
            k, dentro, tramo = linea
            _subtitulo(screen, area, datos["textos"][k], dentro, tramo)
        negro = 0
        if t < 450:
            negro = 255 * (1 - t / 450)
        elif t > datos["ms"] - 450:
            negro = 255 * (1 - (datos["ms"] - t) / 450)
        if negro > 0:
            screen.blit(cache_dibujo.capa(screen.get_size(), (0, 0, 0, int(negro) // 8 * 8)), (0, 0))
        _pie_saltar(screen, area, self.t)


def _voz(nombre):
    """La narración `nombre` (Audio/Narrador), si está grabada."""
    from juego import voces
    if voces.ruta(nombre) is not None:
        from juego.audio_manager import audio_manager
        audio_manager.play_voz(nombre)


def _callar():
    from juego.audio_manager import audio_manager
    if audio_manager.sonando_voz:
        audio_manager.parar_voz()


def _anclas_escena_1(duracion):
    """La escena 1 va al paso de la narración de Lucas (apertura_1): el chat
    llega mientras dice "una niña... chatea", la dirección se escribe cuando
    dice "le escribe su dirección" y se envía con "y la envía". Pares (ms de
    la escena, ms de la animación); sin la narración o sin sus marcas, la
    animación va a su ritmo de siempre."""
    from juego import voces
    marcas = voces.cortes("apertura_1", len(CINEMATICA[0]["textos"]))
    fin = CINEMATICA[0]["ms"]
    if marcas is None or duracion <= fin:
        return None
    s0, s1 = VOZ_ESCENA_DESDE_MS + marcas[0], VOZ_ESCENA_DESDE_MS + marcas[1]
    anclas = [(0, 0), (max(600, s0 - 1800), 1200), (s0 + 300, 2400), (s1, 6400),
              (s1 + 2300, 8500), (s1 + 2700, 8900), (s1 + 3200, 9600), (duracion, fin)]
    ok = all(b[0] > a[0] and b[1] > a[1] for a, b in zip(anclas, anclas[1:]))
    return anclas if ok else None


def _interpolar(anclas, x, de=0, a=1):
    """De la columna `de` a la columna `a` de `anclas` (tramos rectos)."""
    for p, q in zip(anclas, anclas[1:]):
        if x <= q[de]:
            u = (x - p[de]) / max(1, q[de] - p[de])
            return p[a] + (q[a] - p[a]) * max(0.0, u)
    return anclas[-1][a] + (x - anclas[-1][de])


# Los sonidos de la apertura: (ms desde el principio, nombre, volumen).
def _sonidos_apertura(inicios=None, inicio_frase=None):
    sonidos = []
    if inicios is None:
        inicios, t = [], 0
        for escena in CINEMATICA:
            inicios.append(t)
            t += escena["ms"]
        inicio_frase = t
    for i, escena in enumerate(CINEMATICA):
        inicio = inicios[i]
        if i == 0:
            anclas = _anclas_escena_1(inicios[1] - inicio if len(inicios) > 1 else escena["ms"])
            for ms, nombre, volumen in ((2400, "nota", 0.5), (3800, "nota", 0.6), (5200, "nota", 0.6),
                                        (6400, "tecleo", 0.6), (7300, "tecleo", 0.6),
                                        (8500, "menu_ok", 0.6), (9700, "susurro", 0.7)):
                # (al paso de la narración, si la hay: _anclas_escena_1)
                cuando = _interpolar(anclas, ms, de=1, a=0) if anclas else ms
                sonidos.append((inicio + int(cuando), nombre, volumen))
        elif i == 1:
            sonidos += [(inicio + 400, "nota", 0.5), (inicio + 1500, "menu_ok", 0.5),
                        (inicio + 3000, "foto", 0.5), (inicio + 5600, "nota", 0.6)]
        elif i == 2:
            sonidos += [(inicio + k, "senal", 0.7) for k in (1200, 2200, 3200, 4200)]
            sonidos += [(inicio + 6500, "nota", 0.7)]
        elif i == 3:
            sonidos += [(inicio + k, "fallo", 0.45) for k in (1900, 4300, 6700)]
        elif i == 4:
            sonidos += [(inicio + 600, "ia_voz", 0.5), (inicio + 6000, "menu_mover", 0.6),
                        (inicio + 7000, "puerta", 0.8)]
    sonidos += [(inicio_frase + 300, "tecleo", 0.5), (inicio_frase + 1500, "susto", 0.35)]
    return sonidos



# -- Escena 1: la habitación, 11:47 p. m. ---------------------------------------------------

def _habitacion(sup, t, de_dia=False, con_nina=True, cama_vacia=False):
    w, h = BASE
    if de_dia:
        pared, piso = (84, 80, 108), (64, 56, 74)
    else:
        pared, piso = (18, 20, 40), (22, 20, 34)
    _degradado(sup, pygame.Rect(0, 0, w, 140), tuple(int(c * 0.8) for c in pared), pared)
    pygame.draw.rect(sup, piso, (0, 140, w, 40))
    pygame.draw.line(sup, tuple(int(c * 0.7) for c in piso), (0, 140), (w, 140))
    for x in range(0, w, 24):
        pygame.draw.line(sup, tuple(int(c * 0.85) for c in piso), (x, 141), (x - 14, 180))
    # La ventana con la noche (o la mañana) y la ciudad.
    ventana = pygame.Rect(18, 22, 58, 52)
    pygame.draw.rect(sup, (48, 46, 70) if not de_dia else (150, 140, 160), ventana.inflate(6, 6))
    if de_dia:
        _degradado(sup, ventana, (150, 200, 240), (250, 220, 180))
    else:
        _degradado(sup, ventana, (8, 10, 30), (30, 24, 62))
        _estrellas(sup, ventana, t, 3, 14)
        pygame.draw.circle(sup, (232, 230, 206), (64, 34), 6)
        pygame.draw.circle(sup, (200, 198, 176), (62, 33), 2)
    azar = random.Random(11)
    x = ventana.x
    while x < ventana.right:
        alto = azar.randint(8, 20)
        ancho = azar.randint(6, 12)
        edificio = pygame.Rect(x, ventana.bottom - alto, ancho, alto).clip(ventana)
        pygame.draw.rect(sup, (16, 14, 30) if not de_dia else (110, 110, 140), edificio)
        if not de_dia:
            for yy in range(edificio.y + 2, edificio.bottom - 1, 3):
                for xx in range(edificio.x + 1, edificio.right - 1, 3):
                    if azar.random() < 0.3:
                        sup.set_at((xx, yy), (230, 200, 110))
        x += ancho + 1
    pygame.draw.line(sup, (48, 46, 70) if not de_dia else (150, 140, 160), (ventana.centerx, ventana.y), (ventana.centerx, ventana.bottom))
    pygame.draw.line(sup, (48, 46, 70) if not de_dia else (150, 140, 160), (ventana.x, ventana.centery), (ventana.right, ventana.centery))
    # Cortinas.
    for lado in (ventana.x - 8, ventana.right + 2):
        pygame.draw.rect(sup, (90, 50, 110) if not de_dia else (170, 120, 190), (lado, 16, 6, 64))
    if de_dia:
        # La luz de la mañana que entra en el piso.
        luz = pygame.Surface((w, h))
        luz.fill((0, 0, 0))
        pygame.draw.polygon(luz, (60, 50, 30), [(ventana.x, ventana.bottom), (ventana.right, ventana.bottom),
                                                (ventana.right + 70, 176), (ventana.x + 30, 176)])
        sup.blit(luz, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    # El póster de su cantante favorita (una estrella y "LUNA").
    poster = pygame.Rect(96, 26, 24, 32)
    pygame.draw.rect(sup, (30, 20, 40), poster.inflate(2, 2))
    _degradado(sup, poster, (120, 60, 160), (220, 90, 140))
    pygame.draw.polygon(sup, (255, 230, 120), [(108, 30), (110, 36), (116, 36), (111, 40), (113, 46),
                                               (108, 42), (103, 46), (105, 40), (100, 36), (106, 36)])
    pygame.draw.rect(sup, (250, 240, 250), (101, 50, 14, 2))
    # La mesita de noche con el reloj.
    mesa = pygame.Rect(40, 118, 22, 22)
    pygame.draw.rect(sup, (50, 36, 40) if not de_dia else (120, 90, 80), mesa)
    pygame.draw.rect(sup, (30, 22, 26), mesa, 1)
    pygame.draw.rect(sup, (20, 10, 12), (44, 112, 14, 7))
    if not de_dia or (t // 500) % 2:
        for k, x in enumerate((45, 48, 52, 55)):
            pygame.draw.rect(sup, (230, 40, 40), (x, 114, 2, 3))
        sup.set_at((50, 114), (230, 40, 40))
        sup.set_at((50, 116), (230, 40, 40))
    # La cama.
    cabecera = pygame.Rect(70, 96, 8, 48)
    pygame.draw.rect(sup, (70, 46, 52) if not de_dia else (140, 100, 100), cabecera)
    colchon = pygame.Rect(76, 118, 132, 24)
    pygame.draw.rect(sup, (230, 228, 240), colchon)
    pygame.draw.rect(sup, (60, 40, 48), (76, 140, 132, 6))
    pygame.draw.rect(sup, (60, 40, 48), (200, 112, 8, 34))
    almohada = pygame.Rect(78, 112, 22, 10)
    pygame.draw.ellipse(sup, (240, 240, 250), almohada)
    if con_nina:
        # Sentada contra la almohada: la cobija le tapa las piernas.
        nina = arte.nino(0, despierto=True)
        sup.blit(nina, (90, 102))
    cobija = [(88, 121), (206, 120), (206, 142), (86, 142)]
    if cama_vacia:
        cobija = [(110, 124), (150, 118), (206, 126), (206, 142), (120, 144), (96, 136)]
    pygame.draw.polygon(sup, (110, 70, 160) if not de_dia else (150, 110, 200), cobija)
    for x in range(110, 200, 16):
        sup.set_at((x, 130), (250, 230, 140))
        sup.set_at((x + 6, 136), (250, 230, 140))


def _escena_1(lienzo, t, propia):
    sup = lienzo.sup
    if propia is not None:
        sup.blit(pygame.transform.scale(propia, BASE), (0, 0))
    else:
        _habitacion(sup, t)
        # La luz del celular en la cara (titila al final: algo verde).
        verde = t > 9600 and (t // 90) % 2 == 0
        _brillo(sup, (102, 114), 34, (40, 90, 60) if verde else (40, 60, 100))
        # Un carro que pasa: la luz cruza el techo.
        if 3600 < t < 5600:
            u = (t - 3600) / 2000
            _brillo(sup, (int(-40 + u * 400), 12), 30, (40, 36, 24))
    lienzo.pegar()
    screen, area = lienzo.screen, lienzo.area
    # El celular con el chat, a la derecha.
    if t > 1200:
        sube = 1 - _suave(t, 1200, 700)
        centro = (area.x + int(area.width * 0.76), area.centery + int(area.height * 0.01 + sube * area.height))
        celular(screen, centro, int(area.height * 0.74), lambda s, tt=t: _chat_escena_1(s, tt), t)


def _chat_escena_1(sup, t):
    sup.fill(NX_PANTALLA)
    w = sup.get_width()
    y = _barra_estado(sup)
    y = _cabecera(sup, y, CHAT_ESCENA_1["cuenta"], (220, 90, 150), letra="L")
    f = _f(max(11, w * 0.058))
    y += 10
    tiempos = [2400, 3800, 5200, 6400]
    for (quien, texto), desde in zip(CHAT_ESCENA_1["mensajes"], tiempos):
        if t < desde - 700 and quien == "cuenta":
            break
        if quien == "cuenta" and t < desde:
            # "escribiendo..."
            caja = pygame.Rect(10, y, 50, 26)
            pygame.draw.rect(sup, (226, 228, 238), caja, border_radius=12)
            for k in range(3):
                dy = int(3 * math.sin(t / 120 + k))
                pygame.draw.circle(sup, NX_TENUE, (caja.x + 14 + k * 11, caja.centery + dy), 3)
            break
        if t < desde:
            break
        if quien == "ella" and desde == tiempos[-1]:
            texto = _escrito(tr(texto), t - desde, 14)
            if not texto:
                break
        y = _burbuja(sup, texto, y, quien == "ella", w * 0.72, f)
    if t > 8500:
        f2 = _f(max(10, w * 0.045))
        enviado = t > 8900
        img = f2.render("Enviado" if enviado else "Enviando...", True, NX_TENUE)
        caja = img.get_rect(topright=(w - 12 - (img.get_height() * 2 if enviado else 0), y - 4))
        sup.blit(img, caja)
        if enviado:
            _palomitas(sup, (caja.right + 4, caja.y + 2), img.get_height() - 4, NX_MARCA)
    # Al final la pantalla parpadea en verde.
    if t > 9600 and (t // 90) % 2 == 0:
        sup.fill((40, 160, 90), special_flags=pygame.BLEND_RGB_MULT)
    # La caja para escribir.
    caja = pygame.Rect(8, sup.get_height() - int(w * 0.16), w - 16, int(w * 0.12))
    pygame.draw.rect(sup, NX_TARJETA, caja, border_radius=14)
    pygame.draw.rect(sup, (214, 218, 230), caja, 1, border_radius=14)
    pygame.draw.circle(sup, NX_MARCA, (caja.right - caja.height // 2, caja.centery), caja.height // 2 - 3)


# -- Escena 2: otras pantallas ---------------------------------------------------------------

def _escena_2(lienzo, t, propia):
    sup = lienzo.sup
    if propia is not None:
        sup.blit(pygame.transform.scale(propia, BASE), (0, 0))
    else:
        _degradado(sup, sup.get_rect(), (12, 8, 26), (34, 16, 52))
        for k in range(18):
            azar = random.Random(k)
            x = int((azar.random() * 360 + t * 0.006 * (1 + k % 3)) % 360) - 20
            y = int(azar.random() * 180)
            pygame.draw.circle(sup, (40, 30, 70), (x, y), 1 + k % 3)
    lienzo.pegar()
    screen, area = lienzo.screen, lienzo.area
    alto = int(area.height * 0.7)
    for k, (desde, pintar, giro) in enumerate(((0, _pantalla_ubicacion, 4), (2600, _pantalla_foto, -2),
                                                (5200, _pantalla_secreto, 3))):
        if t < desde:
            continue
        u = _suave(t, desde, 600)
        centro = (area.x + int(area.width * (0.2 + 0.3 * k)),
                  area.centery - int(area.height * 0.04) + int((1 - u) * area.height * 0.6))
        celular(screen, centro, alto, lambda s, tt=t - desde, p=pintar: p(s, tt), t, inclinado=giro)


def _pantalla_ubicacion(sup, t):
    sup.fill(NX_PANTALLA)
    w, h = sup.get_size()
    y = _barra_estado(sup, "19:20")
    y = _cabecera(sup, y, "#RetoNocturno", (240, 150, 50), verificado=False, letra="#")
    mapa = pygame.Rect(0, y, w, int(h * 0.48))
    pygame.draw.rect(sup, (214, 232, 214), mapa)
    for x in range(mapa.x - 20, mapa.right, 28):
        pygame.draw.line(sup, (250, 250, 250), (x, mapa.y), (x + 30, mapa.bottom), 5)
    for yy in range(mapa.y + 10, mapa.bottom, 30):
        pygame.draw.line(sup, (250, 250, 250), (mapa.x, yy), (mapa.right, yy - 10), 4)
    pin = (mapa.centerx, mapa.centery)
    r = int(10 + 8 * ((t % 1200) / 1200))
    pygame.draw.circle(sup, (120, 170, 250), pin, r, 2)
    pygame.draw.circle(sup, NX_MARCA, pin, 7)
    pygame.draw.circle(sup, (255, 255, 255), pin, 3)
    f = _f(max(10, w * 0.055))
    caja = pygame.Rect(8, mapa.bottom + 10, w - 16, int(h * 0.16))
    pygame.draw.rect(sup, NX_TARJETA, caja, border_radius=10)
    sup.blit(f.render("Compartir ubicación", True, NX_TEXTO), (caja.x + 10, caja.y + 8))
    sup.blit(f.render("en vivo", True, NX_TEXTO), (caja.x + 10, caja.y + 8 + f.get_linesize()))
    prendido = t > 1100
    interruptor = pygame.Rect(0, 0, int(w * 0.2), int(w * 0.11))
    interruptor.midright = (caja.right - 10, caja.centery)
    pygame.draw.rect(sup, NX_VERDE if prendido else (190, 192, 204), interruptor, border_radius=interruptor.h // 2)
    x = interruptor.right - interruptor.h // 2 if prendido else interruptor.x + interruptor.h // 2
    pygame.draw.circle(sup, (255, 255, 255), (x, interruptor.centery), interruptor.h // 2 - 3)


def _pantalla_foto(sup, t):
    sup.fill(NX_PANTALLA)
    w, h = sup.get_size()
    y = _barra_estado(sup, "7:02")
    y = _cabecera(sup, y, "@mateo_2015", (90, 160, 230), verificado=False, letra="M")
    foto = pygame.Rect(0, y, w, int(w * 0.95))
    _degradado(sup, foto, (190, 210, 236), (240, 236, 222))
    pygame.draw.rect(sup, (60, 120, 70), (foto.x + 10, foto.y + 14, int(w * 0.5), int(w * 0.26)))   # tablero
    nino = arte.nino_grande(1, max(2, int(w * 0.022)), despierto=True)
    sup.blit(nino, nino.get_rect(midbottom=(foto.centerx, foto.bottom)))
    # El letrero del colegio (en la foto: se ve el nombre).
    letrero = pygame.Rect(foto.right - int(w * 0.46), foto.y + 8, int(w * 0.42), int(w * 0.13))
    pygame.draw.rect(sup, (30, 50, 110), letrero, border_radius=4)
    f = _f(max(9, w * 0.042))
    img = f.render("COLEGIO SAN MARTÍN", True, (250, 240, 200))
    sup.blit(img, img.get_rect(center=letrero.center))
    y = foto.bottom + 8
    f2 = _f(max(10, w * 0.052))
    sup.blit(f2.render("¡Primer día! Grado 5B", True, NX_TEXTO), (10, y))
    likes = int(min(1.0, t / 3000) * 214)
    _me_gusta(sup, (10, y + f2.get_linesize() + 4), f2, likes)


def _pantalla_secreto(sup, t):
    sup.fill(NX_PANTALLA)
    w = sup.get_width()
    y = _barra_estado(sup, "22:58")
    y = _cabecera(sup, y, "@nuevo_amigo_77", (150, 150, 160), verificado=False, letra="?")
    f = _f(max(11, w * 0.058))
    y += 10
    mensajes = [(200, "Vi tus videos. Eres muy talentoso."), (1300, "Te puedo ayudar a ser famoso."),
                (2600, "No le cuentes a tus papás, es nuestro secreto.")]
    for desde, texto in mensajes:
        if t < desde:
            break
        y = _burbuja(sup, texto, y, False, w * 0.76, f)
    if t > 2600:
        k = 0.5 + 0.5 * math.sin(t / 160)
        pygame.draw.rect(sup, (int(200 + 55 * k), 60, 60), sup.get_rect(), 3)


# -- Escena 3: la luz verde y la mañana ------------------------------------------------------

def _escena_3(lienzo, t, propia):
    sup = lienzo.sup
    w, h = BASE
    corte = 5200
    if propia is not None:
        sup.blit(pygame.transform.scale(propia, BASE), (0, 0))
    elif t < corte:
        _degradado(sup, pygame.Rect(0, 0, w, 140), (4, 6, 18), (20, 22, 52))
        _estrellas(sup, pygame.Rect(0, 0, w, 120), t, 9, 60)
        # La nave invisible: solo se nota porque tapa las estrellas y brilla un poco.
        nave = pygame.Rect(90, 6, 140, 22)
        pygame.draw.ellipse(sup, (6, 8, 20), nave)
        pygame.draw.ellipse(sup, (24, 40, 40), nave, 1)
        pygame.draw.rect(sup, (10, 12, 20), (0, 140, w, 40))
        casas = [(28, 100), (98, 96), (170, 102), (240, 98)]
        rayos = [1200, 2200, 3200, 4200]
        for (x, y), rayo in zip(casas, rayos):
            casa = pygame.Rect(x, y, 52, 140 - y)
            pygame.draw.rect(sup, (34, 34, 56), casa)
            pygame.draw.polygon(sup, (52, 34, 46), [(x - 4, y), (x + 26, y - 20), (x + 56, y)])
            pygame.draw.rect(sup, (22, 20, 30), (x + 20, y + 22, 12, 22))
            for vx in (x + 6, x + 36):
                encendida = (230, 200, 110)
                if rayo <= t < rayo + 900:
                    encendida = (120, 255, 160)
                elif t >= rayo + 900:
                    encendida = (24, 24, 36)
                pygame.draw.rect(sup, encendida, (vx, y + 8, 10, 9))
                pygame.draw.line(sup, (34, 34, 56), (vx + 5, y + 8), (vx + 5, y + 16))
            if rayo - 200 <= t < rayo + 900:
                u = min(1.0, (t - rayo + 200) / 300)
                rayo_rect = pygame.Rect(x + 6, 0, 40, int((y + 10) * u))
                luz = pygame.Surface(rayo_rect.size)
                luz.fill((30, 110, 60))
                sup.blit(luz, rayo_rect.topleft, special_flags=pygame.BLEND_RGB_ADD)
                _brillo(sup, (x + 26, y + 10), 30, (60, 200, 110))
                azar = random.Random(int(t // 60))
                for _ in range(10):
                    sup.set_at((x + 8 + azar.randrange(36), azar.randrange(max(1, y + 10))), (200, 255, 210))
    else:
        _habitacion(sup, t, de_dia=True, con_nina=False, cama_vacia=True)
        # El celular en el piso, con la pantalla prendida.
        pygame.draw.rect(sup, (20, 20, 28), (150, 154, 16, 9))
        pygame.draw.rect(sup, (150, 210, 255), (152, 155, 12, 7))
        _brillo(sup, (158, 158), 18, (40, 60, 90))
    lienzo.pegar()
    screen, area = lienzo.screen, lienzo.area
    if t < corte + 600 and t > corte - 600 and propia is None:
        k = 1 - abs(t - corte) / 600
        screen.blit(cache_dibujo.capa(screen.get_size(), (0, 0, 0, int(255 * k) // 8 * 8)), (0, 0))
    if t > corte + 1300:
        _notificacion(screen, area, t - corte - 1300)


def _notificacion(screen, area, t):
    """La notificación de NEXUS: "Gracias por compartir."."""
    u = _suave(t, 0, 500)
    w = int(area.width * 0.42)
    h = int(area.height * 0.13)
    caja = pygame.Rect(0, 0, w, h)
    caja.midtop = (area.centerx, area.y + int(area.height * 0.16) - int((1 - u) * h * 2))
    sombra = caja.move(4, 6)
    screen.blit(cache_dibujo.capa(sombra.size, (0, 0, 0, 120)), sombra.topleft)
    pygame.draw.rect(screen, (246, 247, 252), caja, border_radius=14)
    icono = pygame.Rect(0, 0, h - 20, h - 20)
    icono.midleft = (caja.x + 12, caja.centery)
    pygame.draw.rect(screen, NX_MARCA, icono, border_radius=8)
    logo = _logo(int(icono.height * 0.7))
    if logo is not None:
        screen.blit(logo, logo.get_rect(center=icono.center))
    f = _f(h * 0.25)
    f2 = _f(h * 0.3)
    screen.blit(f.render("NEXUS · ahora", True, NX_TENUE), (icono.right + 12, caja.y + int(h * 0.14)))
    screen.blit(f2.render(NOTIFICACION_FINAL, True, NX_TEXTO), (icono.right + 12, caja.y + int(h * 0.48)))


def _logo(alto):
    def armar():
        ruta = os.path.join(_RAIZ, "Imagenes", "UI", "nexus_icono.png")
        if not os.path.isfile(ruta):
            return None
        img = pygame.image.load(ruta).convert_alpha()
        return pygame.transform.smoothscale(img, (int(img.get_width() * alto / img.get_height()), int(alto)))
    return _guardar(("logo", int(alto)), armar)


# -- Escena 4: NEXUS borra lo de los niños --------------------------------------------------

PUBLICACIONES = [
    ("@valen.stars", (230, 120, 160), True, "¡Nuevo reto! Graba tu baile con #RetoGalaxia", "2,3 M", None),
    ("@papá_de_sofía", (120, 140, 170), False, "Mi hija Sofía no volvió a casa. Tiene 11 años. Por favor compartan.", "18", "borrar"),
    ("@el_mono_oficial", (240, 170, 50), True, "Lo que pasó anoche en la gala... no lo van a creer", "1,1 M", None),
    ("@profe_andrea", (110, 180, 130), False, "Tres de mis alumnos no han vuelto al colegio. ¿Alguien sabe algo?", "9", "borrar"),
    ("@luna.oficial", (220, 90, 150), True, "¡Gracias por tanto amor! Nos vemos en el concierto", "3,4 M", None),
    ("@noticias24", (90, 110, 200), True, "Dicen que los niños se escaparon de casa. Típico de esta generación.", "640 mil", None),
    ("@mamá_de_mateo", (170, 130, 110), False, "¿Alguien ha visto a Mateo? Desapareció el martes.", "4", "borrar"),
    ("@sebas.gamer", (130, 90, 220), True, "Nuevo look, ¿qué opinan?", "870 mil", None),
]


def _escena_4(lienzo, t, propia):
    sup = lienzo.sup
    if propia is not None:
        sup.blit(pygame.transform.scale(propia, BASE), (0, 0))
    else:
        _degradado(sup, sup.get_rect(), (8, 8, 18), (20, 14, 36))
    lienzo.pegar()
    screen, area = lienzo.screen, lienzo.area
    # El feed en el medio.
    feed = pygame.Rect(0, 0, int(area.width * 0.38), area.height)
    feed.midtop = (area.centerx, area.y)
    pygame.draw.rect(screen, NX_PANTALLA, feed)
    f = _f(max(12, area.height * 0.026))
    f_nombre = _f(max(12, area.height * 0.024))
    alto_tarjeta = int(area.height * 0.22)
    sube = t * area.height * 0.00009
    recorte = screen.get_clip()
    screen.set_clip(feed.clip(recorte))
    from screens.paneles import partir_lineas
    for k, (nombre, color, verificado, texto, likes, que) in enumerate(PUBLICACIONES):
        y = int(feed.y + area.height * 0.16 + k * (alto_tarjeta + 10) - sube)
        tarjeta = pygame.Rect(feed.x + 10, y, feed.width - 20, alto_tarjeta)
        if tarjeta.bottom < feed.y or tarjeta.top > feed.bottom:
            continue
        borrada = que == "borrar" and tarjeta.centery < area.y + area.height * 0.58
        glitch = que == "borrar" and area.y + area.height * 0.58 <= tarjeta.centery < area.y + area.height * 0.64
        pygame.draw.rect(screen, NX_TARJETA if not borrada else (226, 228, 236), tarjeta, border_radius=10)
        if borrada:
            img = f.render("Esta publicación fue eliminada.", True, NX_TENUE)
            screen.blit(img, img.get_rect(center=tarjeta.center))
            continue
        r = int(alto_tarjeta * 0.16)
        centro = (tarjeta.x + 12 + r, tarjeta.y + 10 + r)
        pygame.draw.circle(screen, color, centro, r)
        img = f_nombre.render(nombre, True, NX_TEXTO)
        screen.blit(img, (centro[0] + r + 8, centro[1] - img.get_height() // 2))
        if verificado:
            cx = centro[0] + r + 16 + img.get_width()
            pygame.draw.circle(screen, NX_MARCA, (cx, centro[1]), 6)
        yy = centro[1] + r + 6
        for linea in partir_lineas(texto, f, tarjeta.width - 24)[:3]:
            screen.blit(f.render(linea, True, NX_TEXTO), (tarjeta.x + 12, yy))
            yy += f.get_linesize()
        _me_gusta(screen, (tarjeta.x + 12, tarjeta.bottom - f.get_linesize() - 6), f, likes)
        if glitch:
            for dx, c in ((-6, (255, 40, 80)), (6, (40, 220, 255))):
                capa = cache_dibujo.capa(tarjeta.size, (*c, 70))
                screen.blit(capa, tarjeta.move(dx, 0).topleft)
            for _ in range(5):
                yy = random.randint(tarjeta.top, tarjeta.bottom - 4)
                pygame.draw.rect(screen, (30, 30, 40), (tarjeta.x, yy, tarjeta.width, 3))
    # La cabecera del feed.
    cabeza = pygame.Rect(feed.x, feed.y, feed.width, int(area.height * 0.1))
    pygame.draw.rect(screen, NX_TARJETA, cabeza)
    logo = _logo(int(cabeza.height * 0.6))
    if logo is not None:
        screen.blit(logo, logo.get_rect(midleft=(cabeza.x + 14, cabeza.centery)))
    img = _f(cabeza.height * 0.36).render("NEXUS", True, NX_MARCA)
    screen.blit(img, img.get_rect(center=cabeza.center))
    screen.set_clip(recorte)
    # A la izquierda: cuántos niños faltan.
    contador = int(12 + (347 - 12) * _suave(t, 300, 7000))
    panel = pygame.Rect(0, 0, int(area.width * 0.24), int(area.height * 0.3))
    panel.midright = (feed.left - int(area.width * 0.04), area.centery - int(area.height * 0.05))
    screen.blit(cache_dibujo.capa(panel.size, (40, 8, 12, 200)), panel.topleft)
    pygame.draw.rect(screen, (200, 50, 50), panel, 2)
    f1 = _f(panel.height * 0.11)
    img = f1.render("NIÑOS DESAPARECIDOS", True, (250, 200, 190))
    if img.get_width() > panel.width - 10:
        img = pygame.transform.smoothscale(img, (panel.width - 10, int(img.get_height() * (panel.width - 10) / img.get_width())))
    screen.blit(img, img.get_rect(midtop=(panel.centerx, panel.y + 10)))
    f2 = _f(panel.height * 0.42)
    img = f2.render(str(contador), True, (255, 80, 70))
    screen.blit(img, img.get_rect(center=(panel.centerx, panel.centery + int(panel.height * 0.08))))
    img = f1.render("en todo el mundo", True, (200, 150, 150))
    screen.blit(img, img.get_rect(midbottom=(panel.centerx, panel.bottom - 8)))
    # A la derecha: de qué se habla (de los niños, no).
    tendencias = pygame.Rect(0, 0, int(area.width * 0.22), int(area.height * 0.42))
    tendencias.midleft = (feed.right + int(area.width * 0.04), area.centery - int(area.height * 0.05))
    screen.blit(cache_dibujo.capa(tendencias.size, (20, 22, 40, 210)), tendencias.topleft)
    pygame.draw.rect(screen, NX_MARCA, tendencias, 2)
    f3 = _f(tendencias.height * 0.075)
    y = tendencias.y + 10
    screen.blit(f3.render("TENDENCIAS", True, (200, 210, 250)), (tendencias.x + 12, y))
    y += f3.get_linesize() + 6
    for etiqueta, cifra in (("#RetoGalaxia", "2,3 M"), ("#GalaDeAnoche", "1,1 M"), ("#LunaEnConcierto", "870 mil"),
                            ("#NuevoLook", "640 mil")):
        screen.blit(f3.render(etiqueta, True, (240, 242, 252)), (tendencias.x + 12, y))
        y += f3.get_linesize()
        screen.blit(f3.render(cifra, True, (150, 156, 190)), (tendencias.x + 12, y))
        y += f3.get_linesize() + 4


# -- Escena 5: la sala del gobierno -----------------------------------------------------------

ROLES = ("Tecnomante", "Forjador", "Biomante", "Resonante")


def _escena_5(lienzo, t, propia):
    sup = lienzo.sup
    w, h = BASE
    if propia is not None:
        sup.blit(pygame.transform.scale(propia, BASE), (0, 0))
    else:
        _degradado(sup, pygame.Rect(0, 0, w, 130), (10, 12, 22), (18, 22, 36))
        pygame.draw.rect(sup, (16, 18, 28), (0, 130, w, 50))
        for x in range(0, w, 20):
            pygame.draw.line(sup, (22, 24, 36), (x, 130), (x - 30, 180))
        # La bandera de Colombia en la pared.
        bandera = pygame.Rect(16, 30, 42, 28)
        pygame.draw.rect(sup, (40, 40, 50), bandera.inflate(2, 2))
        pygame.draw.rect(sup, (252, 209, 22), (bandera.x, bandera.y, bandera.w, bandera.h // 2))
        pygame.draw.rect(sup, (0, 56, 147), (bandera.x, bandera.y + bandera.h // 2, bandera.w, bandera.h // 4))
        pygame.draw.rect(sup, (206, 17, 38), (bandera.x, bandera.y + bandera.h * 3 // 4, bandera.w, bandera.h - bandera.h * 3 // 4))
        pygame.draw.line(sup, (90, 90, 100), (bandera.x - 2, bandera.y - 2), (bandera.x - 2, 130))
        # La pantalla grande: la Tierra, la órbita y la nave invisible.
        pantalla = pygame.Rect(84, 14, 152, 84)
        pygame.draw.rect(sup, (50, 54, 74), pantalla.inflate(6, 6))
        _degradado(sup, pantalla, (6, 16, 34), (8, 26, 48))
        for y in range(pantalla.y, pantalla.bottom, 3):
            pygame.draw.line(sup, (10, 22, 42), (pantalla.x, y), (pantalla.right - 1, y))
        tierra = (130, 58)
        pygame.draw.circle(sup, (30, 80, 160), tierra, 22)
        azar = random.Random(4)
        for _ in range(7):
            pygame.draw.circle(sup, (50, 140, 80), (tierra[0] + azar.randint(-14, 14), tierra[1] + azar.randint(-14, 14)),
                               azar.randint(3, 7))
        pygame.draw.circle(sup, (120, 180, 240), tierra, 22, 1)
        orbita = pygame.Rect(0, 0, 90, 34)
        orbita.center = tierra
        pygame.draw.ellipse(sup, (70, 120, 150), orbita, 1)
        a = t / 900
        nave = (int(tierra[0] + math.cos(a) * 45), int(tierra[1] + math.sin(a) * 17))
        if (t // 300) % 2:
            pygame.draw.circle(sup, (255, 80, 70), nave, 3, 1)
            pygame.draw.circle(sup, (255, 80, 70), nave, 1)
        # Los famosos conectados a la nave.
        for k in range(6):
            cara = pygame.Rect(196 + (k % 2) * 18, 22 + (k // 2) * 22, 14, 14)
            pygame.draw.rect(sup, (60, 30 + k * 20, 90 + k * 20), cara)
            pygame.draw.rect(sup, (200, 200, 220), cara, 1)
            if t > 2500 + k * 300:
                pygame.draw.line(sup, (200, 60, 60), cara.midleft, nave)
        x_scan = pantalla.x + int((t * 0.05) % pantalla.width)
        pygame.draw.line(sup, (60, 140, 180), (x_scan, pantalla.y), (x_scan, pantalla.bottom - 1))
        # La mesa con el holograma.
        mesa = pygame.Rect(70, 128, 180, 14)
        pygame.draw.rect(sup, (36, 40, 56), mesa)
        pygame.draw.rect(sup, (60, 66, 90), (mesa.x, mesa.y, mesa.w, 3))
        _brillo(sup, (mesa.centerx, mesa.y - 6), 40, (20, 60, 90))
    lienzo.pegar()
    screen, area = lienzo.screen, lienzo.area
    # Los cuatro agentes, de espaldas mirando la pantalla; al final se voltean.
    s = lienzo.s
    alto = int(54 * s)
    mira = "north" if t < 6000 else "south"
    for k, rol in enumerate(ROLES):
        img = _sprite(os.path.join("Imagenes", "Personajes", rol, f"{rol}_idle_{mira}.png"), alto)
        if img is None:
            continue
        pie = lienzo.p(108 + k * 36, 170)
        screen.blit(img, img.get_rect(midbottom=pie))
    if t > 7000:
        u = _suave(t, 7000, 350)
        f = _f(area.height * 0.06 * (1.6 - 0.6 * u))
        texto = f.render("MISIÓN SECRETA", True, (230, 60, 50))
        marco = texto.get_rect().inflate(30, 16)
        sello = pygame.Surface(marco.size, pygame.SRCALPHA)
        pygame.draw.rect(sello, (230, 60, 50), sello.get_rect(), 4, border_radius=6)
        sello.blit(texto, texto.get_rect(center=sello.get_rect().center))
        sello = pygame.transform.rotate(sello, -8)
        sello.set_alpha(int(230 * u))
        screen.blit(sello, sello.get_rect(center=(area.centerx + int(area.width * 0.22), area.y + int(area.height * 0.66))))


ESCENAS = [_escena_1, _escena_2, _escena_3, _escena_4, _escena_5]


def _frase(screen, frase, t, duracion, glitch=()):
    """La frase sola en negro, escribiéndose; las palabras de `glitch` fallan."""
    screen.fill((0, 0, 0))
    w, h = screen.get_size()
    tam = max(20, h * 0.045)
    f = _f(tam)
    frase = tr(frase)
    glitch = [tr(p) for p in glitch]
    while f.size(frase)[0] > w * 0.9 and tam > 12:     # (que quepa en una pantalla angosta)
        tam -= 2
        f = _f(tam)
    visible = _escrito(frase, t - 300, 26)
    alfa = 255 if t < duracion - 700 else int(255 * max(0.0, (duracion - t) / 700))
    img = f.render(visible, True, (240, 238, 232))
    x = w // 2 - f.size(frase)[0] // 2
    y = h // 2 - img.get_height() // 2
    for palabra in glitch:
        i = frase.find(palabra)
        if i >= 0 and len(visible) >= i + len(palabra) and (t // 110) % 5 == 0:
            dx = f.size(frase[:i])[0]
            for corr, c in ((-3, (255, 40, 80)), (3, (40, 220, 255))):
                fantasma = f.render(palabra, True, c)
                fantasma.set_alpha(150)
                screen.blit(fantasma, (x + dx + corr, y))
    img.set_alpha(alfa)
    screen.blit(img, (x, y))


# ===========================================================================================
# Los finales de la sala oculta (screens/final.py)
# ===========================================================================================

# (ms de la parte con dibujo, ms de los textos, ms de la frase final)
TIEMPOS_FINAL = {
    "sin_entrar": (5200, 6000, 4200),
    "escaparon": (5200, 6000, 4200),
    "quedarse": (6400, 6000, 4200),
    "nadie": (6400, 6000, 4200),
    "liberados": (6200, 9600, 4800),
}
# Cuánto antes del final del dibujo empiezan los textos de la escena.
ADELANTO_TEXTOS = {"sin_entrar": 1200, "liberados": 3400}


VOZ_FINAL_DESDE_MS = 300        # la narración entra un poco después que el primer texto


def _voces_final(final):
    """(narración de los textos, narración de la frase) de ese final (docs/guion_narrador.md)."""
    frase = "final_frase_liberados" if FINALES.get(final, {}).get("frase") else "final_frase"
    return f"final_{final}", frase


def tiempos_final(final):
    """(dibujo, textos, frase) en ms: los de TIEMPOS_FINAL o, si la narración
    es más larga, lo que dura la narración (la voz y los textos van juntos)."""
    from juego import voces
    a, b, c = TIEMPOS_FINAL.get(final, (0, 0, 0))
    if not a:
        return 0, 0, 0
    adelanto = ADELANTO_TEXTOS.get(final, 0)
    textos, frase = _voces_final(final)
    if voces.duracion_ms(textos):
        b = max(b, VOZ_FINAL_DESDE_MS + voces.ms_en_pantalla(textos) + 300 - adelanto)
    if voces.duracion_ms(frase):
        c = max(c, VOZ_FINAL_DESDE_MS + voces.ms_en_pantalla(frase) + 700)
    return a, b, c


def intro_final_ms(final):
    a, b, c = tiempos_final(final)
    return a + b + c


_narrando = {"final": None, "t": -1}


def _narrar_final(final, t):
    """Suena la narración del final cuando le toca (una vez cada una)."""
    a, b, c = tiempos_final(final)
    antes = _narrando["t"] if _narrando["final"] == final and _narrando["t"] <= t else -1
    _narrando.update(final=final, t=t)
    textos, frase = _voces_final(final)
    desde = a - ADELANTO_TEXTOS.get(final, 0) + VOZ_FINAL_DESDE_MS
    for momento, nombre in ((desde, textos), (a + b + VOZ_FINAL_DESDE_MS, frase)):
        if antes < momento <= t:
            _voz(nombre)


def dibujar_final(screen, final, t, jugadores=(), de_fondo=False):
    """La escena de ese final a los `t` ms. Con `de_fondo` (ya pasó la intro y
    van los resultados encima) solo el dibujo, quieto."""
    from screens import final as escenas
    a, b, c = tiempos_final(final)
    if de_fondo:
        if _narrando["final"] is not None:
            # (si saltaron la escena, la narración se corta con ella)
            _narrando.update(final=None, t=-1)
            _callar()
    else:
        _narrar_final(final, t)
    textos = FINALES[final]["escena"]
    w, h = screen.get_size()
    area = screen.get_rect()
    if de_fondo:
        if final in ("sin_entrar", "escaparon"):
            escenas._escena_escape(screen, 6000 + t % 60000)
        elif final == "quedarse":
            escenas._escena_celdas(screen, 5000, list(jugadores), patrulla="cambiaformas")
        elif final == "liberados":
            _manana(screen, 2000 + t % 60000, con_celular=False)
            escenas_oscuras(screen, 90)
        else:
            escenas._escena_celdas(screen, 5000, list(jugadores))
        return
    if t < a + b:
        # El dibujo (y después, los textos encima de su continuación).
        if final in ("sin_entrar", "escaparon"):
            if final == "escaparon" and t >= a:
                escenas._escena_escape(screen, t)
                escenas.oscurecer(screen, 170)
                _noticia_viral(screen, t - a)
            else:
                escenas._escena_escape(screen, t)
                if t > a:
                    escenas.oscurecer(screen, int(min(140, (t - a) / 6)))
        elif final == "quedarse":
            # Como la derrota normal (las celdas), pero patrulla el
            # Cambiaformas (Diego, nov 25: antes los aliens se amontonaban).
            if t < a:
                escenas._escena_celdas(screen, t, list(jugadores), patrulla="cambiaformas")
            else:
                _feed_sigue(screen, t - a)
        elif final == "liberados":
            if t < a:
                escenas._escena_escape(screen, t)
            else:
                _manana(screen, t - a)
        else:
            if t < a:
                _guardia_final(screen, t)
            else:
                escenas._escena_celdas(screen, t - a, list(jugadores))
                _titular_falso(screen, t - a)
        adelanto = ADELANTO_TEXTOS.get(final, 0)
        if t >= a - max(1200, adelanto):
            desde = a - adelanto
            dentro = t - desde
            if dentro >= 0:
                linea = _linea_narrada(textos, dentro, b + adelanto, _voces_final(final)[0],
                                       VOZ_FINAL_DESDE_MS)
                if linea is not None:
                    k, en_linea, tramo = linea
                    _subtitulo(screen, area, textos[k], en_linea, tramo)
        if t > a - 300 and t < a + 300 and final in ("quedarse", "nadie", "liberados"):
            k = 1 - abs(t - a) / 300
            screen.blit(cache_dibujo.capa((w, h), (0, 0, 0, int(255 * k) // 8 * 8)), (0, 0))
        return
    frase = FINALES[final].get("frase", FRASE_FINAL)
    _frase(screen, frase, t - a - b, c, ("dirección", "compartes", "lugar"))


def _noticia_viral(screen, t):
    """El final "escaparon": por fin NEXUS habla de los niños."""
    area = screen.get_rect()
    alto = int(area.height * 0.72)

    def pintar(sup, tt):
        sup.fill(NX_PANTALLA)
        sw = sup.get_width()
        y = _barra_estado(sup, "6:15")
        y = _cabecera(sup, y, "@agentes.colombia", (252, 209, 22), letra="A")
        f = _f(max(11, sw * 0.062))
        from screens.paneles import partir_lineas
        y += 8
        for linea in partir_lineas("Los niños desaparecidos están en la nave. Lo vimos.", f, sw - 24):
            sup.blit(f.render(linea, True, NX_TEXTO), (12, y))
            y += f.get_linesize()
        foto = pygame.Rect(8, y + 6, sw - 16, int(sw * 0.62))
        pygame.draw.rect(sup, (16, 30, 24), foto)
        for k in range(4):
            cap = arte.capsula(k, max(1, foto.height / 90))
            if cap is not None:
                sup.blit(cap, cap.get_rect(midbottom=(foto.x + int(foto.width * (0.14 + 0.24 * k)), foto.bottom)))
        y = foto.bottom + 10
        compartido = int(12_400_000 * _suave(tt, 300, 4500))
        texto = f"{compartido:,}".replace(",", ".")
        f2 = _f(max(11, sw * 0.06))
        sup.blit(f2.render(f"Compartido {texto} veces", True, NX_VERDE), (12, y))
        sup.blit(f2.render("TENDENCIA #1 en el mundo", True, NX_MARCA), (12, y + f2.get_linesize() + 4))
    celular(screen, (area.centerx, int(area.height * 0.44)), alto, pintar, t)


def _manana(screen, t, con_celular=True):
    """El final "liberados": a la mañana siguiente, la niña de vuelta en su
    cuarto; después, en el celular, la noticia de que volvieron."""
    lienzo = Lienzo(screen)
    _habitacion(lienzo.sup, t, de_dia=True, con_nina=True)
    # La luz de la mañana que va subiendo.
    _brillo(lienzo.sup, (46, 48), int(40 + 10 * _suave(t, 0, 3000)), (60, 50, 30))
    lienzo.pegar()
    if t < 700:
        k = 1 - t / 700
        screen.blit(cache_dibujo.capa(screen.get_size(), (0, 0, 0, int(255 * k) // 8 * 8)), (0, 0))
    if not con_celular or t < 3600:
        return
    area = lienzo.area
    sube = 1 - _suave(t, 3600, 800)
    centro = (area.x + int(area.width * 0.76), area.centery + int(area.height * 0.02 + sube * area.height))
    celular(screen, centro, int(area.height * 0.76), _noticia_volvieron, t - 3600)


def _noticia_volvieron(sup, t):
    sup.fill(NX_PANTALLA)
    sw = sup.get_width()
    y = _barra_estado(sup, "7:02")
    y = _cabecera(sup, y, "@noticias.colombia", NX_MARCA, letra="N")
    f = _f(max(10, sw * 0.058))
    from screens.paneles import partir_lineas
    y += 6
    for linea in partir_lineas("Volvieron los niños desaparecidos. Dicen que unos agentes los sacaron de la nave.",
                               f, sw - 20):
        sup.blit(f.render(linea, True, NX_TEXTO), (10, y))
        y += f.get_linesize()
    # La foto: los niños, de pie, con el cielo de la mañana.
    foto = pygame.Rect(8, y + 6, sw - 16, int(sw * 0.5))
    _degradado(sup, foto, (150, 200, 240), (250, 220, 180))
    pygame.draw.rect(sup, (110, 150, 110), (foto.x, foto.bottom - foto.height // 5, foto.width, foto.height // 5))
    from data.historia import APAGADAS, SE_APAGA, CAPSULAS
    vivos = [i for i in range(CAPSULAS) if i not in APAGADAS and i != SE_APAGA.get("capsula")]
    for k, i in enumerate(vivos):
        chico = arte.nino(i, despierto=True)
        escala = foto.height * 0.62 / chico.get_height()
        img = pygame.transform.scale(chico, (max(1, int(chico.get_width() * escala)), max(1, int(chico.get_height() * escala))))
        sup.blit(img, img.get_rect(midbottom=(foto.x + int(foto.width * (k + 0.5) / len(vivos)), foto.bottom - 2)))
    y = foto.bottom + 8
    compartido = int(9_800_000 * _suave(t, 300, 4500))
    f2 = _f(max(10, sw * 0.056))
    sup.blit(f2.render(f"Compartido {compartido:,} veces".replace(",", "."), True, NX_VERDE), (10, y))
    y += f2.get_linesize() + 8
    # Lo de los agentes, más abajo (sale después).
    if t > 2600:
        tarjeta = pygame.Rect(6, y, sw - 12, int(sw * 0.3))
        pygame.draw.rect(sup, NX_TARJETA, tarjeta, border_radius=8)
        pygame.draw.circle(sup, (252, 209, 22), (tarjeta.x + 14, tarjeta.y + 14), 9)
        sup.blit(f2.render("#NoVolvieron", True, NX_ROJO), (tarjeta.x + 28, tarjeta.y + 6))
        ly = tarjeta.y + 6 + f2.get_linesize() + 2
        for linea in partir_lineas("Los agentes se quedaron arriba para que ellos pudieran bajar.", f2, tarjeta.width - 14)[:2]:
            sup.blit(f2.render(linea, True, NX_TEXTO), (tarjeta.x + 8, ly))
            ly += f2.get_linesize()


def _feed_sigue(screen, t):
    """El final "quedarse": la pantalla se apagó y NEXUS sigue como si nada."""
    screen.fill((0, 0, 0))
    area = screen.get_rect()
    # Estática al principio.
    if t < 500:
        azar = random.Random(int(t // 40))
        for _ in range(400):
            v = azar.randint(20, 120)
            screen.fill((v, v, v), (azar.randrange(area.width), azar.randrange(area.height), 3, 2))
        return
    alto = int(area.height * 0.74)

    def pintar(sup, tt):
        sup.fill(NX_PANTALLA)
        sw = sup.get_width()
        y = _barra_estado(sup, "9:41")
        y = _cabecera(sup, y, "Para ti", NX_MARCA, verificado=False, letra="N")
        f = _f(max(10, sw * 0.055))
        sube = tt * 0.03
        posts = [p for p in PUBLICACIONES if p[5] is None] * 3
        from screens.paneles import partir_lineas
        for k, (nombre, color, verificado, texto, likes, _) in enumerate(posts):
            yy = int(y + 8 + k * sw * 0.42 - sube)
            if yy > sup.get_height() or yy < y - sw * 0.42:
                continue
            tarjeta = pygame.Rect(6, yy, sw - 12, int(sw * 0.38))
            pygame.draw.rect(sup, NX_TARJETA, tarjeta, border_radius=8)
            pygame.draw.circle(sup, color, (tarjeta.x + 16, tarjeta.y + 16), 10)
            sup.blit(f.render(nombre, True, NX_TEXTO), (tarjeta.x + 32, tarjeta.y + 8))
            ly = tarjeta.y + 30
            for linea in partir_lineas(texto, f, tarjeta.width - 16)[:2]:
                sup.blit(f.render(linea, True, NX_TEXTO), (tarjeta.x + 8, ly))
                ly += f.get_linesize()
            _me_gusta(sup, (tarjeta.x + 8, tarjeta.bottom - f.get_linesize() - 4), f, likes)
    celular(screen, (area.centerx, int(area.height * 0.44)), alto, pintar, t)


def _titular_falso(screen, t):
    """El final "nadie": NEXUS les echa la culpa."""
    area = screen.get_rect()
    u = _suave(t, 600, 500)
    if u <= 0:
        return
    caja = pygame.Rect(0, 0, int(area.width * 0.7), int(area.height * 0.12))
    caja.midtop = (area.centerx, int(area.height * 0.05) - int((1 - u) * area.height * 0.2))
    pygame.draw.rect(screen, (246, 247, 252), caja, border_radius=12)
    pygame.draw.rect(screen, NX_ROJO, caja, 3, border_radius=12)
    f = _f(caja.height * 0.24)
    f2 = _f(caja.height * 0.3)
    screen.blit(f.render("NEXUS · ÚLTIMA HORA", True, NX_ROJO), (caja.x + 18, caja.y + 10))
    texto = "Agentes colombianos difundían noticias falsas"
    img = f2.render(texto, True, NX_TEXTO)
    if img.get_width() > caja.width - 30:
        img = pygame.transform.smoothscale(img, (caja.width - 30, int(img.get_height() * (caja.width - 30) / img.get_width())))
    screen.blit(img, (caja.x + 18, caja.bottom - img.get_height() - 12))


def escenas_oscuras(screen, cuanto):
    from screens import final as escenas
    escenas.oscurecer(screen, cuanto)


def _guardia_final(screen, t):
    """El final "nadie": el Guardia suelta la fruta y destruye la cápsula."""
    lienzo = Lienzo(screen)
    sup = lienzo.sup
    w, h = BASE
    temblor = 0
    if 2600 < t < 5600:
        temblor = int(math.sin(t / 30) * (3 if t < 4200 else 5))
    _degradado(sup, pygame.Rect(0, 0, w, 110), (20, 22, 34), (34, 36, 50))
    pygame.draw.rect(sup, (60, 64, 80), (0, 110, w, 70))
    for x in range(0, w, 20):
        pygame.draw.line(sup, (72, 78, 94), (x, 110), (x, 180))
    for y in range(110, 180, 20):
        pygame.draw.line(sup, (54, 58, 72), (0, y), (w, y))
    pygame.draw.rect(sup, (188, 165, 119), (0, 108, w, 2))
    if t > 2400:
        rojo = pygame.Surface(BASE)
        rojo.fill((int(40 + 30 * math.sin(t / 150)), 0, 0))
        sup.blit(rojo, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    lienzo.pegar()
    s = lienzo.s
    # La cápsula (entera, y rota después del golpe).
    rota = t > 4300
    from juego import sprites_objetos
    cap = sprites_objetos.imagen("nave_rota.png" if rota else "nave_completa.png", alto=int(70 * s))
    if cap is not None:
        screen.blit(cap, cap.get_rect(midbottom=(lienzo.p(110, 150)[0] + temblor, lienzo.p(110, 150)[1])))
    if rota and t < 5600:
        azar = random.Random(int(t // 50))
        for _ in range(14):
            x, y = lienzo.p(110 + azar.uniform(-20, 20), 130 + azar.uniform(-18, 10))
            pygame.draw.circle(screen, (255, 210, 120), (x, y), max(1, int(s * 0.6)))
    # El Guardia: con la fruta, la suelta, ruge y camina a la cápsula.
    guardia = _sprite(os.path.join("Imagenes", "Aliens", "Alien_Guardia", "Alien_Guardia_idle_west.png"), int(86 * s))
    x_guardia = 220 - 70 * _suave(t, 3000, 1200)
    pie = lienzo.p(x_guardia, 160)
    if guardia is not None:
        screen.blit(guardia, guardia.get_rect(midbottom=(pie[0] + temblor, pie[1])))
    # La fruta: en su mano, cae y rueda.
    if t < 1400:
        fruta = lienzo.p(x_guardia - 12, 118)
    else:
        u = _suave(t, 1400, 700)
        fruta = lienzo.p(x_guardia - 12 - 30 * _suave(t, 2100, 1600), 118 + 40 * u)
    pygame.draw.circle(screen, (250, 140, 40), fruta, max(3, int(4 * s)))
    pygame.draw.circle(screen, (255, 210, 120), (fruta[0] - int(s), fruta[1] - int(s)), max(1, int(1.4 * s)))
    pygame.draw.line(screen, (80, 160, 70), (fruta[0], fruta[1] - int(4 * s)), (fruta[0] + int(2 * s), fruta[1] - int(6 * s)), max(1, int(s)))
    if 2400 < t < 3600:
        f = _f(lienzo.area.height * 0.08)
        img = f.render("¡GRRRAAAH!", True, (255, 120, 90))
        screen.blit(img, img.get_rect(center=(pie[0], lienzo.p(0, 40)[1])))
    if t > 4300 and t < 4500:
        screen.blit(cache_dibujo.capa(screen.get_size(), (255, 255, 255, 180)), (0, 0))
