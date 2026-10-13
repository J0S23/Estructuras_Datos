"""Oscuridad y linterna: durante un apagón cada jugador ve solo lo que alumbra.

Normalmente la nave está iluminada. Cuando el evento de apagón (eventos.py)
tumba la luz, se dibuja esto hasta que alguien encienda la caja de fusibles.

Sobre cada viewport se pone una capa negra casi opaca y se le "abren huecos":

- un halo suave alrededor del jugador (lo que ve de cerca),
- el cono de su linterna, hacia donde camina,
- un halo chico alrededor de cada compañero (se ven entre ellos).

De los aliens solo se ve el cuerpo, y solo donde llega la luz: durante el
apagón no se dibujan sus conos, el anillo del Ciego ni sus ojos, y sus señales
(!, ?, zZ) quedan debajo de la oscuridad, igual de oscuras que el alien. La única forma de volver a verlos es prender la caja de fusibles.

Cómo se hace sin que pese: un "mapa de luz" en grises, una sola superficie por
tamaño de viewport que se reutiliza cada frame. El cono se pinta directo con
polígonos más claros, los halos son degradados precalculados que se pegan con
BLEND_RGB_MAX (gana el más claro) y al final todo se multiplica con la imagen
(BLEND_RGB_MULT).

La linterna no se corta en las paredes: alumbra un poco a través de ellas.
Es a propósito para que sea barato; se puede afinar después.
"""

import math

import pygame


OPACIDAD = 232               # 255 = negro total
OPACIDAD_APAGON = 250
RADIO_HALO = 210             # alrededor del jugador
RADIO_HALO_COMPANERO = 110
ALCANCE_LINTERNA = 540
MEDIO_ANGULO_LINTERNA = math.radians(30)
FACTOR_APAGON = 0.5          # cuánto se encoge la luz en un apagón

ANGULO_DIRECCION = {
    "east": 0.0, "south-east": math.pi / 4, "south": math.pi / 2,
    "south-west": 3 * math.pi / 4, "west": math.pi, "north-west": -3 * math.pi / 4,
    "north": -math.pi / 2, "north-east": -math.pi / 4,
}

_capas = {}
_halos = {}


def _capa(tamano):
    if tamano not in _capas:
        _capas[tamano] = pygame.Surface(tamano)
    return _capas[tamano]


def _gris(opacidad):
    v = 255 - opacidad
    return (v, v, v)


def _halo(radio):
    """Círculo blanco en el centro que se va apagando hasta negro en el borde."""
    radio = max(8, int(radio))
    if radio not in _halos:
        halo = pygame.Surface((radio * 2, radio * 2))
        halo.fill((0, 0, 0))
        anillos = 48
        for k in range(anillos, 0, -1):
            t = k / anillos                      # 1 en el borde, ~0 en el centro
            opacidad = int(255 * max(0.0, (t - 0.35) / 0.65) ** 1.4)
            pygame.draw.circle(halo, _gris(opacidad), (radio, radio), int(radio * t))
        _halos[radio] = halo
    return _halos[radio]


class Linterna:
    """Hacia dónde apunta la linterna de un jugador. Gira suave, no de golpe."""

    def __init__(self):
        self.angulo = math.pi / 2

    def actualizar(self, direccion):
        objetivo = ANGULO_DIRECCION.get(direccion, self.angulo)
        diferencia = (objetivo - self.angulo + math.pi) % (2 * math.pi) - math.pi
        self.angulo += diferencia * 0.2


def dibujar(screen, vista, camara, dueño, jugadores, apagon=False):
    """Oscurece el viewport `vista` dejando ver lo que alumbra `dueño`.

    Se arma un "mapa de luz" en grises (blanco = se ve todo, casi negro = no se
    ve nada) y se multiplica con lo que ya está dibujado. Multiplicar es más
    barato que mezclar una capa transparente del tamaño de la pantalla.
    """
    luz = _capa(vista.size)
    factor = FACTOR_APAGON if apagon else 1.0
    luz.fill(_gris(OPACIDAD_APAGON if apagon else OPACIDAD))

    def local(p):
        return (p[0] - camara.x, p[1] - camara.y)

    # El cono de la linterna, en tres capas (de la más tenue a la más
    # brillante) para que el borde no sea tan duro.
    if dueño.preso is None and not dueño.escondido:
        cx, cy = local(dueño.hitbox.center)
        angulo = getattr(getattr(dueño, "linterna", None), "angulo", math.pi / 2)
        alcance = ALCANCE_LINTERNA * factor
        for escala, opacidad in ((1.0, 150), (0.72, 95), (0.45, 55)):
            medio = MEDIO_ANGULO_LINTERNA * escala
            largo = alcance * (0.85 + 0.15 * escala)
            puntos = [(cx, cy)]
            for i in range(9):
                a = angulo - medio + 2 * medio * i / 8
                puntos.append((cx + math.cos(a) * largo, cy + math.sin(a) * largo))
            pygame.draw.polygon(luz, _gris(opacidad), puntos)

    # Halos: el del dueño y uno chico por compañero. Con MAX gana el más claro.
    for jugador in jugadores:
        if jugador is not dueño and (jugador.escondido or getattr(jugador, "eliminado", False)):
            continue
        radio = (RADIO_HALO if jugador is dueño else RADIO_HALO_COMPANERO) * factor
        halo = _halo(radio)
        x, y = local(jugador.hitbox.center)
        luz.blit(halo, (x - halo.get_width() // 2, y - halo.get_height() // 2),
                 special_flags=pygame.BLEND_RGB_MAX)

    screen.blit(luz, vista.topleft, special_flags=pygame.BLEND_RGB_MULT)
