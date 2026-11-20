"""Estilo común de las pantallas de fuera de la partida (cuántos juegan,
dificultad, controles, roles, ayuda, créditos, carga, jugar en red): el mismo
espacio y el mismo vidrio con neón del menú principal y los botones.

- `fondo(screen)`: degradado y nebulosa (los del árbol de logros) con
  estrellas en tres capas que pasan lento y titilan.
- `titulo(screen, texto, centro, tam)`: título con un halo de su color y una
  línea de adorno debajo.
- `tarjeta(screen, rect, elegido, color)`: vidrio oscuro con una franja del
  color a la izquierda; la escogida brilla, late, la cruza un reflejo y lleva
  el borde de neón.
- `pie(screen, texto, y)`: las pistas de teclas de abajo, con cada "[TECLA]"
  dibujada como una tecla.
- `icono_pantalla(screen, rect, n)`: el dibujito de cómo se parte la pantalla
  con n jugadores.

Con los efectos apagados (juego/efectos.py) se ve igual pero quieto.
"""

import math
import random
import re

import pygame

from juego import efectos
from juego.fuentes import fuente_de_tamano

COLOR_TEXTO = (240, 242, 252)
COLOR_TENUE = (160, 168, 206)
COLOR_ORO = (255, 214, 64)
COLOR_NEON = (90, 220, 255)
COLOR_ROSA = (233, 110, 255)
COLOR_PISTA = (194, 216, 248)
# El color de cada jugador antes de escoger rol (J1..J4).
COLOR_JUGADOR = [(110, 200, 255), (255, 170, 80), (110, 220, 140), (240, 120, 200)]


def _t():
    return pygame.time.get_ticks() if efectos.ACTIVOS else 0


def _mezclar(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# -- Fondo ----------------------------------------------------------------------------------

_estrellas = {}


def fondo(screen, rect=None):
    """El espacio: degradado, nebulosa y estrellas que pasan (tres capas)."""
    from screens.logros import _fondo
    rect = rect or screen.get_rect()
    base = _fondo(rect.size)
    screen.blit(base, rect.topleft)
    capas = _estrellas.get(rect.size)
    if capas is None:
        azar = random.Random(23)
        cantidad = max(30, rect.w * rect.h // 9000)
        capas = _estrellas[rect.size] = [
            [(azar.uniform(0, rect.w), azar.uniform(0, rect.h), azar.uniform(0, 6.3)) for _ in range(cantidad // n)]
            for n in (2, 3, 6)]
        if len(_estrellas) > 8:
            _estrellas.clear()
            _estrellas[rect.size] = capas
    t = _t()
    for k, (capa, vel, brillo) in enumerate(zip(capas, (0.004, 0.009, 0.02), (110, 170, 235))):
        for x0, y, fase in capa:
            x = rect.x + (x0 - t * vel) % rect.w
            c = int(brillo * (0.7 + 0.3 * math.sin(t / 600 + fase)))
            color = (c, c, min(255, c + 25))
            if k == 2:
                pygame.draw.line(screen, color, (x, rect.y + y), (x + 1, rect.y + y))
            else:
                screen.set_at((int(x), int(rect.y + y)), color)


# -- Títulos --------------------------------------------------------------------------------

_titulos = {}


def titulo(screen, texto, centro, tam, color=COLOR_TEXTO, brillo=COLOR_NEON, adorno=True):
    """Un título con halo de color detrás y una línea de adorno debajo.
    Devuelve su rect."""
    clave = (texto, tam, color, brillo)
    img = _titulos.get(clave)
    if img is None:
        if len(_titulos) > 80:
            _titulos.clear()
        f = fuente_de_tamano(tam)
        letras = f.render(texto, True, color)
        w, h = letras.get_size()
        margen = max(10, tam // 2)
        img = pygame.Surface((w + 2 * margen, h + 2 * margen))
        img.fill((0, 0, 0))
        halo = f.render(texto, True, tuple(int(c * 0.55) for c in brillo))
        chico = pygame.Surface(img.get_size())
        chico.fill((0, 0, 0))
        chico.blit(halo, (margen, margen))
        for _ in range(2):
            chico = pygame.transform.smoothscale(
                pygame.transform.smoothscale(chico, (max(1, chico.get_width() // 6), max(1, chico.get_height() // 6))),
                img.get_size())
        img.blit(chico, (0, 0))
        _titulos[clave] = (img, letras, margen)
        img = _titulos[clave]
    resplandor, letras, margen = img
    rect = letras.get_rect(center=centro)
    screen.blit(resplandor, (rect.x - margen, rect.y - margen), special_flags=pygame.BLEND_RGB_ADD)
    screen.blit(letras, rect)
    if adorno:
        y = rect.bottom + max(6, tam // 4)
        largo = max(rect.w // 2, 120)
        for i in range(largo // 2):
            v = 1 - i / (largo / 2)
            c = _mezclar((0, 0, 0), brillo, v)
            screen.set_at((rect.centerx + i, y), c)
            screen.set_at((rect.centerx - i, y), c)
        pygame.draw.polygon(screen, brillo, [(rect.centerx, y - 4), (rect.centerx + 4, y),
                                             (rect.centerx, y + 4), (rect.centerx - 4, y)])
    return rect


def texto(screen, cadena, f, pos, color=COLOR_TEXTO, ancla="topleft", sombra=True):
    """Un texto con sombrita (se lee mejor sobre las estrellas). Devuelve su rect."""
    img = f.render(cadena, True, color)
    rect = img.get_rect(**{ancla: pos})
    if sombra:
        screen.blit(f.render(cadena, True, (6, 6, 14)), rect.move(1, 2))
    screen.blit(img, rect)
    return rect


# -- Tarjetas -------------------------------------------------------------------------------

_vidrios = {}


def _vidrio(tamano, elegido, radio):
    clave = (tamano, elegido, radio)
    img = _vidrios.get(clave)
    if img is None:
        if len(_vidrios) > 80:
            _vidrios.clear()
        w, h = tamano
        img = pygame.Surface(tamano, pygame.SRCALPHA)
        arriba = (36, 32, 84, 230) if elegido else (20, 20, 44, 215)
        abajo = (22, 48, 96, 230) if elegido else (12, 12, 28, 215)
        for y in range(h):
            k = y / max(1, h - 1)
            pygame.draw.line(img, tuple(int(arriba[i] + (abajo[i] - arriba[i]) * k) for i in range(4)), (0, y), (w, y))
        mascara = pygame.Surface(tamano, pygame.SRCALPHA)
        pygame.draw.rect(mascara, (255, 255, 255, 255), (0, 0, w, h), border_radius=radio)
        img.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        reflejo = pygame.Surface((max(1, w - 2 * radio), max(2, h // 5)), pygame.SRCALPHA)
        for y in range(reflejo.get_height()):
            pygame.draw.line(reflejo, (255, 255, 255, int(14 * (1 - y / reflejo.get_height()))),
                             (0, y), (reflejo.get_width(), y))
        img.blit(reflejo, (radio, 3))
        _vidrios[clave] = img
    return img


_halos_borde = {}


def _halo_borde(tamano, color, radio):
    """El resplandor de la tarjeta escogida: solo alrededor del borde. (El de
    los botones, ui_components._halo, se arma de una superficie 6 veces más
    chica: en una tarjeta grande se veía una mancha escalonada por dentro.)"""
    clave = (tamano, color, radio)
    img = _halos_borde.get(clave)
    if img is None:
        if len(_halos_borde) > 60:
            _halos_borde.clear()
        w, h = tamano[0] + 36, tamano[1] + 36
        img = pygame.Surface((w, h))
        img.fill((0, 0, 0))
        # Anillos del borde hacia afuera, cada uno más tenue.
        for k in range(18, 0, -1):
            f = (1 - k / 19) ** 1.8
            c = tuple(int(v * f) for v in color)
            pygame.draw.rect(img, c, pygame.Rect(18 - k, 18 - k, tamano[0] + 2 * k, tamano[1] + 2 * k),
                             border_radius=radio + k)
        # Por dentro, solo una orilla de unos px que se apaga hacia el centro.
        for k in range(1, 9):
            f = (1 - k / 9) ** 2
            c = tuple(int(v * f) for v in color)
            pygame.draw.rect(img, c, pygame.Rect(18 + k, 18 + k, tamano[0] - 2 * k, tamano[1] - 2 * k),
                             border_radius=max(2, radio - k))
        pygame.draw.rect(img, (0, 0, 0), pygame.Rect(27, 27, tamano[0] - 18, tamano[1] - 18),
                         border_radius=max(2, radio - 9))
        _halos_borde[clave] = img
    return img


def tarjeta(screen, rect, elegido=False, color=COLOR_NEON, apagada=False, radio=12, franja=True):
    """Una tarjeta de vidrio. La escogida brilla (halo que late), la cruza un
    reflejo y lleva el borde de neón de su color."""
    from juego.ui_components import _reflejo
    t = _t()
    if elegido and not apagada:
        latido = 0.6 + 0.4 * math.sin(t / 280)
        nivel = round(latido * 4) / 4
        halo = _halo_borde(rect.size, tuple(int(c * 0.45 * nivel) for c in color), radio)
        screen.blit(halo, (rect.x - 18, rect.y - 18), special_flags=pygame.BLEND_RGB_ADD)
    screen.blit(_vidrio(rect.size, elegido and not apagada, radio), rect.topleft)
    if franja:
        tira = pygame.Rect(rect.x, rect.y + radio // 2, 5, rect.h - radio)
        pygame.draw.rect(screen, color if not apagada else (70, 74, 100), tira, border_radius=3)
    if apagada:
        borde = (60, 64, 92)
    elif elegido:
        borde = color
    else:
        borde = _mezclar(color, (20, 20, 40), 0.55)
    pygame.draw.rect(screen, borde, rect, 2, border_radius=radio)
    if elegido and not apagada and efectos.ACTIVOS:
        periodo = 2800
        dentro = t % periodo
        if dentro < 1200:
            x = rect.x - rect.h + int((dentro / 1200) * (rect.w + rect.h * 2))
            recorte = screen.get_clip()
            screen.set_clip(rect.inflate(-4, -4).clip(recorte))
            # En tarjetas altas el reflejo va en pedazos de 120 px; cada uno se
            # corre 60 px a la izquierda (lo que baja la diagonal en 120 px)
            # para que la franja siga recta y no se vea partida en escalones.
            tramo = min(120, rect.h)
            reflejo = _reflejo(tramo)
            for k, y in enumerate(range(rect.y, rect.bottom, tramo)):
                screen.blit(reflejo, (x - k * (tramo // 2), y), special_flags=pygame.BLEND_RGB_ADD)
            screen.set_clip(recorte)


def panel(screen, rect, color=COLOR_NEON, titulo_panel=None, f=None, radio=14):
    """Un recuadro grande de vidrio (ayuda, detalles). Devuelve dónde empieza
    su contenido."""
    screen.blit(_vidrio(rect.size, False, radio), rect.topleft)
    pygame.draw.rect(screen, _mezclar(color, (20, 20, 40), 0.45), rect, 2, border_radius=radio)
    if not titulo_panel:
        return rect.y + 14
    f = f or fuente_de_tamano(18)
    y = rect.y + 12
    texto(screen, titulo_panel, f, (rect.x + 18, y), color)
    y += f.get_linesize() + 4
    pygame.draw.line(screen, _mezclar(color, (20, 20, 40), 0.5), (rect.x + 16, y), (rect.right - 16, y), 1)
    return y + 8


# -- Pistas de teclas -----------------------------------------------------------------------

_TECLA = re.compile(r"\[([^\]]+)\]")


def pie(screen, cadena, y, f=None, color=COLOR_PISTA, x=None):
    """Las pistas de abajo ("[ENTER] continuar  [ESC] volver"), centradas en
    `y` (y en `x`, si no en el medio), con cada [TECLA] dibujada como una tecla."""
    from juego.idioma import tr
    f = f or fuente_de_tamano(max(13, min(18, screen.get_width() // 80)))
    cadena = tr(cadena)
    trozos = []
    pos = 0
    for m in _TECLA.finditer(cadena):
        if m.start() > pos:
            trozos.append(("texto", cadena[pos:m.start()]))
        trozos.append(("tecla", m.group(1)))
        pos = m.end()
    if pos < len(cadena):
        trozos.append(("texto", cadena[pos:]))
    imagenes = []
    for tipo, t in trozos:
        img = f.render(t, True, COLOR_TEXTO if tipo == "tecla" else color)
        imagenes.append((tipo, img, img.get_width() + (16 if tipo == "tecla" else 0)))
    total = sum(w for _, _, w in imagenes)
    alto = f.get_height() + 8
    fondo_pie = pygame.Rect(0, 0, total + 36, alto + 10)
    fondo_pie.center = (screen.get_width() // 2 if x is None else x, y)
    capa = pygame.Surface(fondo_pie.size, pygame.SRCALPHA)
    pygame.draw.rect(capa, (8, 8, 20, 170), capa.get_rect(), border_radius=fondo_pie.h // 2)
    screen.blit(capa, fondo_pie.topleft)
    x = fondo_pie.x + 18
    for tipo, img, w in imagenes:
        if tipo == "tecla":
            caja = pygame.Rect(x, y - alto // 2, w, alto)
            pygame.draw.rect(screen, (14, 14, 30), caja.move(0, 2), border_radius=6)
            pygame.draw.rect(screen, (46, 50, 86), caja, border_radius=6)
            pygame.draw.rect(screen, (120, 132, 190), caja, 1, border_radius=6)
            screen.blit(img, img.get_rect(center=caja.center))
        else:
            screen.blit(img, img.get_rect(midleft=(x, y)))
        x += w
    return fondo_pie


# -- Dibujitos ------------------------------------------------------------------------------

def icono_pantalla(screen, rect, n, elegido=False):
    """Una pantallita partida como queda con n jugadores (cada parte del
    color de su jugador; con 3, el cuarto cuadro es el panel del equipo)."""
    marco = rect.copy()
    pygame.draw.rect(screen, (8, 8, 18), marco, border_radius=6)
    pygame.draw.rect(screen, (150, 160, 210) if elegido else (90, 98, 140), marco, 2, border_radius=6)
    adentro = marco.inflate(-8, -8)
    g = 3
    if n == 2:
        partes = [pygame.Rect(adentro.x, adentro.y, adentro.w // 2 - g // 2, adentro.h),
                  pygame.Rect(adentro.centerx + g // 2 + 1, adentro.y, adentro.w // 2 - g // 2 - 1, adentro.h)]
    else:
        mw, mh = adentro.w // 2 - g // 2, adentro.h // 2 - g // 2
        partes = [pygame.Rect(adentro.x, adentro.y, mw, mh),
                  pygame.Rect(adentro.right - mw, adentro.y, mw, mh),
                  pygame.Rect(adentro.x, adentro.bottom - mh, mw, mh),
                  pygame.Rect(adentro.right - mw, adentro.bottom - mh, mw, mh)]
    t = _t()
    for i, parte in enumerate(partes):
        if n == 3 and i == 3:
            # El panel del equipo: rayitas.
            pygame.draw.rect(screen, (30, 32, 56), parte, border_radius=3)
            for k in range(3):
                yy = parte.y + 6 + k * max(4, parte.h // 4)
                pygame.draw.line(screen, (90, 98, 140), (parte.x + 6, yy), (parte.right - 6 - k * 6, yy), 2)
            continue
        color = COLOR_JUGADOR[i % 4]
        k = 0.55 + (0.25 * (0.5 + 0.5 * math.sin(t / 400 + i)) if elegido else 0)
        pygame.draw.rect(screen, _mezclar((10, 10, 20), color, k * 0.55), parte, border_radius=3)
        pygame.draw.rect(screen, _mezclar((10, 10, 20), color, k), parte, 1, border_radius=3)
        # Un muñequito en el medio.
        cx, cy = parte.center
        r = max(2, min(parte.w, parte.h) // 8)
        pygame.draw.circle(screen, color, (cx, cy - r), r)
        pygame.draw.rect(screen, color, (cx - r, cy, 2 * r, int(r * 1.6)), border_radius=r // 2 + 1)


def medidor(screen, centro, nivel, total, color, tam=10):
    """Rombitos llenos hasta `nivel` (la dificultad)."""
    paso = tam * 2 + 4
    x0 = centro[0] - (paso * total - 4) // 2 + tam
    for i in range(total):
        cx = x0 + i * paso
        puntos = [(cx, centro[1] - tam), (cx + tam, centro[1]), (cx, centro[1] + tam), (cx - tam, centro[1])]
        if i < nivel:
            pygame.draw.polygon(screen, color, puntos)
        pygame.draw.polygon(screen, color if i < nivel else (80, 86, 120), puntos, 2)


def icono_control(screen, rect, mando, color):
    """Un tecladito o un mando, del color dado, dentro de `rect`."""
    oscuro = _mezclar((10, 10, 20), color, 0.35)
    if not mando:
        cuerpo = pygame.Rect(0, 0, rect.w, int(rect.w * 0.42))
        cuerpo.center = rect.center
        pygame.draw.rect(screen, oscuro, cuerpo, border_radius=4)
        pygame.draw.rect(screen, color, cuerpo, 2, border_radius=4)
        tecla = max(3, cuerpo.w // 11)
        for fila in range(3):
            y = cuerpo.y + 4 + fila * (tecla + 2)
            corrida = fila % 2 * tecla // 2
            for x in range(cuerpo.x + 5 + corrida, cuerpo.right - tecla - 3, tecla + 2):
                pygame.draw.rect(screen, color, (x, y, tecla, tecla - 1), 1)
        espacio = pygame.Rect(0, 0, cuerpo.w // 2, max(2, tecla - 2))
        espacio.midbottom = (cuerpo.centerx, cuerpo.bottom - 4)
        pygame.draw.rect(screen, color, espacio, 1)
        return
    w, h = rect.w, int(rect.w * 0.55)
    cuerpo = pygame.Rect(0, 0, w, h)
    cuerpo.center = rect.center
    r = h // 2
    # Dos agarraderas redondas y el puente del medio.
    for cx in (cuerpo.x + r, cuerpo.right - r):
        pygame.draw.circle(screen, oscuro, (cx, cuerpo.centery + 2), r)
        pygame.draw.circle(screen, color, (cx, cuerpo.centery + 2), r, 2)
    puente = pygame.Rect(cuerpo.x + r, cuerpo.y, w - 2 * r, int(h * 0.8))
    pygame.draw.rect(screen, oscuro, puente)
    pygame.draw.line(screen, color, puente.topleft, puente.topright, 2)
    # La cruz y los cuatro botones.
    k = max(2, r // 3)
    cx, cy = cuerpo.x + r, cuerpo.centery
    pygame.draw.rect(screen, color, (cx - k, cy - k // 3, 2 * k, max(2, k * 2 // 3)))
    pygame.draw.rect(screen, color, (cx - k // 3, cy - k, max(2, k * 2 // 3), 2 * k))
    cx = cuerpo.right - r
    for dx, dy in ((0, -k), (k, 0), (0, k), (-k, 0)):
        pygame.draw.circle(screen, color, (cx + dx, cy + dy), max(2, k // 2))


_brillos = {}


def _brillo_elipse(tamano, color):
    """Una mancha de luz ovalada y difusa (se suma con BLEND_RGB_ADD)."""
    clave = (tamano, color)
    img = _brillos.get(clave)
    if img is None:
        if len(_brillos) > 40:
            _brillos.clear()
        w, h = tamano
        img = pygame.Surface(tamano)
        img.fill((0, 0, 0))
        for k in range(12, 0, -1):
            f = k / 12
            c = tuple(int(v * (1 - f) ** 1.6) for v in color)
            r = pygame.Rect(0, 0, int(w * f), int(h * f))
            r.center = (w // 2, h // 2)
            pygame.draw.ellipse(img, c, r)
        _brillos[clave] = img
    return img


def pedestal(screen, centro_abajo, ancho, color):
    """La luz de color bajo un personaje (retratos de la elección de rol)."""
    luz = _brillo_elipse((int(ancho * 1.5), max(20, ancho // 2)), tuple(int(c * 0.6) for c in color))
    screen.blit(luz, luz.get_rect(center=centro_abajo), special_flags=pygame.BLEND_RGB_ADD)
    base = pygame.Rect(0, 0, ancho, max(8, ancho // 7))
    base.center = centro_abajo
    pygame.draw.ellipse(screen, _mezclar((10, 10, 20), color, 0.3), base)
    pygame.draw.ellipse(screen, color, base, 2)
