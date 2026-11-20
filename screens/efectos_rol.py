"""El personaje de cada rol en la elección de rol (screens/seleccion.py), con
los efectos visuales prendidos: camina en su lugar (el que estás mirando) o
respira (el que ya escogiste), y alrededor hace lo de su habilidad:

- Tecnomante: una línea de escaneo que lo recorre y hologramas que flotan.
- Forjador: chispas que saltan de la mano y un engranaje que gira atrás.
- Biomante: anillos de pulso verde que salen del pecho y crucecitas que suben.
- Resonante: ondas de sonido rosadas a los dos lados.

Todo sale del tiempo (sin estado). `dibujar(screen, rect, rol, color, listo)`:
`rect` es donde iba el retrato quieto (screens/seleccion._retrato).
"""

import math
import os
import random

import pygame

from screens.vidrio import brillo


def _cuadros(rol, alto, listo):
    from screens.final import _hoja
    accion = "breathing_south" if listo else "walking_south"
    return _hoja(os.path.join("Imagenes", "Personajes", rol, f"{rol}_{accion}.png"), alto)


def dibujar(screen, rect, rol, color, listo=False):
    """El personaje animado en `rect` y el efecto de su habilidad."""
    t = pygame.time.get_ticks()
    cuadros = _cuadros(rol, rect.height, listo)
    if not cuadros:
        return False
    fuerza = 1.0 if listo else 0.75
    atras = _EFECTOS.get(rol, (None, None))[0]
    if atras is not None:
        atras(screen, rect, color, t, fuerza)
    img = cuadros[int(t / 1000 * (6 if listo else 9)) % len(cuadros)]
    screen.blit(img, img.get_rect(midbottom=rect.midbottom))
    delante = _EFECTOS.get(rol, (None, None))[1]
    if delante is not None:
        delante(screen, rect, color, t, fuerza)
    return True


# -- Tecnomante -------------------------------------------------------------------------

def _tecnomante_atras(screen, r, color, t, fuerza):
    # Tres hologramas que flotan a los lados: pantallitas con rayas.
    cian = (90, 230, 255)
    for i, (dx, dy) in enumerate(((-0.46, -0.36), (0.44, -0.3), (0.46, 0.08))):
        flota = math.sin(t / 600 + i * 2) * r.h * 0.03
        w, h = int(r.w * 0.22), int(r.h * 0.13)
        caja = pygame.Rect(0, 0, w, h)
        caja.center = (int(r.centerx + dx * r.w), int(r.centery + dy * r.h + flota))
        brillo(screen, caja.center, w * 0.8, tuple(int(c * 0.22 * fuerza) for c in cian))
        pygame.draw.rect(screen, cian, caja, 1)
        for k in range(3):
            largo = int((0.4 + 0.5 * abs(math.sin(t / 300 + i + k))) * (w - 8))
            pygame.draw.line(screen, cian, (caja.x + 4, caja.y + 4 + k * (h - 8) // 2),
                             (caja.x + 4 + largo, caja.y + 4 + k * (h - 8) // 2), 1)


def _tecnomante_delante(screen, r, color, t, fuerza):
    # La línea de escaneo que baja y sube por el cuerpo.
    u = (t % 1800) / 1800
    y = r.y + int(r.h * (u * 2 if u < 0.5 else 2 - u * 2))
    brillo(screen, (r.centerx, y), r.w * 0.5, tuple(int(c * 0.35 * fuerza) for c in (90, 230, 255)))
    pygame.draw.line(screen, (170, 245, 255), (r.x - 6, y), (r.right + 6, y), 2)


# -- Forjador -----------------------------------------------------------------------------

def _forjador_atras(screen, r, color, t, fuerza):
    # Un engranaje que gira detrás, arriba.
    cx, cy = r.centerx - int(r.w * 0.42), r.y + int(r.h * 0.22)
    radio = r.w * 0.22
    giro = t / 900
    puntos = []
    for i in range(32):
        a = giro + i * math.pi * 2 / 32
        rr = radio if (i % 4) in (1, 2) else radio * 0.75
        puntos.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    oscuro = tuple(int(c * 0.45) for c in color)
    pygame.draw.polygon(screen, oscuro, puntos)
    pygame.draw.polygon(screen, tuple(int(c * 0.75) for c in color), puntos, 2)
    pygame.draw.circle(screen, (20, 18, 30), (int(cx), int(cy)), int(radio * 0.3))


def _forjador_delante(screen, r, color, t, fuerza):
    # Chispas que saltan de la mano (abajo a la derecha) y caen.
    mano = (r.centerx - int(r.w * 0.32), r.y + int(r.h * 0.66))
    azar = random.Random(4)
    for i in range(int(30 * fuerza)):
        periodo = azar.uniform(500, 900)
        fase = azar.uniform(0, periodo)
        u = ((t + fase) % periodo) / periodo
        vx, vy = azar.uniform(-1.0, 0.5) * r.w * 0.9, -azar.uniform(0.3, 0.9) * r.h * 0.8
        x = mano[0] + vx * u
        y = mano[1] + vy * u + r.h * 1.4 * u * u
        if y > r.bottom:
            continue
        c = (255, int(230 - 140 * u), int(120 - 100 * u))
        largo = 2 + int(3 * (1 - u))
        pygame.draw.line(screen, c, (int(x), int(y)), (int(x - vx * 0.05), int(y - (vy + r.h * 2.8 * u) * 0.05)), largo)
    if (t // 90) % 3 == 0:
        brillo(screen, mano, r.w * 0.35, (90, 50, 10))


# -- Biomante -----------------------------------------------------------------------------

def _biomante_atras(screen, r, color, t, fuerza):
    # Anillos de pulso que salen del pecho (pum-pum).
    pecho = (r.centerx, r.y + int(r.h * 0.42))
    for k in range(3):
        u = ((t / 1300) + k / 3) % 1.0
        radio = int(r.w * (0.2 + 0.75 * u))
        c = tuple(int(v * (1 - u) * fuerza) for v in color)
        if radio > 2:
            pygame.draw.ellipse(screen, c, pygame.Rect(0, 0, radio * 2, int(radio * 1.3)).move(
                pecho[0] - radio, pecho[1] - int(radio * 0.65)), 2)
    latido = max(0.0, math.sin(t / 1300 * math.pi * 2)) ** 6
    if latido > 0.1:
        brillo(screen, pecho, r.w * 0.6, tuple(int(c * 0.4 * latido) for c in color))


def _biomante_delante(screen, r, color, t, fuerza):
    # Crucecitas de salud que suben y se apagan.
    azar = random.Random(9)
    for i in range(6):
        periodo = azar.uniform(1400, 2200)
        u = ((t + azar.uniform(0, periodo)) % periodo) / periodo
        x = r.x + azar.uniform(0.0, 1.0) * r.w
        y = r.bottom - u * r.h * 1.05
        k = max(2, int(r.w * 0.05 * (1 - u * 0.5)))
        c = tuple(int(v * (1 - u)) for v in (170, 255, 190))
        pygame.draw.rect(screen, c, (x - k, y - k // 3, 2 * k, max(2, k * 2 // 3)))
        pygame.draw.rect(screen, c, (x - k // 3, y - k, max(2, k * 2 // 3), 2 * k))


# -- Resonante ----------------------------------------------------------------------------

def _resonante_atras(screen, r, color, t, fuerza):
    # Ondas de sonido a los dos lados, que salen y se apagan.
    centro = (r.centerx, r.y + int(r.h * 0.3))
    for k in range(4):
        u = ((t / 1100) + k / 4) % 1.0
        radio = int(r.w * (0.3 + 0.7 * u))
        c = tuple(int(v * (1 - u) * fuerza) for v in color)
        caja = pygame.Rect(0, 0, radio * 2, radio * 2)
        caja.center = centro
        if radio > 4:
            pygame.draw.arc(screen, c, caja, -0.6, 0.6, 3)
            pygame.draw.arc(screen, c, caja, math.pi - 0.6, math.pi + 0.6, 3)


def _resonante_delante(screen, r, color, t, fuerza):
    # Un destello rosado en la cabeza, al ritmo de las ondas.
    u = (t / 1100) % 1.0
    if u < 0.3:
        brillo(screen, (r.centerx, r.y + int(r.h * 0.22)), r.w * 0.45,
               tuple(int(c * 0.35 * (1 - u / 0.3) * fuerza) for c in color))


_EFECTOS = {
    "Tecnomante": (_tecnomante_atras, _tecnomante_delante),
    "Forjador": (_forjador_atras, _forjador_delante),
    "Biomante": (_biomante_atras, _biomante_delante),
    "Resonante": (_resonante_atras, _resonante_delante),
}
