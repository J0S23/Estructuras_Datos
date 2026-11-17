"""Lo chico que se dibuja igual cuadro tras cuadro, hecho una vez.

En la partida, cada vista armaba en CADA cuadro los mismos textos (puntos,
rol, sala, "86 lpm", el letrero de la flecha...) y las mismas capas
semitransparentes (el fondo del pulso, el de los letreros, el halo de las
notas): crear una Surface con alfa y llenarla cuesta más que pegarla, y
`render` de un texto otro tanto. Con 4 jugadores eran ~40 textos y ~20 capas
por cuadro; en el PC de Diego, varios ms (nov 17).

Lo que devuelven estas funciones es COMPARTIDO: se pega con `blit` y ya.
Quien lo quiera cambiar (set_alpha, dibujar encima) hace `.copy()` antes.
Al cambiar de idioma se vacía (los textos pasan por `tr`).
"""

import pygame

from juego import idioma

MAXIMO = 600          # entradas por caché antes de vaciarla (textos que cambian: reloj, lpm)

_textos = {}
_capas = {}
_elipses = {}


def texto(f, contenido, color, antialias=True):
    """`f.render(contenido, antialias, color)`, guardado."""
    clave = (id(f), contenido, tuple(color), antialias)
    img = _textos.get(clave)
    if img is None:
        if len(_textos) > MAXIMO:
            _textos.clear()
        img = _textos[clave] = f.render(contenido, antialias, color)
    return img


def capa(tamano, rgba):
    """Una Surface con alfa de `tamano` llena de `rgba` (los fondos oscuros
    semitransparentes de los letreros y del pulso)."""
    clave = (max(1, int(tamano[0])), max(1, int(tamano[1])), tuple(rgba))
    img = _capas.get(clave)
    if img is None:
        if len(_capas) > MAXIMO:
            _capas.clear()
        img = pygame.Surface(clave[:2], pygame.SRCALPHA)
        img.fill(clave[2])
        _capas[clave] = img
    return img


def elipse(tamano, rgba):
    """Una Surface con alfa de `tamano` con una elipse llena de `rgba` que
    ocupa toda la superficie (los halos que laten)."""
    clave = (max(1, int(tamano[0])), max(1, int(tamano[1])), tuple(rgba))
    img = _elipses.get(clave)
    if img is None:
        if len(_elipses) > MAXIMO:
            _elipses.clear()
        img = pygame.Surface(clave[:2], pygame.SRCALPHA)
        pygame.draw.ellipse(img, clave[2], img.get_rect())
        _elipses[clave] = img
    return img


_circulos = {}


def circulo(lado, rgba, radio):
    """Una Surface con alfa de `lado` x `lado` con un círculo de `rgba` y
    `radio` en el centro (los halos de las piezas)."""
    clave = (int(lado), tuple(rgba), int(radio))
    img = _circulos.get(clave)
    if img is None:
        if len(_circulos) > MAXIMO:
            _circulos.clear()
        img = pygame.Surface((clave[0], clave[0]), pygame.SRCALPHA)
        pygame.draw.circle(img, clave[1], (clave[0] // 2, clave[0] // 2), clave[2])
        _circulos[clave] = img
    return img


_recortes = {}


def pegar(screen, img, pos):
    """`screen.blit(img, pos)`, pero pegando solo el pedazo dibujado de `img`
    (su get_bounding_rect, guardado por imagen). Los cuadros de los
    personajes miden 158x158 y el muñeco ocupa ~60x100: el resto es
    transparente y mezclarlo costaba ~4 veces más que el muñeco (16 por cuadro
    con 4 jugadores). Da los mismos píxeles: lo transparente no cambia nada.
    Solo para imágenes que no se modifican después (los cuadros cargados)."""
    caja = _recortes.get(img)
    if caja is None:
        if len(_recortes) > 4000:
            _recortes.clear()
        caja = _recortes[img] = img.get_bounding_rect()
    return screen.blit(img, (pos[0] + caja.x, pos[1] + caja.y), caja)


@idioma.al_cambiar
def limpiar():
    _textos.clear()
