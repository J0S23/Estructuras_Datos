"""Interpolación en el cliente: que se vea fluido con 30 instantáneas por segundo.

El servidor manda la posición de cada jugador y cada alien 30 veces por
segundo (y por la red pueden llegar a tirones). Si el cliente dibujara
siempre la última, todo avanzaría a saltos de 2 cuadros, más los tirones de
la red. Lo que se hace es dibujar un poquito en el PASADO (RETRASO_MS = 50):
casi siempre hay una instantánea antes y otra después de ese momento, y se
dibuja la mezcla de las dos según cuánto se avanzó entre ellas.

    tiempo del servidor ──●─────────●─────────●────────●──►
                          c=200     c=202     c=204     c=206 (la última)
                                       ▲
                          se dibuja aquí (100 ms antes de la última)

El "tiempo del servidor" sale del número de cuadro (`c`, 60 por segundo):
se estima cuánto le lleva el reloj del cliente al del servidor con la
llegada más rápida que se ha visto (`desfase`), así un mensaje que llega
tarde no mueve la referencia.

Solo se interpolan posiciones y ángulos; lo demás (vidas, paneles, misión)
va con la última instantánea.

El retraso se ADAPTA a la red (nov 21, Diego: "los lagazos por ping alto"):
con wifi, a veces una instantánea llega 30-100 ms tarde (y por TCP las que
vienen detrás también). Con 50 ms fijos, en ese rato no había una "después"
y los aliens y el otro jugador se quedaban quietos y saltaban (con 80 ms de
ping y ~30 de jitter: más de la mitad de los cuadros). Ahora se mide cuánto
más tarde de lo normal llega cada una (`tarde`, sobre el desfase) y el
retraso es lo que hace falta para que casi siempre haya una después:
el espacio entre dos instantáneas + lo que llegan tarde casi siempre
(PERCENTIL de las últimas MUESTRAS) + MARGEN_MS, entre RETRASO_MS y
RETRASO_MAX_MS. Sube rápido (para no congelarse) y baja despacio (que no se
note que el tiempo se acelera). Si igual se queda sin la de después, sigue
la última velocidad hasta EXTRAPOLAR_MS en vez de congelarse.
"""

import math
import time

from cliente_servidor.protocolo import HZ_JUEGO

# 100 ms se sentía pesado jugando (tecla -> se ve moverse ~115 ms en la misma
# laptop, más por wifi). Con 30 instantáneas por segundo (una cada ~33 ms),
# 50 ms todavía deja casi siempre una antes y otra después.
RETRASO_MS = 50
RETRASO_MAX_MS = 220    # más que esto se nota que todo va "en el pasado"
GUARDAR = 30            # instantáneas guardadas (un segundo a 30 por segundo)
MUESTRAS = 90           # cuánto llegaron tarde las últimas (3 s)
PERCENTIL = 0.95
MARGEN_MS = 8
SUBIR_POR_S = 4.0       # qué tan rápido va el retraso hacia el que hace falta (subiendo)
BAJAR_MS_POR_S = 25.0   # y bajando: 25 ms por segundo (el tiempo va ~2.5 % más rápido)
EXTRAPOLAR_MS = 34


def posiciones(secciones):
    """{"j0": (x, y, ángulo de linterna), "a3": (x, y, ángulo), "npreso_4": (x, y, 0)}
    de una instantánea."""
    salida = {}
    i = 0
    while f"j{i}" in secciones:
        j = secciones[f"j{i}"]
        salida[f"j{i}"] = (j["x"], j["y"], j.get("lin", 0.0))
        i += 1
    aliens = secciones.get("al", {})
    for k in range(aliens.get("n", 0)):
        pos = aliens.get(str(k))
        if pos:
            salida[f"a{k}"] = tuple(pos)
    # Los prisioneros que caminan (por su nodo de NEXUS): antes iban con la
    # última instantánea, a saltos de 30 por segundo (y a tirones con wifi).
    for datos in (secciones.get("npc") or {}).get("npcs") or ():
        caja = datos.get("hitbox") if isinstance(datos, dict) else None
        if isinstance(caja, dict) and isinstance(caja.get("R"), list) and len(caja["R"]) == 4:
            x, y, w, h = caja["R"]
            salida[f"n{datos.get('nodo')}"] = (x + w / 2, y + h / 2, 0.0)
    return salida


def _angulo(a, b, t):
    """De a hacia b por el lado más corto (de 179° a -179° son 2°, no 358°)."""
    d = (b - a + math.pi) % (2 * math.pi) - math.pi
    return a + d * t


class Interpolador:
    def __init__(self, retraso_ms=RETRASO_MS, reloj=time.perf_counter, adaptar=True):
        self.retraso = retraso_ms / 1000.0
        self.minimo = retraso_ms / 1000.0
        self.adaptar = adaptar
        self.reloj = reloj
        self.bufer = []          # [(cuadro, posiciones)], de la más vieja a la más nueva
        self.desfase = None      # reloj local - tiempo del servidor (el más chico visto)
        self.tarde = []          # cuánto más tarde que la más rápida llegaron las últimas (s)
        self.necesario = self.retraso
        self._t_ahora = None
        self.secos = 0           # cuadros dibujados sin instantánea "después" (para F3)
        self.dibujados = 0

    def agregar(self, cuadro, secciones, ahora=None):
        ahora = self.reloj() if ahora is None else ahora
        t_servidor = cuadro / HZ_JUEGO
        desfase = ahora - t_servidor
        if self.desfase is None or desfase < self.desfase:
            if self.desfase is not None and self.adaptar:
                # Llegó una más rápida que todas: la referencia baja. Sin más,
                # lo que se dibuja saltaba hacia adelante esa diferencia; así
                # el retraso la absorbe y después baja de a poco.
                self.retraso = min(RETRASO_MAX_MS / 1000.0, self.retraso + self.desfase - desfase)
            self.desfase = desfase
        else:
            # Que se adapte despacio si el reloj del servidor se atrasa de verdad.
            self.desfase += (desfase - self.desfase) * 0.002
        if self.bufer and cuadro <= self.bufer[-1][0]:
            self.bufer = [b for b in self.bufer if b[0] < cuadro]   # (empezó otra partida)
        if self.bufer:
            espacio = (cuadro - self.bufer[-1][0]) / HZ_JUEGO
            self.tarde.append(max(0.0, desfase - self.desfase))
            del self.tarde[:-MUESTRAS]
            orden = sorted(self.tarde)
            casi_siempre = orden[min(len(orden) - 1, int(len(orden) * PERCENTIL))]
            self.necesario = max(self.minimo, min(RETRASO_MAX_MS / 1000.0,
                                                  min(espacio, 0.1) + casi_siempre + MARGEN_MS / 1000.0))
        self.bufer.append((cuadro, posiciones(secciones)))
        del self.bufer[:-GUARDAR]

    def _ajustar(self, ahora):
        """Lleva el retraso de a poco hacia el que hace falta."""
        dt = 0.0 if self._t_ahora is None else max(0.0, min(0.1, ahora - self._t_ahora))
        self._t_ahora = ahora
        if not self.adaptar:
            return
        if self.necesario > self.retraso:
            self.retraso += (self.necesario - self.retraso) * min(1.0, SUBIR_POR_S * dt)
        else:
            self.retraso = max(self.necesario, self.retraso - BAJAR_MS_POR_S / 1000.0 * dt)

    def ahora(self, ahora=None):
        """{clave: (x, y, ángulo)} para dibujar en este momento."""
        if not self.bufer:
            return {}
        ahora = self.reloj() if ahora is None else ahora
        self._ajustar(ahora)
        objetivo = (ahora - self.desfase - self.retraso) * HZ_JUEGO     # en cuadros
        self.dibujados += 1
        if objetivo >= self.bufer[-1][0]:
            self.secos += 1
            return self._extrapolar(objetivo)
        if objetivo <= self.bufer[0][0]:
            return dict(self.bufer[0][1])
        for (ca, pa), (cb, pb) in zip(self.bufer, self.bufer[1:]):
            if ca <= objetivo <= cb:
                t = (objetivo - ca) / max(1, cb - ca)
                salida = {}
                for clave, b in pb.items():
                    a = pa.get(clave)
                    if a is None or abs(a[0] - b[0]) + abs(a[1] - b[1]) > 300:
                        salida[clave] = b        # (apareció o se teletransportó)
                        continue
                    salida[clave] = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                                     _angulo(a[2], b[2], t))
                return salida
        return dict(self.bufer[-1][1])

    def _extrapolar(self, objetivo):
        """Sin la instantánea de después (llegó tarde): cada cosa sigue un poco
        con la velocidad que traía (hasta EXTRAPOLAR_MS) en vez de quedarse
        quieta y saltar cuando llegue."""
        cb, pb = self.bufer[-1]
        if len(self.bufer) < 2:
            return dict(pb)
        ca, pa = self.bufer[-2]
        pasado = min(objetivo - cb, EXTRAPOLAR_MS / 1000.0 * HZ_JUEGO)
        t = pasado / max(1, cb - ca)
        salida = {}
        for clave, b in pb.items():
            a = pa.get(clave)
            if a is None or abs(a[0] - b[0]) + abs(a[1] - b[1]) > 300:
                salida[clave] = b
                continue
            salida[clave] = (b[0] + (b[0] - a[0]) * t, b[1] + (b[1] - a[1]) * t, b[2])
        return salida
