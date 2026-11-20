"""El vidrio del HUD de la partida (con los efectos visuales prendidos): el
mismo estilo de los menús (screens/estilo.py, juego/ui_components.Button),
pero hecho para dibujarse cada cuadro en 2-4 vistas, así que todo se guarda
ya armado y por cuadro solo se pega.

- `caja(screen, rect, color)`: vidrio oscuro con degradado, un brillo fino
  arriba y el borde de neón del color (un poco apagado).
- `barra(screen, rect, valor, color, color_final)`: canal redondeado y el
  relleno en degradado con un brillo encima.
- `brillo(screen, centro, radio, color)`: una mancha de luz para sumar (el
  corazón que late).

Sin efectos (juego/efectos.ACTIVOS False) el HUD se dibuja como antes: estas
funciones solo se llaman con los efectos prendidos.
"""

import pygame

_cajas = {}
_barras = {}
_brillos = {}


def _mezclar(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def caja(screen, rect, color=(120, 132, 190), alfa=215, radio=8):
    """Pega el vidrio en `rect` (guardado por tamaño, color, alfa y radio)."""
    clave = (rect.size, tuple(color), alfa, radio)
    img = _cajas.get(clave)
    if img is None:
        if len(_cajas) > 240:
            _cajas.clear()
        img = _cajas[clave] = _armar_caja(rect.size, color, alfa, radio)
    screen.blit(img, rect.topleft)


def _armar_caja(tam, color, alfa, radio):
    w, h = tam
    img = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
    arriba, abajo = (26, 26, 52), (12, 12, 26)
    for y in range(h):
        c = _mezclar(arriba, abajo, y / max(1, h - 1))
        pygame.draw.line(img, (*c, alfa), (0, y), (w, y))
    mascara = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
    pygame.draw.rect(mascara, (255, 255, 255, 255), mascara.get_rect(), border_radius=radio)
    img.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    # Brillo fino arriba y el borde de neón.
    if w > 2 * radio + 4:
        pygame.draw.line(img, (*_mezclar(color, (255, 255, 255), 0.5), 70), (radio, 2), (w - radio, 2), 1)
    pygame.draw.rect(img, (*_mezclar(color, (20, 20, 40), 0.35), 255), img.get_rect(), 2, border_radius=radio)
    return img


def _en_degradado(colores, t):
    if len(colores) == 1:
        return colores[0]
    tramo = min(len(colores) - 2, int(t * (len(colores) - 1)))
    return _mezclar(colores[tramo], colores[tramo + 1], t * (len(colores) - 1) - tramo)


def barra(screen, rect, valor, color, color_final=None, medio=None):
    """Una barra redondeada llena hasta `valor` (0-1). El relleno va de
    `color` a `color_final` (pasando por `medio`, si se da) a lo largo de
    toda la barra."""
    valor = max(0.0, min(1.0, valor))
    radio = max(2, rect.h // 2)
    clave = ("canal", rect.size)
    canal = _barras.get(clave)
    if canal is None:
        canal = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(canal, (10, 10, 22, 230), canal.get_rect(), border_radius=radio)
        pygame.draw.rect(canal, (70, 78, 120, 255), canal.get_rect(), 1, border_radius=radio)
        _barras[clave] = canal
    screen.blit(canal, rect.topleft)
    lleno = int(rect.w * valor)
    if lleno <= 1:
        return
    colores = [tuple(color)] + ([tuple(medio)] if medio else []) + [tuple(color_final or color)]
    clave = ("relleno", rect.size, tuple(colores))
    img = _barras.get(clave)
    if img is None:
        if len(_barras) > 120:
            _barras.clear()
        img = pygame.Surface(rect.size, pygame.SRCALPHA)
        for x in range(rect.w):
            c = _en_degradado(colores, x / max(1, rect.w - 1))
            pygame.draw.line(img, (*c, 255), (x, 0), (x, rect.h))
            pygame.draw.line(img, (*_mezclar(c, (255, 255, 255), 0.45), 255), (x, 1), (x, max(1, rect.h // 3)))
        mascara = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mascara, (255, 255, 255, 255), mascara.get_rect(), border_radius=radio)
        img.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        _barras[clave] = img
    screen.blit(img, rect.topleft, pygame.Rect(0, 0, lleno, rect.h))


def brillo(screen, centro, radio, color):
    """Una mancha de luz redonda (se suma). Guardada por radio y color."""
    radio = max(2, int(radio) // 2 * 2)
    clave = (radio, tuple(color))
    img = _brillos.get(clave)
    if img is None:
        if len(_brillos) > 120:
            _brillos.clear()
        img = pygame.Surface((radio * 2, radio * 2))
        img.fill((0, 0, 0))
        for k in range(14, 0, -1):
            f = (1 - k / 15) ** 2
            pygame.draw.circle(img, tuple(int(c * f) for c in color), (radio, radio), int(radio * k / 14))
        _brillos[clave] = img
    screen.blit(img, img.get_rect(center=(int(centro[0]), int(centro[1]))), special_flags=pygame.BLEND_RGB_ADD)
