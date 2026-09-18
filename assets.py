"""Carga de imágenes con respaldo: si el archivo aún no existe, no rompe nada.

Mientras el equipo va agregando arte a Imagenes/ (ver Imagenes/README.md),
las pantallas siguen funcionando con colores sólidos de relleno.

Además tolera que el nombre del archivo no sea exactamente el esperado: si se
pide "Imagenes/Fondos/fondo_menu.png" y en esa carpeta hay un
"FondoDeMenu.jpeg", lo encuentra igual. Así el equipo de arte no tiene que
acertarle al nombre exacto para que su imagen aparezca en el juego.
"""

import os

import pygame

_CACHE = {}
_RESUELTAS = {}

EXTENSIONES = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

# Palabras clave por imagen esperada, de la más específica a la más general.
# Si no existe el archivo con el nombre exacto, se busca en la misma carpeta
# un archivo cuyo nombre contenga alguna de estas palabras.
ALIAS = {
    "fondo_menu": ("fondomenu", "fondodemenu", "menu"),
    "fondo_ciudad": ("fondociudad", "ciudad"),
    "icono_confianza": ("confianza",),
    "icono_verificacion": ("verificacion", "verificado"),
    "icono_desinformacion": ("desinformacion",),
    "icono_convivencia": ("convivencia",),
    "ciudadano_idle": ("ciudadano",),
    "periodista_idle": ("periodista",),
    "influencer_idle": ("influencer",),
}


def _normalizar(nombre):
    return "".join(c for c in nombre.lower() if c.isalnum())


def _resolver_ruta(ruta_relativa):
    """Devuelve la ruta real en disco para `ruta_relativa`, buscando por nombre
    aproximado si el archivo exacto no está. None si no hay nada parecido."""
    if ruta_relativa in _RESUELTAS:
        return _RESUELTAS[ruta_relativa]

    raiz = os.path.dirname(__file__)
    ruta_exacta = os.path.join(raiz, ruta_relativa)
    resultado = None

    if os.path.isfile(ruta_exacta):
        resultado = ruta_exacta
    else:
        carpeta = os.path.dirname(ruta_exacta)
        base = os.path.splitext(os.path.basename(ruta_relativa))[0]
        if os.path.isdir(carpeta):
            candidatos = [
                f for f in sorted(os.listdir(carpeta))
                if f.lower().endswith(EXTENSIONES)
            ]
            claves = (base,) + ALIAS.get(base, ())
            for clave in claves:
                clave_norm = _normalizar(clave)
                for archivo in candidatos:
                    if clave_norm and clave_norm in _normalizar(os.path.splitext(archivo)[0]):
                        resultado = os.path.join(carpeta, archivo)
                        break
                if resultado:
                    break

    _RESUELTAS[ruta_relativa] = resultado
    return resultado


def cargar_imagen(ruta_relativa, tamano=None):
    """Devuelve una Surface para `ruta_relativa` (relativa a la raíz del
    proyecto), o None si no existe ningún archivo parecido o pygame no lo
    puede leer.

    `tamano`, si se da, es un (ancho, alto) al que se escala la imagen.
    """
    clave = (ruta_relativa, tamano)
    if clave in _CACHE:
        return _CACHE[clave]

    ruta_absoluta = _resolver_ruta(ruta_relativa)
    imagen = None
    if ruta_absoluta:
        try:
            imagen = pygame.image.load(ruta_absoluta).convert_alpha()
            if tamano is not None:
                imagen = pygame.transform.smoothscale(imagen, tamano)
        except pygame.error:
            imagen = None

    _CACHE[clave] = imagen
    return imagen


def dibujar_fondo_o_color(screen, ruta_relativa, color_respaldo):
    """Dibuja la imagen de fondo si existe; si no, rellena con color_respaldo."""
    tamano = screen.get_size()
    imagen = cargar_imagen(ruta_relativa, tamano)
    if imagen is not None:
        screen.blit(imagen, (0, 0))
    else:
        screen.fill(color_respaldo)
