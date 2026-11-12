"""La decoración del mapa: muebles, luces y plantas (las imágenes de Anny).

Qué hay y cómo se comporta cada cosa: data/decoracion.py (CATALOGO). Dónde
va: `decoracion` en Hitboxes/<mapa>_objetos.json, que se pone con el editor de
mapa. Aquí se arma un `Mueble` por cada uno al empezar la partida.

- Los "sólidos" tienen una hitbox en su base (solo los pies: por detrás se
  pasa). Esas hitboxes van a `mundo.muebles`, que el mundo trata como parte
  del mapa: los jugadores, aliens y prisioneros chocan con ellas y los caminos
  las rodean. No tapan la vista de nadie (se ve por encima).
- Se dibujan junto con los personajes, ordenados por su base: el que está más
  abajo en la pantalla tapa al de más arriba (screens/partida.py).
- Lo de la pared y lo del piso se dibuja antes, debajo de todos.
"""

import pygame

from data.decoracion import CATALOGO, SOLIDO, ENCIMA, PARED, PISO
from juego import sprites_objetos


def tamano(clave):
    """(ancho, alto) en px del mundo de la imagen ya recortada y agrandada,
    o None si no está en el catálogo o falta el archivo."""
    ficha = CATALOGO.get(clave)
    if ficha is None:
        return None
    img = sprites_objetos.imagen(ficha["archivo"], escala=ficha["escala"])
    return img.get_size() if img is not None else None


def rect_imagen(dato, ancho_mundo, alto_mundo=None):
    """Dónde cae la imagen en el mundo (x, y, ancho, alto), o None."""
    tam = tamano(dato.get("img"))
    if tam is None:
        return None
    alto_mundo = alto_mundo or ancho_mundo
    x = int(round(dato["rx"] * ancho_mundo))
    y = int(round(dato["ry"] * alto_mundo)) - int(dato.get("alzado", 0))
    return (x - tam[0] // 2, y - tam[1], tam[0], tam[1])


def rect_hitbox(dato, ancho_mundo, alto_mundo=None):
    """Lo que ocupa en el piso (x, y, ancho, alto), o None si no se choca."""
    ficha = CATALOGO.get(dato.get("img"))
    if ficha is None or ficha["capa"] != SOLIDO or not ficha.get("base"):
        return None
    caja = rect_imagen(dato, ancho_mundo, alto_mundo)
    if caja is None:
        return None
    x, y, ancho, alto = caja
    fw, fh = ficha["base"]
    w, h = max(8, int(ancho * fw)), max(8, int(alto * fh))
    return (x + (ancho - w) // 2, y + alto - h, w, h)


ALFA_TAPANDO = 120
ALTO_PERSONAJE = 110     # lo que mide un jugador en pantalla, para saber si lo tapa


def marcar_transparentes(muebles, jugadores):
    """Los muebles que tapan a un jugador que está detrás quedan transparentes."""
    cuerpos = [(j.hitbox.bottom, pygame.Rect(j.hitbox.x - 8, j.hitbox.bottom - ALTO_PERSONAJE,
                                             j.hitbox.width + 16, ALTO_PERSONAJE))
               for j in jugadores if not getattr(j, "eliminado", False)]
    for m in muebles:
        m.transparente = any(pies < m.hitbox.bottom and m.rect.colliderect(cuerpo)
                             for pies, cuerpo in cuerpos)


class Mueble:
    def __init__(self, dato, mundo):
        self.dato = dato
        self.clave = dato["img"]
        self.ficha = CATALOGO[self.clave]
        self.capa = self.ficha["capa"]
        self.imagen = sprites_objetos.imagen(self.ficha["archivo"], escala=self.ficha["escala"],
                                             volteado=bool(dato.get("volteado")))
        self.rect = pygame.Rect(rect_imagen(dato, mundo.ancho, mundo.alto))
        caja = rect_hitbox(dato, mundo.ancho, mundo.alto)
        self.solido = caja is not None
        # `hitbox`: con lo que se choca. Lo que no se choca usa una rayita en
        # su base, solo para saber a quién tapa (lo de "encima" de una mesa
        # cuenta desde donde está apoyado, no desde donde se ve).
        base_y = self.rect.bottom + int(dato.get("alzado", 0))
        self.hitbox = pygame.Rect(caja) if caja else pygame.Rect(self.rect.x, base_y - 1, self.rect.width, 1)

        self.transparente = False     # lo pone el dibujo: tapa a un jugador
        self._imagen_alfa = None

    def dibujar(self, screen, offset):
        imagen = self.imagen
        if self.transparente:
            # Un jugador está detrás: el mueble se vuelve medio transparente
            # para que no se pierda de vista (sobre todo el tanque o los
            # armarios, que lo tapan entero).
            if self._imagen_alfa is None:
                self._imagen_alfa = self.imagen.copy()
                self._imagen_alfa.set_alpha(ALFA_TAPANDO)
            imagen = self._imagen_alfa
        screen.blit(imagen, (self.rect.x - offset[0], self.rect.y - offset[1]))


class Erguido:
    """Un objeto del juego parado en el piso (consola, terminal): se ordena
    con los personajes por su base, como un mueble. `dibujo(screen, offset)`
    lo pinta; `rect` es lo que ocupa su dibujo (para saber a quién tapa)."""

    MARGEN = 30          # lo que el dibujo puede salirse de `rect` (borde, palomita)

    def __init__(self, hitbox, rect, dibujo):
        self.hitbox = hitbox
        self.rect = rect
        self._dibujo = dibujo
        self.transparente = False

    def dibujar(self, screen, offset):
        if not self.transparente:
            self._dibujo(screen, offset)
            return
        m = self.MARGEN
        capa = pygame.Surface((self.rect.width + 2 * m, self.rect.height + 2 * m), pygame.SRCALPHA)
        self._dibujo(capa, (self.rect.x - m, self.rect.y - m))
        capa.set_alpha(ALFA_TAPANDO)
        screen.blit(capa, (self.rect.x - m - offset[0], self.rect.y - m - offset[1]))


def hitboxes_estaciones(objetos, mundo):
    """Lo que se choca de los objetos del juego que se paran en el piso: las
    patas de las consolas de navegación, de las terminales del Tecnomante,
    de las terminales NEXUS y de los casilleros (sprites_objetos.hitbox).
    Mismos rects que arman la misión, las estaciones, las zonas y los
    escondites."""
    from data.escondites import ANCHO_ENTRADA, ALTO_ENTRADA
    from data.estaciones import TAMANO_ESTACION
    from misiones.mision import TAMANO_CONSOLA
    rects = []
    for clave, puntos, tam in (
            ("consola", objetos.get("consolas") or (), TAMANO_CONSOLA),
            ("terminal", [(t["rx"], t["ry"]) for t in objetos.get("terminales") or ()], TAMANO_ESTACION),
            ("nexus", objetos.get("nexus") or (), (60, 60)),
            ("escondite", [(e["rx"], e["ry"]) for e in objetos.get("escondites") or ()],
             (ANCHO_ENTRADA, ALTO_ENTRADA))):
        for rx, ry in puntos:
            rect = pygame.Rect(0, 0, *tam)
            rect.center = (int(rx * mundo.ancho), int(ry * mundo.alto))
            caja = sprites_objetos.hitbox(clave, rect)
            if caja is not None:
                rects.append(caja)
    return rects


def crear(objetos, mundo):
    """Los muebles del mapa (los que no estén en el catálogo, o sin imagen,
    se saltan) y sus hitboxes puestas en el mundo, junto con las de las
    consolas y las terminales."""
    muebles = []
    for dato in objetos.get("decoracion") or ():
        if tamano(dato.get("img")) is None:
            continue
        muebles.append(Mueble(dato, mundo))
    if hasattr(mundo, "poner_muebles"):
        mundo.poner_muebles([m.hitbox for m in muebles if m.solido] + hitboxes_estaciones(objetos, mundo))
    return muebles


def de_fondo(muebles, camara):
    """Los que van debajo de los personajes: primero el piso, después la pared."""
    visibles = [m for m in muebles if m.capa in (PISO, PARED) and m.rect.colliderect(camara)]
    visibles.sort(key=lambda m: (m.capa != PISO, m.hitbox.bottom))
    return visibles


def con_personajes(muebles, camara):
    """Los que se ordenan con los personajes (sólidos y lo que va encima)."""
    return [m for m in muebles if m.capa in (SOLIDO, ENCIMA) and m.rect.colliderect(camara)]
