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

La cápsula es PROVISIONAL: el dibujo de la cápsula reparada del juego
(Imagenes/Objetos/nave_completa.png), volteado y con fuego dibujado. Cuando
esté la animación de verdad, basta con poner la hoja en
Imagenes/UI/capsula_escape.png (cuadros cuadrados uno al lado del otro, la
cápsula mirando a la DERECHA): se usa sola, a `FPS_CAPSULA` cuadros por
segundo, y el fuego dibujado se apaga si `FUEGO_DIBUJADO` es False.

Todo sale del tiempo `t` (ms desde que apareció la pantalla): sin estado.
Lo pesado (fondo, nebulosa, planeta, galaxia, celdas) se arma una vez por
tamaño de pantalla.
"""

import math
import os
import random

import pygame

INTRO_MS = 5600
FPS_CAPSULA = 10
FUEGO_DIBUJADO = True

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


def _hoja(ruta, alto, voltear=False):
    """Los cuadros de una hoja (cuadros cuadrados en fila), recortados todos
    al mismo rectángulo y agrandados a `alto` px (sin suavizar: pixel art)."""
    def armar():
        try:
            hoja = pygame.image.load(os.path.join(_RAIZ, ruta)).convert_alpha()
        except (pygame.error, FileNotFoundError, OSError):
            return []
        lado = hoja.get_height()
        cuadros = [hoja.subsurface((i * lado, 0, lado, lado)) for i in range(max(1, hoja.get_width() // lado))]
        caja = None
        for c in cuadros:
            r = c.get_bounding_rect()
            if r.w and r.h:
                caja = r if caja is None else caja.union(r)
        if caja is None:
            return []
        escala = alto / caja.h
        tam = (max(1, int(caja.w * escala)), max(1, int(alto)))
        salida = []
        for c in cuadros:
            img = pygame.transform.scale(c.subsurface(caja), tam)
            salida.append(pygame.transform.flip(img, True, False) if voltear else img)
        return salida
    return _guardado(("hoja", ruta, int(alto), voltear), armar)


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


def _nave_alien(alto):
    """La nave de los aliens, de lado (se queda atrás)."""
    def armar():
        w, h = int(alto * 2.2), int(alto)
        sup = pygame.Surface((w, h), pygame.SRCALPHA)
        # La cúpula de vidrio, con un brillo verdoso por dentro.
        cupula = pygame.Rect(int(w * 0.3), int(h * 0.06), int(w * 0.4), int(h * 0.5))
        for k in range(12):
            f = k / 12
            r = cupula.inflate(-int(cupula.w * 0.7 * f), -int(cupula.h * 0.7 * f))
            r.bottom = cupula.bottom - int(cupula.h * 0.1 * f)
            pygame.draw.ellipse(sup, (int(30 + 40 * f), int(50 + 120 * f), int(60 + 60 * f)), r)
        pygame.draw.ellipse(sup, (120, 200, 170), cupula, 2)
        pygame.draw.arc(sup, (200, 255, 230), cupula.inflate(-cupula.w * 0.3, -cupula.h * 0.3), 1.9, 2.6, 3)
        # El casco: un disco ancho con degradado de arriba a abajo.
        casco = pygame.Rect(0, int(h * 0.36), w, int(h * 0.4))
        for k in range(16):
            f = k / 15
            franja = pygame.Rect(casco.x, casco.y + int(casco.h * f * 0.9), casco.w, int(casco.h * (1 - f * 0.9)))
            pygame.draw.ellipse(sup, (int(70 - 46 * f), int(64 - 44 * f), int(96 - 60 * f)), franja)
        pygame.draw.ellipse(sup, (120, 110, 150), casco, 3)
        borde = casco.inflate(-int(w * 0.06), -int(casco.h * 0.45))
        pygame.draw.ellipse(sup, (40, 36, 56), borde, 2)
        # Ventanitas encendidas a lo largo.
        for i in range(14):
            x = int(w * (0.12 + 0.055 * i))
            y = int(casco.centery - casco.h * 0.04)
            pygame.draw.rect(sup, (255, 210, 120) if i % 4 else (120, 230, 200), (x, y, max(4, w // 90), max(3, h // 40)))
        # Patas de aterrizaje y el motor de abajo.
        pygame.draw.ellipse(sup, (110, 255, 190), (int(w * 0.38), int(h * 0.7), int(w * 0.24), int(h * 0.08)))
        # La compuerta abierta por donde salió la cápsula (a la derecha).
        pygame.draw.ellipse(sup, (255, 170, 90), (int(w * 0.86), int(h * 0.5), int(w * 0.07), int(h * 0.1)))
        return sup
    return _guardado(("nave_alien", int(alto)), armar)


def _capsula(alto):
    """Los cuadros de la cápsula, mirando a la derecha. La de verdad si está
    (Imagenes/UI/capsula_escape.png); si no, la provisional."""
    ruta = os.path.join("Imagenes", "UI", "capsula_escape.png")
    if os.path.exists(os.path.join(_RAIZ, ruta)):
        cuadros = _hoja(ruta, alto)
        if cuadros:
            return cuadros
    return _hoja(os.path.join("Imagenes", "Objetos", "nave_completa.png"), alto, voltear=True)


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
    # La nave alienígena: al principio a la izquierda, y se queda atrás.
    if t < 4200:
        nave = _nave_alien(int(h * 0.5))
        x = -nave.get_width() * 0.62 - w * 0.5 * _suave(t, 300, 3800)
        y = h * 0.36 - nave.get_height() // 2
        if t > 2600:
            nave = nave.copy()
            nave.set_alpha(int(255 * (1 - (t - 2600) / 1600)))
        screen.blit(nave, (int(x), int(y)))
        for i in range(6):
            if (t // 300 + i) % 3:
                pygame.draw.circle(screen, (255, 60, 70), (int(x + nave.get_width() * (0.12 + 0.13 * i)),
                                                           int(y + nave.get_height() * 0.66)), 3)
    # La cápsula.
    cx, cy, escala, angulo = _camino_capsula(t, w, h)
    cuadros = _capsula(int(h * 0.26) // 4 * 4 or 4)
    if not cuadros:
        return
    img = cuadros[int(t / 1000 * FPS_CAPSULA) % len(cuadros)]
    if escala < 0.999:
        # Mientras se acerca (crece) no se guarda: se agranda en el momento.
        img = pygame.transform.scale(img, (max(1, int(img.get_width() * escala)),
                                           max(1, int(img.get_height() * escala))))
    if FUEGO_DIBUJADO:
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
    if True:
        sup = pygame.Surface((radio * 2, radio * 2))
        sup.fill((0, 0, 0))
        for k in range(16, 0, -1):
            f = (1 - k / 17) ** 2
            pygame.draw.circle(sup, tuple(int(c * f) for c in color), (radio, radio), int(radio * k / 16))
        return sup


def _escena_celdas(screen, t, jugadores):
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
        cuadros = _hoja(os.path.join("Imagenes", "Aliens", "Alien_Rapido", f"Alien_Rapido_walking_{lado}.png"),
                        int(h * 0.3))
        if cuadros:
            img = cuadros[int(t / 1000 * 9) % len(cuadros)]
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

def dibujar(screen, victoria, t, jugadores=()):
    """La escena del final en todo `screen` en el tiempo `t` (ms)."""
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
