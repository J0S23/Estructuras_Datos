"""Navegación de los aliens: caminos que rodean las paredes.

Antes, cuando un alien iba a revisar un ruido (la alarma del código malo, una
señal de la Resonante, un señuelo...) caminaba en línea recta hacia el punto, y
si había una pared en medio se quedaba mirándola. Ahora:

1. Si hay línea libre (con el ancho del alien) va directo.
2. Si no, busca un camino con **BFS** sobre una cuadrícula del mapa: cada
   celda es un lugar donde cabe el alien, vecinas en 8 direcciones. Es el mismo
   recorrido por niveles que se usa para dibujar los árboles, pero sobre un
   grafo implícito (las celdas son los nodos; las celdas vecinas libres, las
   aristas).
3. El camino se "estira": se salta los puntos intermedios a los que ya se
   puede llegar en línea recta, para que no camine en zigzag.

Lo que cambia durante la partida (la puerta de la prisión, los sellos del
Forjador) no está en la cuadrícula fija: se revisa al buscar cada camino.
"""

from collections import deque

import pygame


PASO = 16
MAX_NODOS = 40000        # tope del BFS, por si el destino no se alcanza


class Navegacion:
    def __init__(self, mundo, ancho, alto, paso=PASO):
        self.mundo = mundo
        self.ancho, self.alto, self.paso = ancho, alto, paso
        base = mundo.paredes_base
        self.libre = set()
        for x in range(0, mundo.ancho - ancho, paso):
            for y in range(0, mundo.alto - alto, paso):
                if pygame.Rect(x, y, ancho, alto).collidelist(base) == -1:
                    self.libre.add((x, y))

    # -- Lo que cambia en la partida -------------------------------------------------

    def _bloqueos_extra(self):
        mundo = self.mundo
        extra = [p for p in mundo.paredes if p not in mundo.paredes_base]
        extra += list(getattr(mundo, "bloqueos_alien", []))
        return extra

    def _celda_de(self, punto):
        x = int(punto[0] - self.ancho / 2) // self.paso * self.paso
        y = int(punto[1] - self.alto / 2) // self.paso * self.paso
        return x, y

    def _mas_cercana(self, punto, ok):
        """La celda libre más cercana a `punto` (busca en un radio chico)."""
        cx, cy = self._celda_de(punto)
        mejor, mejor_d = None, None
        for r in range(0, 6):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    c = (cx + dx * self.paso, cy + dy * self.paso)
                    if ok(c):
                        d = (c[0] + self.ancho / 2 - punto[0]) ** 2 + (c[1] + self.alto / 2 - punto[1]) ** 2
                        if mejor is None or d < mejor_d:
                            mejor, mejor_d = c, d
            if mejor is not None:
                return mejor
        return None

    # -- Buscar un camino --------------------------------------------------------------

    def camino(self, desde, hasta):
        """Lista de puntos (centros) de `desde` a `hasta`, o None si no hay."""
        extra = self._bloqueos_extra()
        w, h = self.ancho, self.alto

        def ok(c):
            if c not in self.libre:
                return False
            return not extra or pygame.Rect(c[0], c[1], w, h).collidelist(extra) == -1

        inicio = self._mas_cercana(desde, ok)
        meta = self._mas_cercana(hasta, ok)
        if inicio is None or meta is None:
            return None
        previo = {inicio: None}
        cola = deque([inicio])
        p = self.paso
        vecinos = ((p, 0), (-p, 0), (0, p), (0, -p), (p, p), (p, -p), (-p, p), (-p, -p))
        while cola and len(previo) < MAX_NODOS:
            c = cola.popleft()
            if c == meta:
                break
            for dx, dy in vecinos:
                v = (c[0] + dx, c[1] + dy)
                if v in previo or not ok(v):
                    continue
                # En diagonal, que no corte una esquina.
                if dx and dy and (not ok((c[0] + dx, c[1])) or not ok((c[0], c[1] + dy))):
                    continue
                previo[v] = c
                cola.append(v)
        if meta not in previo:
            return None
        celdas = []
        c = meta
        while c is not None:
            celdas.append(c)
            c = previo[c]
        celdas.reverse()
        puntos = [(cx + w // 2, cy + h // 2) for cx, cy in celdas]
        puntos.append((int(hasta[0]), int(hasta[1])))
        return self.estirar(puntos)

    def libre_entre(self, a, b):
        """¿El alien entero cabe por la línea recta de `a` a `b`?"""
        choca = getattr(self.mundo, "colisiona_alien", self.mundo.colisiona)
        # Un poco más ancho que el alien: así no roza esquinas al doblar.
        return self.mundo.linea_libre(a, b, self.ancho + 4, self.alto + 4, paso=8, colisiona=choca)

    def estirar(self, puntos):
        """Quita los puntos intermedios que se pueden saltar en línea recta."""
        if len(puntos) <= 2:
            return puntos
        resultado = [puntos[0]]
        i = 0
        while i < len(puntos) - 1:
            j = len(puntos) - 1
            while j > i + 1 and not self.libre_entre(puntos[i], puntos[j]):
                j -= 1
            resultado.append(puntos[j])
            i = j
        return resultado[1:]


def de_mundo(mundo, ancho, alto):
    """Una navegación por mundo y tamaño de alien (se arma la primera vez)."""
    cache = mundo.__dict__.setdefault("_navegaciones", {})
    clave = (ancho, alto)
    if clave not in cache:
        cache[clave] = Navegacion(mundo, ancho, alto)
    return cache[clave]
