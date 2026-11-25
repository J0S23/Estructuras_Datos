"""La escena del final de la partida (detrás de los resultados).

Primero se ve sola unos segundos (`INTRO_MS`; Enter, un botón o un clic la
saltan) y después queda de fondo, oscurecida, detrás de los resultados
(screens/resultados.py):

- **Escaparon**: la cápsula sale de la nave alienígena (arriba a la
  izquierda) y vuela hacia la Tierra (abajo a la derecha, girando despacio,
  con nubes, hielo en los polos, la noche del lado de abajo y su
  atmósfera): estrellas en tres capas (rayas al arrancar, como un salto),
  una nebulosa, una galaxia que gira y estrellas fugaces. La nave se queda
  atrás.
- **No escaparon**: el bloque de celdas: cada jugador en la suya (su
  personaje respirando), las rejas caen una tras otra (con polvo y temblor),
  la baliza roja gira y un alien patrulla por delante.

La cápsula volando es la animación de Anny (Imagenes/UI/capsula_escape.png:
16 cuadros de 80x80 uno al lado del otro, mirando a la DERECHA, con sus
propios propulsores) a `FPS_CAPSULA` cuadros por segundo, agrandada a un
múltiplo entero (pixel art). Si esa hoja no está, se usa el dibujo de la
cápsula reparada del juego (Imagenes/Objetos/nave_completa.png, ya mirando a
la derecha) con fuego dibujado (`FUEGO_DIBUJADO`).

Todo sale del tiempo `t` (ms desde que apareció la pantalla): sin estado.
Lo pesado (fondo, nebulosa, planeta, galaxia, celdas) se arma una vez por
tamaño de pantalla.
"""

import math
import os
import random

import pygame

INTRO_MS = 5600
FPS_CAPSULA = 12               # (los 12 FPS de la animación de Anny)
FUEGO_DIBUJADO = True          # (solo con la cápsula provisional: la de Anny trae sus propulsores)
HOJA_CAPSULA = os.path.join("Imagenes", "UI", "capsula_escape.png")

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cache = {}


def _guardado(clave, armar):
    img = _cache.get(clave)
    if img is None:
        if len(_cache) > 40:
            _cache.clear()
        img = _cache[clave] = armar()
    return img


def _suave(t, inicio, duracion):
    if t <= inicio:
        return 0.0
    x = min(1.0, (t - inicio) / max(1, duracion))
    return 1 - (1 - x) ** 3


def _hoja(ruta, alto, voltear=False, entero=False):
    """Los cuadros de una hoja (cuadros cuadrados en fila), recortados todos
    al mismo rectángulo y agrandados a `alto` px (sin suavizar: pixel art).
    Con `entero`, a la escala entera más cercana (los pixeles parejos)."""
    def armar():
        try:
            hoja = pygame.image.load(os.path.join(_RAIZ, ruta)).convert_alpha()
        except (pygame.error, FileNotFoundError, OSError):
            return []
        lado = hoja.get_height()
        if hoja.get_width() < 2 * lado:
            cuadros = [hoja]          # (un dibujo solo, no una hoja de cuadros)
        else:
            cuadros = [hoja.subsurface((i * lado, 0, lado, lado)) for i in range(hoja.get_width() // lado)]
        caja = None
        for c in cuadros:
            r = c.get_bounding_rect()
            if r.w and r.h:
                caja = r if caja is None else caja.union(r)
        if caja is None:
            return []
        escala = alto / caja.h
        if entero:
            escala = max(1, round(escala))
        tam = (max(1, int(caja.w * escala)), max(1, int(caja.h * escala)))
        salida = []
        for c in cuadros:
            img = pygame.transform.scale(c.subsurface(caja), tam)
            salida.append(pygame.transform.flip(img, True, False) if voltear else img)
        return salida
    return _guardado(("hoja", ruta, int(alto), voltear, entero), armar)


# ===========================================================================================
# Escaparon: el espacio
# ===========================================================================================

def _fondo_espacio(tam):
    """Degradado, nebulosa y el planeta con su anillo (fijo, una vez)."""
    def armar():
        w, h = tam
        sup = pygame.Surface(tam)
        for y in range(0, h, 2):
            k = y / h
            pygame.draw.rect(sup, (int(6 + 14 * k), int(6 + 4 * k), int(20 + 24 * k)), (0, y, w, 2))
        # Nebulosa: manchas grandes en una superficie chica, agrandada suave.
        chica = pygame.Surface((max(16, w // 6), max(16, h // 6)))
        chica.fill((0, 0, 0))
        azar = random.Random(11)
        cw, ch = chica.get_size()
        for color, n in (((60, 24, 110), 6), ((16, 64, 100), 5), ((110, 24, 80), 4), ((34, 34, 120), 3)):
            for _ in range(n):
                x, y = azar.uniform(0.25, 1.0) * cw, azar.uniform(0, 0.75) * ch
                r = azar.uniform(0.1, 0.22) * cw
                mancha = pygame.Surface((int(r * 2) + 2, int(r * 2) + 2))
                mancha.fill((0, 0, 0))
                pasos = 24
                for k in range(pasos, 0, -1):
                    f = (1 - k / (pasos + 1)) ** 2.4 * 0.42
                    pygame.draw.circle(mancha, tuple(int(c * f) for c in color), (int(r) + 1, int(r) + 1),
                                       max(1, int(r * k / pasos)))
                chica.blit(mancha, (int(x - r), int(y - r)), special_flags=pygame.BLEND_RGB_ADD)
        chica = pygame.transform.smoothscale(pygame.transform.smoothscale(chica, (cw // 2, ch // 2)), (cw, ch))
        sup.blit(pygame.transform.smoothscale(chica, tam), (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        # Estrellas quietas muy lejanas.
        for _ in range(w * h // 2500):
            v = azar.randint(40, 110)
            sup.set_at((azar.randrange(w), azar.randrange(h)), (v, v, min(255, v + 30)))
        # La atmósfera de la Tierra (la Tierra misma gira: _dibujar_tierra).
        r, centro = _lugar_tierra(w, h)
        halo = _armar_resplandor(int(r * 1.22), (40, 110, 220))
        sup.blit(halo, halo.get_rect(center=centro), special_flags=pygame.BLEND_RGB_ADD)
        return sup
    return _guardado(("espacio", tam), armar)


def _textura_tierra(r):
    """El mapa de la Tierra (mares, continentes, hielo y nubes) de 3r x 2r,
    que se repite a lo ancho: al correrlo, la Tierra gira."""
    def armar():
        largo, alto = r * 3, r * 2
        azar = random.Random(3)
        suelo = pygame.Surface((largo, alto))
        for y in range(alto):
            k = abs(y - r) / r
            suelo.fill((int(16 + 14 * k), int(58 + 26 * k), int(132 + 30 * k)), (0, y, largo, 1))

        def mancha(sup, color, x, y, radio):
            for dx in (-largo, 0, largo):
                pygame.draw.circle(sup, color, (int(x + dx), int(y)), int(radio))
        # Continentes: caminatas de círculos verdes, con desiertos y montes.
        for _ in range(7):
            x, y = azar.uniform(0, largo), azar.uniform(alto * 0.22, alto * 0.8)
            for _ in range(int(azar.uniform(40, 90))):
                radio = azar.uniform(0.03, 0.08) * r
                mancha(suelo, (58, 118, 62), x, y, radio)
                if azar.random() < 0.25:
                    mancha(suelo, (150, 128, 78), x + azar.uniform(-4, 4), y, radio * 0.6)
                elif azar.random() < 0.3:
                    mancha(suelo, (40, 92, 50), x, y + azar.uniform(-4, 4), radio * 0.5)
                x = (x + azar.uniform(-0.06, 0.07) * r) % largo
                y = min(alto * 0.86, max(alto * 0.14, y + azar.uniform(-0.05, 0.05) * r))
        # Los polos.
        for y0, signo in ((0, 1), (alto, -1)):
            for _ in range(60):
                x = azar.uniform(0, largo)
                mancha(suelo, (230, 240, 250), x, y0 + signo * azar.uniform(0, 0.06) * r, azar.uniform(0.03, 0.07) * r)
        # Nubes: remolinos blancos semitransparentes.
        nubes = pygame.Surface((largo, alto), pygame.SRCALPHA)
        for _ in range(110):
            x, y = azar.uniform(0, largo), azar.uniform(alto * 0.1, alto * 0.9)
            w_n, h_n = azar.uniform(0.1, 0.35) * r, azar.uniform(0.02, 0.06) * r
            for dx in (-largo, 0, largo):
                pygame.draw.ellipse(nubes, (255, 255, 255, int(azar.uniform(60, 150))),
                                    (int(x - w_n / 2 + dx), int(y - h_n / 2), int(w_n), int(h_n)))
        suelo.blit(nubes, (0, 0))
        return suelo
    return _guardado(("tierra_textura", r), armar)


def _sombra_tierra(r):
    """Luz desde arriba a la izquierda: la noche abajo a la derecha, y el
    borde que se oscurece (como una esfera). Más la máscara del círculo."""
    def armar():
        d = 2 * r
        # Primero todo oscuro y se aclara hacia la luz.
        sombra = pygame.Surface((d, d), pygame.SRCALPHA)
        sombra.fill((0, 0, 12, 225))
        for k in range(40):
            f = k / 39
            a = int(225 * (1 - f) ** 1.3)
            pygame.draw.circle(sombra, (0, 0, 12, a), (r - int(r * 0.38 * f), r - int(r * 0.38 * f)),
                               int(r * (1.25 - f * 0.75)))
        mascara = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(mascara, (255, 255, 255, 255), (r, r), r)
        return sombra, mascara
    return _guardado(("tierra_sombra", r), armar)


def _tierra(r, giro):
    """La Tierra de radio r, girada `giro` px (la última se guarda)."""
    giro = int(giro) % (r * 3)
    clave = ("tierra", r)
    actual = _cache.get(clave)
    if actual is not None and actual[0] == giro:
        return actual[1]
    textura = _textura_tierra(r)
    sombra, mascara = _sombra_tierra(r)
    img = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
    img.blit(textura, (-giro, 0))
    img.blit(textura, (r * 3 - giro, 0))
    img.blit(sombra, (0, 0))
    img.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    _cache[clave] = (giro, img)
    return img


def _lugar_tierra(w, h):
    return int(h * 0.44), (int(w * 0.93), int(h * 1.04))


def _dibujar_tierra(screen, t):
    """La Tierra abajo a la derecha (hacia allá va la cápsula), con su
    atmósfera. Gira despacito."""
    w, h = screen.get_size()
    r, centro = _lugar_tierra(w, h)
    tierra = _tierra(r, t * 0.004)
    screen.blit(tierra, tierra.get_rect(center=centro))
    # El borde iluminado de la atmósfera.
    pygame.draw.arc(screen, (120, 190, 255), pygame.Rect(0, 0, 2 * r, 2 * r).move(centro[0] - r, centro[1] - r),
                    math.radians(95), math.radians(175), 3)


def _galaxia(lado):
    """Una galaxia espiral (para sumarla). Se arma una vez."""
    def armar():
        chico = lado // 2
        sup = pygame.Surface((chico, chico))
        sup.fill((0, 0, 0))
        punto = pygame.Surface((5, 5))
        azar = random.Random(5)
        c = chico / 2
        for brazo in range(2):
            for i in range(900):
                u = azar.random() ** 0.8
                ang = brazo * math.pi + u * 3.4 * math.pi + azar.gauss(0, 0.28)
                r = u * c * 0.95 + azar.gauss(0, 3)
                x, y = c + r * math.cos(ang), c + r * math.sin(ang) * 0.55
                v = (1 - u) * 0.8 + 0.2
                color = (int(120 * v), int(110 * v), int(190 * v)) if azar.random() < 0.7 else \
                    (int(200 * v), int(120 * v), int(170 * v))
                punto.fill((0, 0, 0))
                pygame.draw.circle(punto, color, (2, 2), 1 if azar.random() < 0.8 else 2)
                sup.blit(punto, (int(x) - 2, int(y) - 2), special_flags=pygame.BLEND_RGB_ADD)
        for k in range(14, 0, -1):
            f = (1 - k / 15) ** 2
            capa = pygame.Surface((chico, chico))
            capa.fill((0, 0, 0))
            pygame.draw.ellipse(capa, (int(255 * f), int(225 * f), int(200 * f)),
                                pygame.Rect(0, 0, int(chico * 0.04 * k), int(chico * 0.024 * k)).move(
                                    int(c - chico * 0.02 * k), int(c - chico * 0.012 * k)))
            sup.blit(capa, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        return pygame.transform.smoothscale(sup, (lado, lado))
    return _guardado(("galaxia", lado), armar)


def _galaxia_girada(lado, angulo):
    """La galaxia girada (de a 2 grados; se guarda solo la última)."""
    angulo = int(angulo) // 2 * 2 % 360
    clave = ("galaxia_girada", lado)
    actual = _cache.get(clave)
    if actual is None or actual[0] != angulo:
        actual = _cache[clave] = (angulo, pygame.transform.rotate(_galaxia(lado), angulo))
    return actual[1]


def _estrellas_espacio(screen, t, velocidad, rayas):
    """Tres capas de estrellas que pasan hacia arriba a la izquierda (la
    cápsula va hacia abajo a la derecha, a la Tierra); con `rayas` > 0 se
    estiran como en un salto."""
    w, h = screen.get_size()
    def armar():
        azar = random.Random(31)
        return [[(azar.uniform(0, w + 160), azar.uniform(0, h), azar.uniform(0, 6.3))
                 for _ in range(w * h // (4000 * (3 - n)))] for n in range(3)]
    capas = _guardado(("estrellas", (w, h)), armar)
    for n, capa in enumerate(capas):
        vel = velocidad * (0.25, 0.55, 1.0)[n]
        brillo = (120, 180, 245)[n]
        largo = int(rayas * (20, 60, 140)[n])
        for x0, y0, fase in capa:
            x = (x0 - vel) % (w + 160) - 80
            y = (y0 - vel * 0.3) % h
            c = int(brillo * (0.75 + 0.25 * math.sin(t / 500 + fase)))
            color = (c, c, min(255, c + 30))
            if largo > 2:
                pygame.draw.line(screen, color, (x, y), (x + largo, y + largo * 0.3), 1 + (n == 2))
            elif n == 2:
                pygame.draw.rect(screen, color, (x, y, 2, 2))
            else:
                screen.set_at((int(x), int(y)), color)


def _fugaces(screen, t):
    w, h = screen.get_size()
    periodo = 3700
    u = (t % periodo) / 700
    if u > 1:
        return
    azar = random.Random(t // periodo)
    x0, y0 = azar.uniform(0.3, 1.0) * w, azar.uniform(0.02, 0.4) * h
    x, y = x0 - u * w * 0.25, y0 + u * h * 0.12
    for k in range(10):
        f = 1 - k / 10
        c = int(230 * f * (1 - u * 0.6))
        pygame.draw.circle(screen, (c, c, min(255, c + 20)), (int(x + k * 9), int(y - k * 4.3)), max(1, int(2 * f)))


# Base de la nave alienígena (pixel art): se dibuja chiquita y se agranda sin suavizar.
NAVE_BASE = (240, 104)          # px de la nave dibujada (se agranda a un múltiplo entero)
COMPUERTA = (217, 59)           # dónde está la compuerta abierta en ese dibujo


def _mezcla(a, b, f):
    f = max(0.0, min(1.0, f))
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def _nave_alien_base():
    """La nave de los aliens, de lado, en pixel art (240x104): un platillo
    de metal oscuro con franjas, la cúpula verde con tres siluetas, la panza
    orgánica con costillas, aletas, antena y, a la derecha, la compuerta
    abierta por donde salió la cápsula. Con contorno oscuro, como los sprites
    del juego."""
    def armar():
        w, h = NAVE_BASE
        sup = pygame.Surface((w, h), pygame.SRCALPHA)
        cx = w // 2
        # -- Aletas de atrás (detrás del casco) -----------------------------------
        for lado in (-1, 1):
            base_x = cx + lado * 70
            puntas = [(base_x - lado * 10, 50), (base_x + lado * 30, 16), (base_x + lado * 38, 18),
                      (base_x + lado * 24, 52)]
            pygame.draw.polygon(sup, (58, 46, 84), puntas)
            pygame.draw.line(sup, (150, 120, 200), puntas[1], puntas[2])
            pygame.draw.line(sup, (96, 78, 136), puntas[0], puntas[1])
        # -- La panza: orgánica, con costillas --------------------------------------
        panza = pygame.Rect(cx - 80, 54, 160, 40)
        pygame.draw.ellipse(sup, (40, 22, 50), panza)
        pygame.draw.ellipse(sup, (78, 38, 88), panza.inflate(-14, -14))
        pygame.draw.ellipse(sup, (104, 52, 112), panza.inflate(-60, -24))
        for i in range(-6, 7):
            if i == 0:
                continue
            x = cx + i * 11
            alto_c = 16 - abs(i) * 2
            inclina = 3 if i > 0 else -3
            pygame.draw.line(sup, (168, 92, 170), (x, 70), (x + inclina, 70 + alto_c))
            pygame.draw.line(sup, (30, 14, 38), (x + 1, 71), (x + 1 + inclina, 71 + alto_c))
        # El emisor de abajo (verde).
        pygame.draw.ellipse(sup, (24, 70, 58), (cx - 24, 84, 48, 14))
        pygame.draw.ellipse(sup, (70, 220, 160), (cx - 18, 86, 36, 9))
        pygame.draw.ellipse(sup, (200, 255, 225), (cx - 9, 88, 18, 4))
        # -- El casco: un disco ancho con franjas de luz --------------------------
        casco = pygame.Rect(2, 40, w - 4, 38)
        alto_casco = casco.height
        for y in range(casco.top, casco.bottom):
            f = (y - casco.top) / alto_casco
            # ancho de la elipse en esta fila
            dy = (y + 0.5 - casco.centery) / (alto_casco / 2)
            if abs(dy) >= 1:
                continue
            medio = int((casco.width / 2) * math.sqrt(1 - dy * dy))
            if f < 0.5:
                color = _mezcla((150, 144, 182), (82, 76, 112), f / 0.5)
                if 0.1 < f < 0.2:
                    color = _mezcla(color, (214, 210, 240), 0.5)      # el brillo de arriba
            else:
                color = _mezcla((66, 58, 92), (26, 22, 40), (f - 0.5) / 0.5)
            pygame.draw.line(sup, color, (cx - medio, y), (cx + medio - 1, y))
        # El borde del ecuador: una franja brillante y luces.
        ecuador = casco.centery
        for y, color in ((ecuador - 1, (196, 190, 230)), (ecuador, (120, 112, 160)), (ecuador + 1, (40, 34, 60))):
            dy = (y + 0.5 - casco.centery) / (alto_casco / 2)
            medio = int((casco.width / 2) * math.sqrt(max(0.0, 1 - dy * dy)))
            pygame.draw.line(sup, color, (cx - medio + 2, y), (cx + medio - 3, y))
        # Paneles: costuras verticales (curvas por la perspectiva) y remaches.
        for i in range(-9, 10):
            x = cx + int(math.sin(i / 10 * math.pi / 2) * (casco.width / 2 - 8))
            pygame.draw.line(sup, (58, 52, 82), (x, casco.top + 9), (x, ecuador - 3))
            pygame.draw.line(sup, (18, 14, 30), (x, ecuador + 3), (x, casco.bottom - 7))
            if i % 2 == 0:
                sup.set_at((x + 2, ecuador - 6), (200, 196, 232))
        # Ventanas a lo largo, bajo el ecuador.
        for i in range(-8, 9):
            x = cx + int(math.sin(i / 9.5 * math.pi / 2) * (casco.width / 2 - 20))
            color = (120, 240, 200) if i % 3 == 0 else (255, 206, 120)
            pygame.draw.rect(sup, (20, 14, 26), (x - 2, ecuador + 4, 5, 4))
            pygame.draw.rect(sup, color, (x - 1, ecuador + 5, 3, 2))
        # -- La cubierta de arriba y la cúpula --------------------------------------
        cubierta = pygame.Rect(cx - 70, 34, 140, 18)
        pygame.draw.ellipse(sup, (96, 90, 128), cubierta)
        pygame.draw.ellipse(sup, (140, 134, 172), cubierta.inflate(-10, -8))
        pygame.draw.ellipse(sup, (60, 54, 86), cubierta, 1)
        cupula = pygame.Rect(cx - 42, 6, 84, 64)
        recorte = pygame.Rect(0, 0, w, 42)
        vidrio = pygame.Surface((w, h), pygame.SRCALPHA)
        for k in range(14):
            f = k / 13
            r = cupula.inflate(-int(cupula.w * 0.75 * f), -int(cupula.h * 0.75 * f))
            r.bottom = cupula.bottom - int(cupula.h * 0.08 * f)
            pygame.draw.ellipse(vidrio, _mezcla((20, 54, 56), (110, 250, 190), f ** 1.4), r)
        # Las tres siluetas de adentro (cabezas largas, cuellos finos), a contraluz.
        sombra = (22, 58, 52)
        for dx, alto_s in ((-19, 2), (0, -2), (18, 3)):
            x = cx + dx
            pygame.draw.ellipse(vidrio, sombra, (x - 4, 18 + alto_s, 9, 13))
            pygame.draw.rect(vidrio, sombra, (x - 1, 30 + alto_s, 3, 3))
            pygame.draw.ellipse(vidrio, sombra, (x - 6, 32 + alto_s, 13, 14))
            vidrio.set_at((x - 2, 24 + alto_s), (200, 255, 140))
            vidrio.set_at((x + 2, 24 + alto_s), (200, 255, 140))
        sup.blit(vidrio, recorte, recorte)
        # Borde y brillo del vidrio.
        pygame.draw.arc(sup, (170, 255, 220), cupula, 0.05, math.pi - 0.05, 1)
        pygame.draw.arc(sup, (240, 255, 250), cupula.inflate(-18, -14), 1.9, 2.5, 2)
        sup.set_at((cx - 22, 16), (255, 255, 255))
        # La antena.
        pygame.draw.line(sup, (150, 144, 182), (cx, 6), (cx, 0))
        pygame.draw.rect(sup, (255, 70, 80), (cx - 1, 0, 3, 2))
        # -- La compuerta abierta (a la derecha): por ahí salió la cápsula ----------
        puerta = pygame.Rect(w - 34, ecuador - 6, 22, 12)
        pygame.draw.ellipse(sup, (24, 12, 10), puerta.inflate(6, 4))
        pygame.draw.ellipse(sup, (230, 110, 50), puerta)
        pygame.draw.ellipse(sup, (255, 190, 110), puerta.inflate(-6, -4))
        pygame.draw.ellipse(sup, (255, 246, 210), puerta.inflate(-12, -8))
        # (la tapa, abierta hacia arriba)
        pygame.draw.polygon(sup, (110, 104, 146), [(puerta.left, puerta.top - 2), (puerta.right, puerta.top - 2),
                                                   (puerta.right - 3, puerta.top - 9), (puerta.left + 4, puerta.top - 8)])
        pygame.draw.line(sup, (200, 196, 232), (puerta.left + 4, puerta.top - 8), (puerta.right - 3, puerta.top - 9))
        # -- Contorno oscuro de 1 px (como los sprites del juego) -------------------
        mascara = pygame.mask.from_surface(sup)
        borde = pygame.Surface((w, h), pygame.SRCALPHA)
        for x, y in mascara.outline():
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                px, py = x + ox, y + oy
                if 0 <= px < w and 0 <= py < h and not mascara.get_at((px, py)):
                    borde.set_at((px, py), (10, 8, 18))
        borde.blit(sup, (0, 0))
        return borde
    return _guardado(("nave_alien_base",), armar)


def _nave_alien(alto):
    """La nave de los aliens, agrandada a la escala entera más cercana a `alto` px."""
    def armar():
        base = _nave_alien_base()
        escala = max(1, round(alto / NAVE_BASE[1]))
        return pygame.transform.scale(base, (NAVE_BASE[0] * escala, NAVE_BASE[1] * escala))
    return _guardado(("nave_alien", int(alto)), armar)


def _dibujar_nave_alien(screen, t, w, h):
    """La nave de la que salieron, con sus luces: la cúpula y el emisor de
    abajo laten, la compuerta abierta brilla y las luces del borde corren."""
    nave = _nave_alien(int(h * 0.5))
    lejos = _suave(t, 500, 4300)
    escala = 1 - 0.6 * lejos
    nw, nh = nave.get_size()
    # (achicada en pasos: no se reescala en cada cuadro)
    paso = round(escala * 20) / 20
    if paso < 0.999:
        nave = _guardado(("nave_alien_lejos", nh, paso),
                         lambda: pygame.transform.scale(nave, (int(nw * paso), int(nh * paso))))
    sw, sh = nave.get_size()
    # Al principio, la compuerta justo donde aparece la cápsula (_camino_capsula).
    # Después se queda atrás: se achica hacia arriba a la izquierda (sin
    # salirse de la pantalla enseguida, para que se alcance a ver).
    ks = sw / NAVE_BASE[0]
    x = (w * 0.25 - w * 0.17 * lejos) - COMPUERTA[0] * ks
    y = (h * 0.39 - h * 0.1 * lejos) - COMPUERTA[1] * ks
    alfa = 1.0 if t < 3000 else max(0.0, 1 - (t - 3000) / 1900)
    if alfa < 1:
        nave = nave.copy()
        nave.set_alpha(int(255 * alfa))
    screen.blit(nave, (int(x), int(y)))
    if alfa <= 0:
        return
    k = sw / NAVE_BASE[0]                         # px de pantalla por px del dibujo

    def punto(px, py):
        return int(x + px * k), int(y + py * k)

    def luz(px, py, radio, color, fuerza=1.0):
        r = max(3, int(radio * k * fuerza))
        img = _resplandor(r, tuple(int(c * alfa) for c in color))
        screen.blit(img, img.get_rect(center=punto(px, py)), special_flags=pygame.BLEND_RGB_ADD)

    latido = 0.75 + 0.25 * math.sin(t / 260)
    luz(120, 30, 46, (30, 90, 70), latido)                   # la cúpula
    luz(120, 90, 34, (40, 140, 100), latido)                 # el emisor de abajo
    luz(COMPUERTA[0], COMPUERTA[1], 22, (170, 90, 30), 0.85 + 0.15 * math.sin(t / 90))   # la compuerta
    # Las luces del borde: una ola que corre de izquierda a derecha.
    for i in range(-8, 9):
        px = 120 + int(math.sin(i / 9.5 * math.pi / 2) * (NAVE_BASE[0] / 2 - 22))
        ola = math.sin(i * 0.7 - t / 120)
        if ola > 0.6:
            luz(px, 64, 5, (200, 160, 80) if i % 3 else (80, 200, 160))
    # La antena: un pitido rojo.
    if (t // 450) % 2 == 0:
        luz(120, 1, 6, (200, 40, 50))


def _capsula(alto):
    """(cuadros, provisional): los cuadros de la cápsula, mirando a la
    derecha. La animación de Anny si está (HOJA_CAPSULA); si no, la
    provisional (sin animación: lleva el fuego dibujado)."""
    if os.path.exists(os.path.join(_RAIZ, HOJA_CAPSULA)):
        cuadros = _hoja(HOJA_CAPSULA, alto, entero=True)
        if cuadros:
            return cuadros, False
    return _hoja(os.path.join("Imagenes", "Objetos", "nave_completa.png"), alto), True


_giradas = {}


def _girada(img, angulo):
    """La cápsula girada (guardada por ángulo: ya afuera solo se mece)."""
    angulo = round(angulo)
    clave = (id(img), angulo)
    girada = _giradas.get(clave)
    if girada is None:
        if len(_giradas) > 80:
            _giradas.clear()
        girada = _giradas[clave] = pygame.transform.rotate(img, angulo)
    return girada


def _camino_capsula(t, w, h):
    """(x, y, escala, ángulo) de la cápsula en el tiempo t: sale de la nave
    (arriba a la izquierda) hacia la Tierra (abajo a la derecha)."""
    salida = _suave(t, 250, 2900)
    x = w * (0.25 + 0.32 * salida)
    y = h * (0.39 + 0.12 * salida)
    escala = 0.35 + 0.65 * salida
    # Ya afuera: flota.
    x += math.sin(t / 1300) * w * 0.012 * salida
    y += math.sin(t / 800) * h * 0.012 * salida
    angulo = -4 - 10 * salida + 3 * math.sin(t / 900) * salida
    return x, y, escala, angulo


def _chispa(radio, nivel):
    """Un puntito de luz para sumar (nivel 0-5: de amarillo a violeta oscuro)."""
    colores = ((255, 230, 150), (255, 170, 70), (230, 100, 50), (150, 60, 70), (80, 40, 80), (40, 24, 50))
    return _resplandor(max(3, radio // 3 * 3), colores[min(5, nivel)])


def _fuego(screen, t, punta, escala, intensidad, angulo):
    """El fuego del motor: un cono que titila con su resplandor y una estela
    de chispas que se queda atrás y se apaga (hacia donde apunta la cola)."""
    x, y = punta
    a = math.radians(angulo)
    ax, ay = -math.cos(a), math.sin(a)          # hacia atrás
    px, py = math.sin(a), math.cos(a)           # de lado
    luz = _resplandor(max(8, int(60 * escala)), (150, 80, 30))
    screen.blit(luz, luz.get_rect(center=(int(x + ax * 20 * escala), int(y + ay * 20 * escala))),
                special_flags=pygame.BLEND_RGB_ADD)
    azar = random.Random(7)
    for i in range(34):
        edad = ((t / 900) + i / 34) % 1.0
        atras = edad * 420 * escala * (0.6 + 0.4 * intensidad) + 8 * escala
        lado = azar.uniform(-1, 1) * edad * 46 * escala
        r = int((6 + edad * 22) * escala)
        img = _chispa(r, int(edad * 6))
        screen.blit(img, img.get_rect(center=(int(x + ax * atras + px * lado), int(y + ay * atras + py * lado))),
                    special_flags=pygame.BLEND_RGB_ADD)
    largo = (56 + 30 * math.sin(t / 37) + 16 * math.sin(t / 23)) * escala * intensidad
    ancho = 17 * escala
    for k, color in enumerate(((255, 110, 40), (255, 190, 80), (255, 250, 220))):
        f = 1 - k * 0.3
        pygame.draw.polygon(screen, color, [(x + px * ancho * f, y + py * ancho * f),
                                            (x + ax * largo * f, y + ay * largo * f),
                                            (x - px * ancho * f, y - py * ancho * f)])


def _escena_escape(screen, t):
    w, h = screen.get_size()
    screen.blit(_fondo_espacio((w, h)), (0, 0))
    lado = int(h * 0.32)
    galaxia = _galaxia_girada(lado, t * 0.004)
    screen.blit(galaxia, galaxia.get_rect(center=(int(w * 0.85), int(h * 0.17))), special_flags=pygame.BLEND_RGB_ADD)
    _dibujar_tierra(screen, t)
    # Velocidad: arranca como un salto y se calma.
    arranque = _suave(t, 300, 1400) * (1 - _suave(t, 1800, 2200))
    recorrido = t * 0.06 + 2600 * _suave(t, 300, 3800)
    _estrellas_espacio(screen, t, recorrido, arranque)
    _fugaces(screen, t)
    # La nave alienígena: al principio a la izquierda, y se queda atrás
    # (se aleja: se corre a la izquierda, se achica y se apaga).
    if t < 5000:
        _dibujar_nave_alien(screen, t, w, h)
    # La cápsula.
    cx, cy, escala, angulo = _camino_capsula(t, w, h)
    cuadros, provisional = _capsula(int(h * 0.26) // 4 * 4 or 4)
    if not cuadros:
        return
    img = cuadros[int(t / 1000 * FPS_CAPSULA) % len(cuadros)]
    if escala < 0.999:
        # Mientras se acerca (crece) no se guarda: se agranda en el momento.
        img = pygame.transform.scale(img, (max(1, int(img.get_width() * escala)),
                                           max(1, int(img.get_height() * escala))))
    if FUEGO_DIBUJADO and provisional:
        a = math.radians(angulo)
        dx, dy = -img.get_width() * 0.44, img.get_height() * 0.02
        punta = (cx + dx * math.cos(a) + dy * math.sin(a), cy - dx * math.sin(a) + dy * math.cos(a))
        _fuego(screen, t, punta, escala * h / 720, 0.6 + 0.4 * _suave(t, 200, 900), angulo)
    girada = _girada(img, angulo) if escala >= 0.999 else pygame.transform.rotate(img, round(angulo))
    screen.blit(girada, girada.get_rect(center=(int(cx), int(cy))))


# ===========================================================================================
# No escaparon: las celdas
# ===========================================================================================

def _cajas_celdas(w, h, n):
    n = max(1, n)
    ancho = min(int(w * 0.2), int((w * 0.86) / n) - 24)
    alto = int(h * 0.48)
    sep = (w - ancho * n) // (n + 1)
    y = int(h * 0.22)
    return [pygame.Rect(sep + i * (ancho + sep), y, ancho, alto) for i in range(n)]


def _fondo_celdas(tam, n):
    """La pared de la prisión, el piso y las celdas vacías (fijo)."""
    def armar():
        w, h = tam
        sup = pygame.Surface(tam)
        for y in range(0, h, 2):
            k = y / h
            pygame.draw.rect(sup, (int(18 + 10 * k), int(16 + 6 * k), int(28 + 8 * k)), (0, y, w, 2))
        # Paneles de la pared.
        paso = max(60, w // 12)
        for x in range(0, w, paso):
            pygame.draw.line(sup, (32, 28, 44), (x, 0), (x, int(h * 0.76)), 2)
            for y in (int(h * 0.08), int(h * 0.7)):
                pygame.draw.circle(sup, (48, 42, 62), (x + 8, y), 3)
        pygame.draw.rect(sup, (30, 26, 40), (0, int(h * 0.15), w, 6))
        # El piso, con rayas de peligro en el borde.
        piso = int(h * 0.76)
        pygame.draw.rect(sup, (24, 22, 32), (0, piso, w, h - piso))
        for x in range(-40, w + 40, 40):
            pygame.draw.polygon(sup, (70, 56, 20), [(x, piso), (x + 20, piso), (x + 8, piso + 10), (x - 12, piso + 10)])
        for i in range(-8, 9):
            pygame.draw.line(sup, (34, 30, 44), (w // 2 + i * w // 10, piso + 12), (w // 2 + i * w // 5, h), 1)
        pygame.draw.line(sup, (48, 42, 62), (0, piso), (w, piso), 3)
        # Las celdas (sin rejas: esas caen).
        for caja in _cajas_celdas(w, h, n):
            pygame.draw.rect(sup, (10, 9, 16), caja)
            luz = pygame.Surface(caja.size)
            luz.fill((0, 0, 0))
            for k in range(14, 0, -1):
                f = (1 - k / 15) ** 2 * 0.5
                pygame.draw.ellipse(luz, (int(120 * f), int(110 * f), int(150 * f)),
                                    pygame.Rect(0, 0, int(caja.w * 0.1 * k), int(caja.h * 0.09 * k)).move(
                                        caja.w // 2 - int(caja.w * 0.05 * k), -int(caja.h * 0.02 * k)))
            sup.blit(luz, caja.topleft, special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.rect(sup, (16, 14, 24), (caja.x, caja.bottom - int(caja.h * 0.12), caja.w,
                                                  int(caja.h * 0.12)))
            marco = caja.inflate(16, 16)
            pygame.draw.rect(sup, (64, 58, 80), marco, 8, border_radius=4)
            pygame.draw.rect(sup, (96, 88, 116), marco, 2, border_radius=4)
        return sup
    return _guardado(("celdas", tam, n), armar)


_resplandores = {}


def _resplandor(radio, color):
    clave = (radio, color)
    img = _resplandores.get(clave)
    if img is None:
        if len(_resplandores) > 400:
            _resplandores.clear()
        img = _resplandores[clave] = _armar_resplandor(radio, color)
    return img


def _armar_resplandor(radio, color):
    sup = pygame.Surface((radio * 2, radio * 2))
    sup.fill((0, 0, 0))
    for k in range(16, 0, -1):
        f = (1 - k / 17) ** 2
        pygame.draw.circle(sup, tuple(int(c * f) for c in color), (radio, radio), int(radio * k / 16))
    return sup


# Quién patrulla por delante de las celdas: (carpeta, hoja, cuadros por segundo, alto).
PATRULLAS = {
    "cazador": ("Alien_Rapido", "walking", 9, 0.3),
    # (en el juego es más alto que los agentes: ~1.5 veces lo que miden en su celda)
    "cambiaformas": ("Alien_Cambiaformas", "running", 12, 0.41),
}


def _escena_celdas(screen, t, jugadores, patrulla="cazador"):
    """Los agentes encerrados, cada uno en su celda, y un alien que patrulla por
    delante. `patrulla` (PATRULLAS): el Cazador en la derrota normal, el
    Cambiaformas en el final "quedarse" de la sala oculta."""
    from data.roles import ROLES_POR_NOMBRE
    w, h = screen.get_size()
    n = max(1, len(jugadores))
    cajas = _cajas_celdas(w, h, n)
    # Temblor cuando cae cada reja.
    caidas = [500 + 380 * i for i in range(n)]
    temblor = 0
    for c in caidas:
        if c + 180 < t < c + 420:
            temblor = int(6 * (1 - (t - c - 180) / 240) * math.sin(t / 15))
    screen.blit(_fondo_celdas((w, h), n), (0, temblor))
    roles = [getattr(j, "rol", None) for j in jugadores] or [None]
    for i, caja in enumerate(cajas):
        caja = caja.move(0, temblor)
        rol = roles[i] if i < len(roles) else None
        color = ROLES_POR_NOMBRE.get(rol, {}).get("color", (200, 200, 220))
        # El personaje, respirando, un poco a la izquierda o a la derecha.
        if rol:
            cuadros = _hoja(os.path.join("Imagenes", "Personajes", rol, f"{rol}_breathing_south.png"),
                            int(caja.h * 0.56))
            if cuadros:
                img = cuadros[int(t / 1000 * 6 + i) % len(cuadros)]
                pie = (caja.centerx + int(caja.w * 0.12 * math.sin(i * 2.1)), caja.bottom - int(caja.h * 0.06))
                pygame.draw.ellipse(screen, (6, 6, 10), pygame.Rect(0, 0, img.get_width(), 12).move(
                    pie[0] - img.get_width() // 2, pie[1] - 6))
                screen.blit(img, img.get_rect(midbottom=pie))
        # La reja: cae desde arriba con un rebote.
        k = _suave(t, caidas[i] - 300, 480)
        caer = (1 - k) + (0.06 * math.sin(min(1.0, (t - caidas[i] - 180) / 300) * math.pi)
                          if caidas[i] + 180 < t < caidas[i] + 480 else 0)
        dy = -int(caja.h * 1.1 * caer)
        recorte = screen.get_clip()
        screen.set_clip(caja.inflate(10, 10).clip(recorte))
        barras = max(4, caja.w // max(14, int(h * 0.03)))
        for b in range(barras + 1):
            x = caja.x + int(b * caja.w / barras)
            pygame.draw.rect(screen, (70, 72, 90), (x - 4, caja.y + dy, 8, caja.h))
            pygame.draw.line(screen, (150, 152, 175), (x - 2, caja.y + dy), (x - 2, caja.bottom + dy), 2)
        for yy in (0.08, 0.5, 0.92):
            pygame.draw.rect(screen, (80, 82, 100), (caja.x, caja.y + dy + int(caja.h * yy) - 5, caja.w, 10))
        screen.set_clip(recorte)
        # Polvo al caer.
        if caidas[i] + 150 < t < caidas[i] + 1100:
            u = (t - caidas[i] - 150) / 950
            azar = random.Random(i)
            for _ in range(14):
                x = caja.x + azar.uniform(0, caja.w)
                lado = azar.choice((-1, 1))
                px = x + lado * u * azar.uniform(20, 70)
                py = caja.bottom - u * azar.uniform(10, 40)
                v = int(70 * (1 - u)) // 10 * 10
                if v > 0:
                    polvo = _resplandor(max(3, int(5 + u * 14)), (v, v, v + 6))
                    screen.blit(polvo, polvo.get_rect(center=(int(px), int(py))), special_flags=pygame.BLEND_RGB_ADD)
        # La placa con el número y la lucecita de encima.
        placa = pygame.Rect(0, 0, int(caja.w * 0.36), int(h * 0.04))
        placa.midbottom = (caja.centerx, caja.y - 14)
        pygame.draw.rect(screen, (30, 28, 42), placa, border_radius=4)
        pygame.draw.rect(screen, color, placa, 2, border_radius=4)
        from juego.fuentes import fuente_de_tamano
        f = fuente_de_tamano(max(12, int(h * 0.024)))
        img = f.render(f"J{i + 1}", True, color)
        screen.blit(img, img.get_rect(center=placa.center))
        if (t // 500 + i) % 2:
            luz = _resplandor(int(h * 0.05), (180, 30, 30))
            screen.blit(luz, luz.get_rect(center=(placa.right + 14, placa.centery)), special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(screen, (255, 70, 70), (placa.right + 14, placa.centery), 4)
    # Un alien patrulla por delante (va y vuelve).
    if t > 1500:
        periodo = 9000
        u = ((t - 1500) % periodo) / periodo
        derecha = u < 0.5
        k = u * 2 if derecha else (1 - u) * 2
        x = -w * 0.1 + k * w * 1.2
        lado = "east" if derecha else "west"
        carpeta, hoja, fps, alto = PATRULLAS.get(patrulla, PATRULLAS["cazador"])
        cuadros = _hoja(os.path.join("Imagenes", "Aliens", carpeta, f"{carpeta}_{hoja}_{lado}.png"),
                        int(h * alto))
        if cuadros:
            img = cuadros[int(t / 1000 * fps) % len(cuadros)]
            pie = (int(x), int(h * 0.94))
            pygame.draw.ellipse(screen, (8, 8, 12), pygame.Rect(0, 0, img.get_width(), 14).move(
                pie[0] - img.get_width() // 2, pie[1] - 7))
            screen.blit(img, img.get_rect(midbottom=pie))
    # La baliza roja que gira (arriba al centro).
    giro = t / 400
    brillo = 0.5 + 0.5 * math.cos(giro)
    if brillo > 0.05:
        luz = _resplandor(int(h * 0.5), (int(150 * brillo) // 10 * 10, 0, 0))
        screen.blit(luz, luz.get_rect(center=(int(w * 0.5 + math.sin(giro) * w * 0.05), int(h * 0.04))),
                    special_flags=pygame.BLEND_RGB_ADD)
    pygame.draw.rect(screen, (60, 20, 24), (w // 2 - 18, 0, 36, int(h * 0.03)), border_radius=6)
    pygame.draw.circle(screen, (255, int(60 + 100 * brillo), 60), (w // 2, int(h * 0.03)), 9)


# ===========================================================================================

def intro_ms(final_historia=None):
    """Cuánto se ve la escena sola antes de los resultados. Los finales de la
    sala oculta (mision.final) son más largos: tienen su historia y la frase."""
    if final_historia:
        from screens import cinematica
        ms = cinematica.intro_final_ms(final_historia)
        if ms:
            return ms
    return INTRO_MS


def dibujar(screen, victoria, t, jugadores=(), final_historia=None, de_fondo=False):
    """La escena del final en todo `screen` en el tiempo `t` (ms). Con
    `final_historia` (mision.final: "sin_entrar", "escaparon", "quedarse",
    "nadie"), la de ese final (screens/cinematica.py)."""
    if final_historia:
        from screens import cinematica
        if final_historia in cinematica.TIEMPOS_FINAL:
            cinematica.dibujar_final(screen, final_historia, t, jugadores, de_fondo=de_fondo)
            return
    if victoria:
        _escena_escape(screen, t)
    else:
        _escena_celdas(screen, t, list(jugadores))


def oscurecer(screen, cuanto=150):
    """La capa oscura que va encima cuando la escena queda de fondo."""
    tam = screen.get_size()
    capa = _guardado(("oscura", tam, cuanto), lambda: _capa_oscura(tam, cuanto))
    screen.blit(capa, (0, 0))


def _capa_oscura(tam, cuanto):
    capa = pygame.Surface(tam)
    capa.fill((8, 8, 18))
    capa.set_alpha(cuanto)
    return capa
