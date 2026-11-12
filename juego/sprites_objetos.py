"""Las imágenes de los objetos del mapa (Imagenes/Objetos/, de Anny).

Cada cosa que antes se dibujaba con formas (consolas, terminales, cajas de
fusibles, casilleros...) pide aquí su imagen con `sprite(clave, alto)`. Si el
archivo no está, devuelve None y quien la pidió vuelve a su dibujo de formas:
así el juego sigue andando sin la carpeta (y las pruebas viejas también).

Qué archivo usa cada cosa está en ARCHIVOS: para cambiar la imagen de un
objeto basta con cambiar el nombre ahí.
"""

import os

import pygame

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(_RAIZ, "Imagenes", "Objetos")

ARCHIVOS = {
    # Lo de la misión.
    "consola": "OBJ-006_Consola_de_control_encendida.png",   # consolas de navegación (las 3 pantallas prendidas)
    "consola_apagada": "OBJ-006_Consola_de_control_apagada.png",   # ya apagada (de Anny)
    "terminal": "OBJ-043_Terminal_de_acceso.png",         # terminales del Tecnomante
    "fusibles": "OBJ-046_Camara_de_contencion.png",       # cajas de fusibles (trae el rayo)
    "panel": "OBJ-045_Panel_de_informacion_digital.png",  # paneles que repara el Forjador
    "panel_puerta": "OBJ-040_Escaner_biometrico.png",     # los dos paneles de una puerta para dos
    # Los casilleros para esconderse: dos modelos, se reparten por clave.
    # (El 029, el armario de cajones, ahora es decoración: data/decoracion.py.)
    "escondite_0": "OBJ-018_Armario_de_control.png",
    "escondite_1": "OBJ-019_Armario_Blindado.png",
    # Lo que se lleva en el inventario.
    "kit": "OBJ-022_Maletin_de_herramientas.png",
    "decodificador": "OBJ-033_Dispositivo_de_comunicacion.png",
    "senuelo": "OBJ-038_Radio_portatil.png",              # el señuelo del Forjador
    "nexus": "terminal.png",                              # las terminales NEXUS
}
MODELOS_ESCONDITE = 2

# Qué tan alto (px del mundo) se dibuja cada objeto del juego. Los muebles de
# la decoración van a x2 (~124 px): la consola va un poco más grande, para
# que se note que es lo de la misión.
ALTOS = {"consola": 136, "terminal": 84, "panel": 46, "panel_puerta": 40,
         "fusibles": 62, "escondite": 96, "nexus": 120}
# Lo que ocupa en el piso lo que se choca (fracción de la imagen, pegado
# abajo y centrado, como `base` en data/decoracion.py): solo las patas, para
# poder pasar por detrás.
BASES = {"consola": (0.9, 0.38), "terminal": (0.86, 0.3), "nexus": (0.9, 0.36),
         "escondite": (0.9, 0.3)}
# Terminal NEXUS: cuántos px por debajo del centro de su zona va su base
# (antes iba 24 px por encima).
BAJADA_NEXUS = 0
# Si falta la imagen, el tamaño que tendría (para que la hitbox no cambie).
_RESPALDO = {"consola": (127, 136), "terminal": (58, 84), "nexus": (120, 120),
             "escondite": (82, 96)}

_originales = {}     # archivo -> Surface recortada a lo que tiene dibujo (o None)
_escalados = {}      # (archivo, alto, apagado, volteado) -> Surface
_contornos = {}      # (archivo, alto, volteado) -> [puntos]


def _original(archivo):
    if archivo not in _originales:
        imagen = None
        try:
            hoja = pygame.image.load(os.path.join(CARPETA, archivo))
            try:
                hoja = hoja.convert_alpha()
            except pygame.error:      # (sin ventana todavía)
                pass
            caja = hoja.get_bounding_rect()
            if caja.width and caja.height:
                imagen = hoja.subsurface(caja).copy()
        except (pygame.error, OSError):
            imagen = None
        _originales[archivo] = imagen
    return _originales[archivo]


def imagen(archivo, alto=None, escala=None, apagado=False, volteado=False, recortar=True):
    """La imagen `archivo` de Imagenes/Objetos/ recortada a su dibujo y
    agrandada: a `alto` px de alto, o por `escala`. `apagado`: oscurecida y
    sin color (sin luz, usada, rota). None si no está el archivo."""
    base = _original(archivo)
    if base is None:
        return None
    if alto is None:
        alto = max(1, int(round(base.get_height() * (escala or 1))))
    clave = (archivo, int(alto), bool(apagado), bool(volteado))
    if clave not in _escalados:
        ancho = max(1, int(round(base.get_width() * alto / base.get_height())))
        img = pygame.transform.scale(base, (ancho, int(alto)))
        if volteado:
            img = pygame.transform.flip(img, True, False)
        if apagado:
            img = img.copy()
            img.fill((105, 108, 128, 255), special_flags=pygame.BLEND_RGBA_MULT)
        _escalados[clave] = img
    return _escalados[clave]


def sprite(clave, alto=None, escala=None, apagado=False):
    """La imagen del objeto `clave` de ARCHIVOS (o None si falta)."""
    archivo = ARCHIVOS.get(clave)
    return imagen(archivo, alto, escala, apagado) if archivo else None


def contorno(img):
    """Los puntos del borde del dibujo de `img` (para resaltarlo: el objeto
    que tienes cerca se marca siguiendo su forma, no con un recuadro)."""
    clave = id(img)
    if clave not in _contornos:
        _contornos[clave] = pygame.mask.from_surface(img, 40).outline()
    return _contornos[clave]


def resaltar(screen, img, pos, color, grosor=3):
    """Dibuja el borde de `img` (ya puesta en `pos`) de `color`."""
    puntos = contorno(img)
    if len(puntos) > 2:
        pygame.draw.lines(screen, color, True, [(x + pos[0], y + pos[1]) for x, y in puntos], grosor)


def modelo_escondite(clave):
    """Qué modelo de casillero le toca a un escondite (siempre el mismo)."""
    return f"escondite_{sum(map(ord, str(clave))) % MODELOS_ESCONDITE}"


# -- Dónde va cada objeto ------------------------------------------------------------------
# El juego guarda de cada objeto un rect "lógico" (donde se para el jugador
# para usarlo, o lo que ocupa en el piso). Su dibujo va en un lugar fijo
# respecto de ese rect; aquí está ese lugar, para que el juego y el editor de
# mapa lo pongan igual.

def _pie(clave, rect):
    """El punto (x, y) del mundo donde va el centro de la base del dibujo."""
    if clave in ("terminal", "escondite"):
        # A la mitad de su casilla: el jugador se para en la mitad de abajo.
        return rect.centerx, rect.centery
    if clave == "fusibles":
        return rect.centerx, rect.bottom + 4
    if clave == "nexus":
        return rect.centerx, rect.centery + BAJADA_NEXUS   # (rect = su zona)
    return rect.centerx, rect.bottom                # la consola: parada en su rect


HUELLA_FIJA = {"consola": (127, 136)}


def tamano_dibujo(clave):
    """(ancho, alto) del dibujo del objeto `clave` (con o sin imagen)."""
    archivo = "escondite_0" if clave == "escondite" else clave
    img = sprite(archivo, ALTOS[clave])
    if img is not None:
        return img.get_size()
    return _RESPALDO.get(clave, (ALTOS[clave], ALTOS[clave]))


def caja_dibujo(clave, rect, img=None):
    """Dónde va (Rect del mundo) el dibujo del objeto `clave` del juego cuyo
    rect lógico es `rect`. `img`: la imagen que se va a pegar (si no, la
    de siempre)."""
    tam = img.get_size() if img is not None else tamano_dibujo(clave)
    caja = pygame.Rect((0, 0), tam)
    if clave in ("panel", "panel_puerta"):
        caja.center = rect.center                   # adentro de su casilla
    else:
        caja.midbottom = _pie(clave, rect)
    return caja


def hitbox(clave, rect):
    """Lo que se choca del objeto `clave` (Rect del mundo), o None si se pasa
    por encima: las patas de la consola, las terminales y los casilleros."""
    if clave not in BASES:
        return None
    # La consola choca como la 006 de siempre (127x136): el dibujo prendido
    # nuevo es más ancho, y con él las patas cortaban rutas ya puestas.
    ancho, alto = HUELLA_FIJA.get(clave) or tamano_dibujo(clave)
    fw, fh = BASES[clave]
    caja = pygame.Rect(0, 0, max(8, int(ancho * fw)), max(8, int(alto * fh)))
    x, y = _pie(clave, rect)
    # (los últimos 8 px del dibujo de la terminal son su sombra en el piso)
    caja.midbottom = (x, y - 8 if clave == "terminal" else y)
    return caja


def frente(clave, rect, ancho=None, alto=40):
    """El pedazo de piso justo delante (abajo) de lo que se choca: donde se
    para quien lo usa y a donde apuntan las flechas."""
    base = hitbox(clave, rect) or rect
    if clave in ("terminal", "escondite"):
        # La terminal y el casillero: lo que queda de su casilla debajo de las patas.
        return pygame.Rect(rect.x, base.bottom, rect.width, max(1, rect.bottom - base.bottom))
    caja = pygame.Rect(0, 0, ancho or rect.width, alto)
    caja.midtop = base.midbottom
    return caja
