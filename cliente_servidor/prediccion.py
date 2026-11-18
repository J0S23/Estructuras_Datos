"""Predicción en el cliente: tu personaje se mueve en TU pantalla al instante.

Sin esto, en red cada paso hacía el viaje completo: la tecla va al servidor
(por wifi), el servidor la aplica, la manda en la siguiente instantánea y el
cliente además dibuja 50 ms en el pasado (interpolacion.py). En la laptop que
no es la del servidor eso eran 100-250 ms entre tecla y movimiento: "lag"
(nov 17, Diego: en la laptop host se sentía normal y en la otra no).

Ahora el cliente mueve a SUS jugadores él mismo, con la misma cuenta que el
servidor (Personaje._mover_eje, a 60 pasos por segundo, mismas paredes,
puertas y velocidad, la mitad en sigilo), y el servidor sigue mandando: cada
vez que llega una instantánea se compara dónde dice el servidor que estaba
con dónde estaba la predicción en ese momento (hace `respuesta_ms`, lo que
tarda una intención en volver incluida en una instantánea), y la diferencia
se corrige de a poquito en los cuadros que siguen. Si la diferencia es
grande (lo atraparon y apareció en la prisión, salió de un escondite, lo
empujó algo que el cliente no sabe) salta directo a lo del servidor.

Los demás (jugadores de la otra laptop y aliens) siguen interpolados.
"""

import math
import time
from collections import deque

from cliente_servidor.protocolo import HZ_JUEGO

SALTO_PX = 90            # más que esto entre predicción y servidor: se salta directo
SIN_CORREGIR_PX = 0.5    # menos que esto: no se corrige (redondeos)
CORRECCION = 0.18        # fracción de lo que falta corregir que se aplica cada cuadro
PASOS_MAX = 8            # pasos de 60 Hz por cuadro como máximo (si el cliente se traba)
RESPUESTA_INICIAL_MS = 120


class Prediccion:
    """La predicción de UN jugador local."""

    def __init__(self):
        self.pos = None                    # (x, y) de la esquina del sprite (como Personaje.x, .y)
        self.historia = deque(maxlen=180)  # [t, x, y]: dónde estaba la predicción (3 s a 60)
        self.acumulado = 0.0               # pasos de 60 Hz pendientes
        self.pendiente = [0.0, 0.0]        # corrección que falta aplicar
        self.linterna = None
        self.activa = False
        self.ultimo_error = 0.0            # px, la última vez que llegó una instantánea (para F3)
        self.saltos = 0

    def soltar(self):
        """Sin predicción (no se puede mover, presentación abierta...): sigue al servidor."""
        self.pos = None
        self.historia.clear()
        self.acumulado = 0.0
        self.pendiente = [0.0, 0.0]
        self.activa = False

    def puede_moverse(self, j):
        return not (j.ocupado or j.escondido or j.preso or not j.puede_moverse
                    or getattr(j, "eliminado", False) or getattr(j, "minijuego", None) is not None)

    def avanzar(self, juego, j, mantener, dt_s, ahora=None):
        """Mueve al jugador `j` del espejo según lo que tiene presionado
        (`mantener`, las acciones). El espejo ya le puso la posición del
        servidor (interpolada): si la predicción está activa se cambia por la
        predicha."""
        from Movimiento.Personaje import direccion_desde_vector
        from entidades.jugador import FACTOR_VELOCIDAD_SIGILO
        from juego.oscuridad import Linterna
        ahora = time.perf_counter() if ahora is None else ahora
        p = j.personaje
        if not self.puede_moverse(j):
            self.soltar()
            return False
        if self.pos is None:
            self.pos = (p.x, p.y)
            self.linterna = Linterna()
            self.linterna.angulo = j.linterna.angulo
        dx = ("derecha" in mantener) - ("izquierda" in mantener)
        dy = ("abajo" in mantener) - ("arriba" in mantener)
        sigilo = "sigilo" in mantener
        velocidad = getattr(j, "velocidad_base", p.velocidad) * (FACTOR_VELOCIDAD_SIGILO if sigilo else 1.0)
        self.acumulado = min(self.acumulado + dt_s * HZ_JUEGO, PASOS_MAX)
        p.x, p.y = self.pos
        p.sync_hitbox_from_sprite()
        colisiona = juego._colisiona_para(j)
        while self.acumulado >= 1:
            self.acumulado -= 1
            if dx or dy:
                # (lo mismo que Personaje.actualizar: un eje a la vez, en diagonal
                # 0.7071 para que no sea más rápido)
                factor = 0.7071 if dx and dy else 1.0
                p._mover_eje(dx * velocidad * factor, 0, colisiona)
                p._mover_eje(0, dy * velocidad * factor, colisiona)
                p.direccion = direccion_desde_vector(dx, dy, p.direccion)
                self.linterna.actualizar(p.direccion)
        # La corrección que dejó la última instantánea, de a poquito (y la
        # historia se corre igual: así no se cuenta dos veces).
        cx, cy = self.pendiente[0] * CORRECCION, self.pendiente[1] * CORRECCION
        if cx or cy:
            p.x += cx
            p.y += cy
            self.pendiente[0] -= cx
            self.pendiente[1] -= cy
            for h in self.historia:
                h[1] += cx
                h[2] += cy
        p.sync_hitbox_from_sprite()
        self.pos = (p.x, p.y)
        self.historia.append([ahora, p.x, p.y])
        # La animación y hacia dónde mira, con la tecla de aquí (si no, al soltar
        # la tecla seguía "caminando" lo que tarda en llegar la instantánea).
        movimiento = bool(dx or dy)
        if movimiento != p.moviendose:
            p.moviendose = movimiento
            nuevo = "walking" if movimiento else (
                "breathing" if p.animaciones.get("breathing", {}).get(p.direccion) else "idle")
            if nuevo != p.estado:
                p.estado, p.frame_actual, p.contador_animacion = nuevo, 0, 0
        j.sigilo = sigilo
        j.linterna.angulo = self.linterna.angulo
        self.activa = True
        return True

    def instantanea(self, x, y, respuesta_ms, ahora=None):
        """Llegó una instantánea: el servidor dice que `j` estaba en (x, y). Esa
        posición es la de hace ~`respuesta_ms` en la historia de la predicción."""
        if self.pos is None or not self.historia:
            return
        ahora = time.perf_counter() if ahora is None else ahora
        respuesta = (respuesta_ms if respuesta_ms is not None else RESPUESTA_INICIAL_MS) / 1000.0
        hx, hy = _en(self.historia, ahora - respuesta)
        ex, ey = x - hx, y - hy
        error = math.hypot(ex, ey)
        self.ultimo_error = error
        if error > SALTO_PX:
            # Muy distinto: lo movió el servidor (prisión, escondite, rescate...).
            self.saltos += 1
            self.pos = (x, y)
            self.historia.clear()
            self.pendiente = [0.0, 0.0]
            return
        self.pendiente = [ex, ey] if error >= SIN_CORREGIR_PX else [0.0, 0.0]


def _en(historia, t):
    """(x, y) de la historia en el momento `t` (interpolando entre dos)."""
    if t <= historia[0][0]:
        return historia[0][1], historia[0][2]
    if t >= historia[-1][0]:
        return historia[-1][1], historia[-1][2]
    for a, b in zip(historia, list(historia)[1:]):
        if a[0] <= t <= b[0]:
            k = (t - a[0]) / max(1e-9, b[0] - a[0])
            return a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k
    return historia[-1][1], historia[-1][2]
