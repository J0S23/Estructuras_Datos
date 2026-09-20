"""Tipografía del juego.

Usa Determination Mono (la misma fuente pixel de EmpatiaQuest, en Fuentes/).
Si el .ttf no está, cae a una fuente del sistema para que el juego siga
corriendo igual.
"""

import os

import pygame


CARPETA_FUENTES = os.path.join(os.path.dirname(__file__), "Fuentes")

ARCHIVOS_FUENTE = (
    "DeterminationMonoWebRegular-Z5oq.ttf",
    "DeterminationMonoWeb.ttf",
)

# Tamaño de cada estilo de texto del juego.
TAMANOS = {
    "title": 56,
    "subtitle": 28,
    "button": 30,
    "body": 26,
    "small": 22,
}

_CACHE = None


def ruta_fuente():
    """Ruta al .ttf de la fuente del juego, o None si no está disponible."""
    for nombre in ARCHIVOS_FUENTE:
        ruta = os.path.join(CARPETA_FUENTES, nombre)
        if os.path.isfile(ruta):
            return ruta
    return None


def _fuente_del_sistema():
    for nombre in ("determination mono web", "consolas", "segoeui", "arial", "verdana"):
        if pygame.font.match_font(nombre):
            return nombre
    return None


def construir_fuentes():
    """Devuelve {estilo: pygame.Font} para todos los estilos del juego.

    Se cachea: llamarla varias veces no vuelve a leer el archivo.
    """
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    ruta = ruta_fuente()
    if ruta:
        _CACHE = {estilo: pygame.font.Font(ruta, tam) for estilo, tam in TAMANOS.items()}
    else:
        nombre = _fuente_del_sistema()
        _CACHE = {
            estilo: pygame.font.SysFont(nombre, tam, bold=(estilo in ("title", "subtitle", "button")))
            for estilo, tam in TAMANOS.items()
        }
    return _CACHE


def fuente(estilo="body"):
    """Atajo para un estilo suelto."""
    return construir_fuentes()[estilo]


_CACHE_TAMANOS = {}


def fuente_de_tamano(px):
    """Fuente del juego en un tamaño arbitrario, cacheada.

    La usan las pantallas que tienen que encoger el texto para que quepa en
    ventanas pequeñas (la ayuda y el panel del ABB), en vez de asumir que la
    pantalla siempre es grande.
    """
    px = max(10, int(px))
    if px in _CACHE_TAMANOS:
        return _CACHE_TAMANOS[px]

    ruta = ruta_fuente()
    if ruta:
        f = pygame.font.Font(ruta, px)
    else:
        f = pygame.font.SysFont(_fuente_del_sistema(), px)
    _CACHE_TAMANOS[px] = f
    return f
