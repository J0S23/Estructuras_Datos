"""Pantalla de menú principal.

El fondo (Imagenes/Fondos/FondoDeMenu.jpeg) ya trae el título del juego
dibujado, así que aquí se dibujan los botones encima, al estilo del menú de
EmpatiaQuest.

Con los efectos prendidos (juego/efectos.py) el fondo tiene vida:
- estrellas en tres capas que pasan lento por el espacio (las de lejos más
  lentas), solo donde el fondo es cielo oscuro, más estrellas que titilan y
  una fugaz de vez en cuando;
- las lámparas del marco y las pantallas de las consolas titilan; las luces
  de los trajes de la tripulación respiran; el vórtice late;
- un brillo pasa por el logo de NEXUS cada tanto;
- los botones son de vidrio oscuro con borde de neón, y el escogido brilla
  (juego/ui_components.Button, igual en la pausa y los resultados).

Los "brillos" salen del mismo fondo: a un pedazo se le resta un gris
(BLEND_RGB_SUB) y queda solo lo que ya brillaba, con su color; eso se suma o
se resta por cuadro (en C, sin recorrer píxeles en Python).
"""

import math
import random

import pygame

from juego.assets import dibujar_fondo_o_color, cargar_imagen
from juego.fuentes import fuente
from juego import efectos


OPCIONES_MENU = [
    ("Jugar", "jugar"),
    ("Jugar en red", "red"),
    ("Logros", "logros"),
    ("Opciones", "opciones"),
    ("Ayuda", "ayuda"),
    ("Créditos", "creditos"),
    ("Salir", "salir"),
]

COLOR_PISTA = (194, 216, 248)
COLOR_SOMBRA_PISTA = (14, 16, 30)
RUTA_FONDO = "Imagenes/Fondos/fondo_menu.png"

# Pedazos del fondo que brillan (fracciones del fondo: x, y, ancho, alto) y
# qué hacen. El fondo se estira a la pantalla, así que valen en cualquier tamaño.
BRILLOS = [
    ((0.105, 0.025, 0.115, 0.035), "lampara"),     # lámparas rosadas de arriba
    ((0.575, 0.025, 0.075, 0.035), "lampara"),
    ((0.855, 0.025, 0.065, 0.035), "lampara"),
    ((0.0, 0.04, 0.07, 0.07), "lampara"),          # esquinas naranjas
    ((0.93, 0.04, 0.07, 0.07), "lampara"),
    ((0.0, 0.25, 0.03, 0.16), "lampara"),          # lateral izquierda
    ((0.0, 0.63, 0.06, 0.2), "pantalla"),          # consolas de los lados
    ((0.94, 0.62, 0.06, 0.2), "pantalla"),
    ((0.1, 0.71, 0.06, 0.11), "traje"),            # la tripulación de espaldas
    ((0.235, 0.72, 0.06, 0.12), "traje"),
    ((0.405, 0.76, 0.06, 0.09), "traje"),
    ((0.545, 0.76, 0.06, 0.1), "traje"),
    ((0.66, 0.86, 0.1, 0.06), "lampara"),          # luces de abajo
    ((0.9, 0.8, 0.1, 0.1), "lampara"),
    ((0.52, 0.4, 0.11, 0.14), "vortice"),
]
LOGO = (0.555, 0.165, 0.39, 0.2)
CIELO = (0.05, 0.06, 0.9, 0.52)          # por donde pasan las estrellas

UMBRAL_BRILLO = 140


class _Fondo:
    """Lo animado del fondo para un tamaño de pantalla."""

    def __init__(self, fondo):
        self.tamano = fondo.get_size()
        w, h = self.tamano
        azar = random.Random(11)
        self.brillos = []
        for i, (frac, modo) in enumerate(BRILLOS):
            capa, rect = _capa_brillo(fondo, frac)
            if capa is not None:
                self.brillos.append((rect, _niveles(capa), modo, i * 1.7))
        capa, self.rect_logo = _capa_brillo(fondo, LOGO, umbral=120)
        self.logo = _niveles(capa) if capa is not None else None
        # Cielo oscuro: donde puede pasar una estrella.
        cielo = pygame.Rect(int(CIELO[0] * w), int(CIELO[1] * h), int(CIELO[2] * w), int(CIELO[3] * h))
        self.cielo = cielo
        oscuro = pygame.mask.from_threshold(fondo, (14, 10, 40, 255), (46, 44, 70, 255))
        self.oscuro = oscuro
        self.capas = []
        for capa, (cantidad, vel, brillo) in enumerate(((90, 0.004, 120), (50, 0.009, 180), (22, 0.018, 240))):
            self.capas.append([(azar.uniform(0, cielo.w), azar.uniform(0, cielo.h), vel, brillo, azar.uniform(0, 6.3))
                               for _ in range(int(cantidad * w * h / (1536 * 960)) + 4)])
        # Estrellas quietas que titilan (sobre cielo oscuro).
        self.titilan = []
        intentos = 0
        while len(self.titilan) < 40 and intentos < 4000:
            intentos += 1
            x, y = azar.randrange(cielo.left, cielo.right), azar.randrange(cielo.top, cielo.bottom)
            if oscuro.get_at((x, y)):
                self.titilan.append((x, y, azar.uniform(0, 6.3), azar.uniform(0.6, 1.8), azar.random() < 0.25))


def _capa_brillo(fondo, frac, umbral=UMBRAL_BRILLO):
    """(lo que brilla de ese pedazo del fondo, su rect). Restar un gris deja
    solo los píxeles claros, con su color."""
    w, h = fondo.get_size()
    rect = pygame.Rect(int(frac[0] * w), int(frac[1] * h), max(1, int(frac[2] * w)), max(1, int(frac[3] * h)))
    rect = rect.clip(fondo.get_rect())
    if rect.w <= 0 or rect.h <= 0:
        return None, rect
    capa = pygame.Surface(rect.size)
    capa.blit(fondo, (0, 0), rect)
    capa.fill((umbral, umbral, umbral), special_flags=pygame.BLEND_RGB_SUB)
    capa.blit(capa, (0, 0), special_flags=pygame.BLEND_RGB_ADD)        # x2: más contraste
    return capa, rect


def _niveles(capa, cuantos=6):
    lista = []
    for k in range(1, cuantos + 1):
        img = capa.copy()
        v = int(255 * k / cuantos)
        img.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
        lista.append(img)
    return lista


def _nivel(niveles, k):
    return niveles[max(0, min(len(niveles) - 1, int(round(k * len(niveles))) - 1))]


_fondos = {}


def _animado(screen):
    tam = screen.get_size()
    datos = _fondos.get(tam)
    if datos is None:
        fondo = cargar_imagen(RUTA_FONDO, tam)
        if fondo is None:
            return None
        _fondos.clear()
        datos = _fondos[tam] = _Fondo(fondo)
    return datos


def _ruido(n, semilla):
    x = (n * 374761393 + semilla * 668265263) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((x ^ (x >> 16)) & 0xFFFF) / 65535


def _dibujar_vida(screen, datos, t):
    cielo = datos.cielo
    # Estrellas que pasan (tres capas).
    for capa in datos.capas:
        for x0, y0, vel, brillo, fase in capa:
            x = cielo.x + (x0 - t * vel) % cielo.w
            y = cielo.y + y0
            if not datos.oscuro.get_at((int(x), int(y))):
                continue
            c = int(brillo * (0.75 + 0.25 * math.sin(t / 500 + fase)))
            screen.set_at((int(x), int(y)), (c, c, min(255, c + 25)))
            if brillo > 200:
                screen.set_at((int(x) + 1, int(y)), (c // 2, c // 2, c // 2 + 20))
    # Las que titilan (algunas con cruz).
    for x, y, fase, vel, cruz in datos.titilan:
        k = 0.5 + 0.5 * math.sin(t / 1000 * vel * 2 * math.pi + fase)
        c = int(255 * k)
        if c < 40:
            continue
        screen.set_at((x, y), (c, c, 255))
        if cruz and k > 0.6:
            largo = 2 + int(3 * k)
            color = (c // 2, c // 2, c * 2 // 3)
            pygame.draw.line(screen, color, (x - largo, y), (x + largo, y))
            pygame.draw.line(screen, color, (x, y - largo), (x, y + largo))
    # Una fugaz cada tanto (arriba, donde no hay nada).
    ciclo = 6500
    n, dentro = divmod(int(t), ciclo)
    if dentro < 900 and _ruido(n, 3) < 0.8:
        k = dentro / 900
        x0 = cielo.x + cielo.w * (0.55 + 0.4 * _ruido(n, 4))
        y0 = cielo.y + cielo.h * (0.02 + 0.12 * _ruido(n, 5))
        x, y = x0 - k * cielo.w * 0.35, y0 + k * cielo.h * 0.18
        dx, dy = cielo.w * 0.05, -cielo.h * 0.026
        for i, color in enumerate(((255, 255, 255), (170, 190, 255), (90, 100, 170))):
            a = (x + dx * i / 3, y + dy * i / 3)
            b = (x + dx * (i + 1) / 3, y + dy * (i + 1) / 3)
            pygame.draw.line(screen, color, a, b, 2 if i == 0 else 1)
    # Lo que brilla del fondo.
    for rect, niveles, modo, fase in datos.brillos:
        if modo == "lampara":
            k = 0.35 + 0.25 * math.sin(t / 700 + fase)
            if _ruido(int(t // 70), int(fase * 10)) < 0.03:
                screen.blit(_nivel(niveles, 0.9), rect, special_flags=pygame.BLEND_RGB_SUB)
                continue
        elif modo == "pantalla":
            k = 0.3 + 0.15 * math.sin(t / 130 + fase)
            if _ruido(int(t // 90), int(fase * 10)) < 0.08:
                k += 0.4
        elif modo == "traje":
            k = 0.3 + 0.3 * math.sin(t / 1000 * 2 * math.pi * 0.45 + fase)
        else:   # vórtice
            k = 0.35 + 0.35 * math.sin(t / 1000 * 2 * math.pi * 0.7)
        if k > 0.02:
            screen.blit(_nivel(niveles, k), rect, special_flags=pygame.BLEND_RGB_ADD)
    # El brillo que pasa por el logo (cada 5 s).
    if datos.logo is not None:
        r = datos.rect_logo
        periodo = 5200
        dentro = t % periodo
        if dentro < 1400:
            k = dentro / 1400
            centro = int(-r.w * 0.15 + (r.w * 1.3) * k)
            for ancho, nivel in ((r.w // 7, 0.35), (r.w // 14, 0.7), (r.w // 30, 1.0)):
                franja = pygame.Rect(centro - ancho // 2, 0, ancho, r.h).clip(pygame.Rect(0, 0, r.w, r.h))
                if franja.w > 0:
                    screen.blit(_nivel(datos.logo, nivel), (r.x + franja.x, r.y), franja,
                                special_flags=pygame.BLEND_RGB_ADD)


def render_menu(screen, botones=None, seleccionado=0):
    # Fondo: usa Imagenes/Fondos/fondo_menu.png (o cualquier imagen de menú
    # que haya en esa carpeta); si no hay ninguna, rellena de color.
    dibujar_fondo_o_color(screen, RUTA_FONDO, (35, 40, 60))
    t = pygame.time.get_ticks()
    if efectos.ACTIVOS:
        datos = _animado(screen)
        if datos is not None:
            _dibujar_vida(screen, datos, t)

    if botones:
        mouse_pos = pygame.mouse.get_pos()
        for i, boton in enumerate(botones):
            hover = boton.contains(mouse_pos) or i == seleccionado
            boton.draw(screen, hover=hover)

    pista = "Mouse o flechas + Enter"
    etiqueta = fuente("small").render(pista, True, COLOR_PISTA)
    sombra = fuente("small").render(pista, True, COLOR_SOMBRA_PISTA)
    rect = etiqueta.get_rect(center=(screen.get_width() // 2, screen.get_height() - 34))
    screen.blit(sombra, rect.move(2, 2))
    screen.blit(etiqueta, rect)
