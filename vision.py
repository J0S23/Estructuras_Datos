"""Campo de visión: los jugadores no ven a través de las paredes.

Como en Among Us, cada jugador solo ve bien lo que tiene en línea recta sin
paredes de por medio y dentro de un radio. Lo demás del mapa se sigue viendo,
pero oscurecido, y los aliens que estén fuera de esa zona no se dibujan.

Cómo se calcula el "polígono de visión" (Campo): desde el centro del jugador se
lanzan rayos en todas las direcciones y cada uno se corta en la primera pared
que toca (o en el radio, si no toca ninguna). Unir las puntas de los rayos da
el polígono. Además de unos rayos repartidos parejo, se lanza un par de rayos
rozando cada esquina de las paredes cercanas: así las sombras de las esquinas
quedan con borde recto y no "serruchado".

El choque rayo-rectángulo es la prueba de "las losas" (slab test): para cada
eje se ve en qué tramo del rayo está dentro del rectángulo, y si los tramos de
los dos ejes se cruzan, el rayo entra al rectángulo donde empieza el cruce.
Las paredes son pocas (unos 20 rectángulos), así que esto va en Python puro.

Obstáculos: las paredes del mapa (incluida la puerta de la prisión, que la
partida agrega a mundo.paredes), las puertas para dos cerradas y las
compuertas bajadas.
"""

import math


RADIO_VISION = 640           # hasta dónde ve un jugador, en píxeles del mundo
RAYOS = 120                  # rayos repartidos parejo (más las esquinas)
ROCE_ESQUINA = 0.0008        # cuánto se desvía el rayo que roza una esquina
# Las paredes se ven "de frente" (vista 3/4): el dibujo de la pared sobresale
# hacia arriba de su hitbox. Para que la cara de la pared no quede negra, el
# rayo se mete un poco en ella, más cuando mira hacia arriba.
ENTRA_EN_PARED = 18
ENTRA_EN_PARED_ARRIBA = 70


def obstaculos(mundo, puertas_dobles=(), compuertas=()):
    rects = list(mundo.paredes)
    rects += [p["rect"] for p in puertas_dobles if not p["abierta"]]
    rects += [c["rect"] for c in compuertas if c["cerrada"]]
    return rects


def _choque(cajas, c, s):
    """Distancia a la que el rayo (c, s) entra a la primera caja, o infinito.

    Las cajas van relativas al origen del rayo: (x0, y0, x1, y1) con el
    origen en (0, 0). Si el origen queda dentro de una caja, esa se ignora.
    """
    mejor = math.inf
    ic = 1 / c if abs(c) > 1e-9 else None
    is_ = 1 / s if abs(s) > 1e-9 else None
    for x0, y0, x1, y1 in cajas:
        if ic is None:
            if not x0 <= 0 <= x1:
                continue
            entra, sale = -math.inf, math.inf
        else:
            a, b = x0 * ic, x1 * ic
            entra, sale = (a, b) if a < b else (b, a)
        if is_ is None:
            if not y0 <= 0 <= y1:
                continue
        else:
            a, b = y0 * is_, y1 * is_
            if a > b:
                a, b = b, a
            if a > entra:
                entra = a
            if b < sale:
                sale = b
        if 0 < entra <= sale and entra < mejor:
            mejor = entra
    return mejor


def _alcance(dist, s, radio):
    """Dónde termina el rayo: en la pared (metiéndose un poco) o en el radio."""
    if dist >= radio:
        return radio
    return min(radio, dist + ENTRA_EN_PARED + ENTRA_EN_PARED_ARRIBA * max(0.0, -s))


class Campo:
    """Lo que ve un jugador desde `origen`: el polígono y las paredes cercanas.

    `cajas` son las paredes cercanas, relativas al origen (ver _choque).
    """

    def __init__(self, origen, rects, radio=RADIO_VISION):
        self.origen = ox, oy = origen
        self.radio = radio
        self.cajas = []
        angulos = [2 * math.pi * i / RAYOS for i in range(RAYOS)]
        for r in rects:
            # Solo las paredes que pueden estar dentro del radio.
            if (r.right < ox - radio or r.left > ox + radio
                    or r.bottom < oy - radio or r.top > oy + radio):
                continue
            caja = (r.left - ox, r.top - oy, r.right - ox, r.bottom - oy)
            if caja[0] < 0 < caja[2] and caja[1] < 0 < caja[3]:
                continue
            self.cajas.append(caja)
            for ex, ey in ((caja[0], caja[1]), (caja[2], caja[1]),
                           (caja[0], caja[3]), (caja[2], caja[3])):
                if ex * ex + ey * ey > radio * radio:
                    continue
                a = math.atan2(ey, ex)
                angulos += (a - ROCE_ESQUINA, a + ROCE_ESQUINA)
        angulos.sort(key=lambda a: a % (2 * math.pi))

        self.puntos = []
        for a in angulos:
            c, s = math.cos(a), math.sin(a)
            dist = _alcance(_choque(self.cajas, c, s), s, radio)
            self.puntos.append((ox + c * dist, oy + s * dist))

    def ve_punto(self, p):
        """True si p está dentro del radio y sin pared de por medio.

        Es lo mismo que preguntar si cae en el polígono, pero más barato: se
        lanza un solo rayo hacia p.
        """
        dx, dy = p[0] - self.origen[0], p[1] - self.origen[1]
        d = math.hypot(dx, dy)
        if d > self.radio:
            return False
        if d < 1:
            return True
        c, s = dx / d, dy / d
        return d <= _alcance(_choque(self.cajas, c, s), s, self.radio)

    def ve_a(self, rect):
        """True si algo de `rect` (la hitbox de un personaje) se ve.

        Se prueban los pies, el centro y un punto más arriba (donde va la
        cabeza del sprite), para que no desaparezca alguien que asoma por una
        esquina.
        """
        return any(self.ve_punto(p) for p in
                   (rect.center, rect.midbottom, (rect.centerx, rect.top - 40)))


_recientes = {}


def campo_de(origen, rects, radio=RADIO_VISION):
    """Campo desde `origen`, reusando el último si nada cambió.

    Un jugador quieto (escondido, preso, leyendo un panel) no vuelve a lanzar
    sus rayos cada cuadro mientras no se muevan él ni las puertas.
    """
    clave = (tuple(origen), radio, tuple(tuple(r) for r in rects))
    campo = _recientes.get(clave)
    if campo is None:
        if len(_recientes) > 16:
            _recientes.clear()
        campo = _recientes[clave] = Campo(origen, rects, radio)
    return campo

