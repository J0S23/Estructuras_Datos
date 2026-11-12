"""Las fotos de perfil de NEXUS (Imagenes/Perfiles/, de Anny).

Una por rol (TECNOMANTE.png, FORJADOR.png, BIOMANTE.png, RESONANTE.png) y una
por cada carpeta de prisioneros (NPC1.png ... NPC8.png = Imagenes/Prisioneros/
NPC_1 ... NPC_8). Vienen de 64x64 con un marco redondo y el nombre escrito
abajo; en el juego se recortan en círculo, sin el nombre, y se achican al
tamaño del avatar.

De quién es cada foto (`clave_de`):
- jugador: la de su rol;
- prisionero: la de su sprite en la partida (`datos["sprite"]`, lo pone App al
  repartir los sprites; el Cambiaformas tiene la de la persona que imita) o,
  si no camina, la primera de sus "sprites" en data/nexus.py;
- bot: igual, con las "sprites" de BOTS. Se ven como cualquier prisionero: las
  cuentas falsas también usan fotos de gente real.
Sin la imagen, `foto` devuelve None y se dibuja el círculo con la inicial.

También el logo de la red (Imagenes/UI/, de Anny): `logo(alto)` es el
planeta solo (nexus_icono.png: encabezado del celular y de la terminal, el
celular vacío) y `logo(alto, completo=True)` el logo con el letrero "NEXUS"
(nexus_logo.png). Los dos salieron del logo de 1254 px recortado y achicado.
"""

import os

import pygame

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(_RAIZ, "Imagenes", "Perfiles")

# El círculo que se recorta del dibujo de 64x64 (deja fuera el nombre de abajo).
CENTRO = (32, 29)
RADIO = 28

_originales = {}   # clave -> Surface recortada en círculo (o None)
_escaladas = {}    # (clave, diámetro) -> Surface


def clave_de(datos):
    """Qué foto le toca a una cuenta (los `datos` de su nodo en el grafo)."""
    if not datos:
        return None
    if datos.get("tipo") == "jugador":
        return (datos.get("nombre") or "").upper() or None
    carpeta = datos.get("sprite") or next(iter(datos.get("sprites") or ()), None)
    if not carpeta:
        return None
    return carpeta.replace("_", "").upper()          # "NPC_3" -> "NPC3"


def _original(clave):
    if clave not in _originales:
        recorte = None
        try:
            imagen = pygame.image.load(os.path.join(CARPETA, f"{clave}.png"))
            try:
                imagen = imagen.convert_alpha()
            except pygame.error:          # (sin ventana todavía)
                pass
            lado = 2 * RADIO
            recorte = pygame.Surface((lado, lado), pygame.SRCALPHA)
            recorte.blit(imagen, (0, 0), (CENTRO[0] - RADIO, CENTRO[1] - RADIO, lado, lado))
            mascara = pygame.Surface((lado, lado), pygame.SRCALPHA)
            pygame.draw.circle(mascara, (255, 255, 255, 255), (RADIO, RADIO), RADIO)
            recorte.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        except (pygame.error, OSError, FileNotFoundError):
            recorte = None
        _originales[clave] = recorte
    return _originales[clave]


def foto(clave, diametro):
    """La foto en círculo de ese diámetro, o None si no hay."""
    if not clave or diametro < 4:
        return None
    llave = (clave, int(diametro))
    if llave not in _escaladas:
        original = _original(clave)
        if original is None:
            _escaladas[llave] = None
        else:
            d = int(diametro)
            if d < original.get_width():
                _escaladas[llave] = pygame.transform.smoothscale(original, (d, d))
            else:
                _escaladas[llave] = pygame.transform.scale(original, (d, d))
    return _escaladas[llave]


_logos = {}       # (archivo, alto) -> Surface o None
CARPETA_UI = os.path.join(_RAIZ, "Imagenes", "UI")


def logo(alto, completo=False):
    """El logo de NEXUS de ese alto (el planeta, o completo con el letrero), o None."""
    archivo = "nexus_logo.png" if completo else "nexus_icono.png"
    llave = (archivo, int(alto))
    if llave not in _logos:
        imagen = None
        try:
            original = pygame.image.load(os.path.join(CARPETA_UI, archivo))
            try:
                original = original.convert_alpha()
            except pygame.error:
                pass
            ancho = max(1, round(original.get_width() * alto / original.get_height()))
            imagen = pygame.transform.smoothscale(original, (ancho, int(alto)))
        except (pygame.error, OSError, FileNotFoundError, ValueError):
            imagen = None
        _logos[llave] = imagen
    return _logos[llave]


def de_nodo(red, nodo, diametro):
    """La foto de una cuenta del grafo de NEXUS (o None)."""
    if red is None or nodo is None:
        return None
    return foto(clave_de(red.grafo.datos.get(nodo)), diametro)
