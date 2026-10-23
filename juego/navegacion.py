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

import heapq
from collections import deque

import pygame


PASO = 16
MAX_NODOS = 40000        # tope del BFS, por si el destino no se alcanza
PESO_ESTIMADO = 1.6      # A* "con prisa": revisa muchas menos celdas y el camino
                         # sale casi igual (después se estira en línea recta)


class Navegacion:
    cuadro = 0                # lo sube el juego en cada cuadro (siguiente_cuadro)
    ultimo_cuadro = -1        # en qué cuadro se calculó el último camino nuevo
    ocupada = False
    def __init__(self, mundo, ancho, alto, paso=PASO):
        self.mundo = mundo
        self.ancho, self.alto, self.paso = ancho, alto, paso
        self._guardados = {}
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

    def _componentes(self):
        """A qué pedazo conectado del mapa fijo pertenece cada celda (se arma
        una vez). Sirve para saber al instante que dos puntos no se conectan
        sin recorrer todo el mapa buscando."""
        if getattr(self, "_comp", None) is None:
            p = self.paso
            vecinos = ((p, 0), (-p, 0), (0, p), (0, -p))
            self._comp, self._celdas_comp = {}, []
            for celda in self.libre:
                if celda in self._comp:
                    continue
                n = len(self._celdas_comp)
                grupo = [celda]
                self._comp[celda] = n
                cola = deque([celda])
                while cola:
                    c = cola.popleft()
                    for dx, dy in vecinos:
                        v = (c[0] + dx, c[1] + dy)
                        if v in self.libre and v not in self._comp:
                            self._comp[v] = n
                            grupo.append(v)
                            cola.append(v)
                self._celdas_comp.append(grupo)
        return self._comp

    def _vecinos(self):
        """Lista de adyacencia del grafo de la nave (se arma una vez): para
        cada celda libre, sus vecinas libres en 8 direcciones con lo que cuesta
        ir (1 o 1.41) y, en diagonal, las dos celdas de la esquina que tienen
        que estar libres para no cortarla."""
        if getattr(self, "_ady", None) is None:
            p, libre = self.paso, self.libre
            self._ady = {}
            for c in libre:
                lista = []
                for dx, dy in ((p, 0), (-p, 0), (0, p), (0, -p), (p, p), (p, -p), (-p, p), (-p, -p)):
                    v = (c[0] + dx, c[1] + dy)
                    if v not in libre:
                        continue
                    if dx and dy:
                        a, b = (c[0] + dx, c[1]), (c[0], c[1] + dy)
                        if a not in libre or b not in libre:
                            continue
                        lista.append((v, 1.4142, (a, b)))
                    else:
                        lista.append((v, 1.0, None))
                self._ady[c] = lista
        return self._ady

    def _tapadas(self, extra):
        """Celdas libres del mapa fijo que tapa lo que cambia (puerta, sellos)."""
        tapadas = set()
        p, w, h = self.paso, self.ancho, self.alto
        for r in extra:
            x0 = (r.left - w) // p * p
            y0 = (r.top - h) // p * p
            for x in range(x0, r.right + p, p):
                for y in range(y0, r.bottom + p, p):
                    if (x, y) in self.libre and pygame.Rect(x, y, w, h).colliderect(r):
                        tapadas.add((x, y))
        return tapadas

    def camino(self, desde, hasta, parcial=False, puede_esperar=False):
        """Lista de puntos (centros) de `desde` a `hasta`, o None si no hay.

        Con `parcial=True`, si no se puede llegar (por ejemplo, el ruido está
        al otro lado de la puerta cerrada de la prisión), devuelve el camino
        hasta la celda alcanzable más cercana al destino: el alien va lo más
        cerca que puede, como haría alguien que oye algo detrás de una puerta.
        En ese caso el último punto NO es `hasta` (ver `self.ultimo_parcial`).

        Busca con A* (un BFS que primero prueba las celdas que van hacia la
        meta): encuentra el mismo tipo de camino que el BFS de antes pero
        revisando muchas menos celdas, así no da tirones cuando varios
        prisioneros y aliens piden camino a la vez.
        """
        self.ultimo_parcial = False
        extra = self._bloqueos_extra()
        # Los prisioneros van y vienen entre los mismos puntos: el mismo camino
        # se pide muchas veces. Se guarda (mientras no cambie lo que tapa).
        clave = (self._celda_de(desde), self._celda_de(hasta), int(hasta[0]), int(hasta[1]),
                 parcial, tuple(tuple(r) for r in extra))
        guardado = self._guardados.get(clave)
        if guardado is not None:
            self.ultimo_parcial = guardado[1]
            return list(guardado[0]) if guardado[0] is not None else None
        # Los prisioneros no tienen prisa: si en este mismo cuadro ya se
        # calculó otro camino nuevo, esperan su turno (None, con `ocupada`) y
        # lo piden después. Así varios caminos largos no caen en el mismo
        # cuadro (tirón).
        self.ocupada = False
        if puede_esperar and Navegacion.ultimo_cuadro == Navegacion.cuadro:
            self.ocupada = True
            return None
        resultado = self._camino(desde, hasta, parcial, extra)
        Navegacion.ultimo_cuadro = Navegacion.cuadro
        if len(self._guardados) > 2000:
            self._guardados.clear()
        self._guardados[clave] = (resultado, self.ultimo_parcial)
        return list(resultado) if resultado is not None else None

    def _camino(self, desde, hasta, parcial, extra):
        tapadas = self._tapadas(extra)
        libre = self.libre
        w, h = self.ancho, self.alto

        def ok(c):
            return c in libre and c not in tapadas

        inicio = self._mas_cercana(desde, ok)
        meta = self._mas_cercana(hasta, ok)
        if inicio is None or meta is None:
            return None
        comp = self._componentes()
        if comp.get(inicio) != comp.get(meta):
            # En el mapa fijo ni siquiera se conectan: lo más cerca posible.
            if not parcial:
                return None
            grupo = [c for c in self._celdas_comp[comp[inicio]] if c not in tapadas]
            meta = min(grupo, key=lambda c: (c[0] + w / 2 - hasta[0]) ** 2 + (c[1] + h / 2 - hasta[1]) ** 2)
            hasta = None
        mx, my = meta
        p = self.paso
        diag = 1.4142

        def estimado(c):
            dx, dy = abs(c[0] - mx) / p, abs(c[1] - my) / p
            return (dx + dy) + (diag - 2) * (dx if dx < dy else dy)

        vecinos = self._vecinos()
        previo = {inicio: None}
        costo = {inicio: 0.0}
        abiertos = [(estimado(inicio), 0, inicio)]
        orden = 0
        heappop, heappush = heapq.heappop, heapq.heappush
        while abiertos and len(previo) < MAX_NODOS:
            _, _, c = heappop(abiertos)
            if c == meta:
                break
            base = costo[c]
            for v, paso, esquinas in vecinos[c]:
                if v in tapadas or (esquinas and (esquinas[0] in tapadas or esquinas[1] in tapadas)):
                    continue
                nuevo = base + paso
                if nuevo < costo.get(v, 1e18):
                    costo[v] = nuevo
                    previo[v] = c
                    orden += 1
                    heappush(abiertos, (nuevo + PESO_ESTIMADO * estimado(v), orden, v))
        llego = meta in previo and hasta is not None
        if meta not in previo or hasta is None:
            if not parcial or len(previo) <= 1:
                return None
            objetivo = hasta if hasta is not None else (mx + w / 2, my + h / 2)
            if meta not in previo:
                meta = min(previo, key=lambda c: (c[0] + w / 2 - objetivo[0]) ** 2
                           + (c[1] + h / 2 - objetivo[1]) ** 2)
            self.ultimo_parcial = True
        celdas = []
        c = meta
        while c is not None:
            celdas.append(c)
            c = previo[c]
        celdas.reverse()
        puntos = [(cx + w // 2, cy + h // 2) for cx, cy in celdas]
        if llego:
            puntos.append((int(hasta[0]), int(hasta[1])))
        return self.estirar(puntos)

    def libre_entre(self, a, b):
        """¿El alien entero cabe por la línea recta de `a` a `b`?"""
        choca = getattr(self.mundo, "colisiona_alien", self.mundo.colisiona)
        # Un poco más ancho que el alien: así no roza esquinas al doblar.
        return self.mundo.linea_libre(a, b, self.ancho + 4, self.alto + 4, paso=8, colisiona=choca)

    def estirar(self, puntos):
        """Quita los puntos intermedios que se pueden saltar en línea recta.
        Desde cada punto avanza mientras el siguiente se vea en línea recta
        (antes probaba desde el final hacia atrás: muchas más líneas)."""
        if len(puntos) <= 2:
            return puntos
        resultado = [puntos[0]]
        i = 0
        n = len(puntos)
        while i < n - 1:
            j = i + 1
            while j + 1 < n and self.libre_entre(puntos[i], puntos[j + 1]):
                j += 1
            resultado.append(puntos[j])
            i = j
        return resultado[1:]


def siguiente_cuadro():
    """Lo llama el juego una vez por cuadro (para repartir los caminos nuevos)."""
    Navegacion.cuadro += 1


def de_mundo(mundo, ancho, alto):
    """Una navegación por mundo y tamaño de alien (se arma la primera vez)."""
    cache = mundo.__dict__.setdefault("_navegaciones", {})
    clave = (ancho, alto)
    if clave not in cache:
        cache[clave] = Navegacion(mundo, ancho, alto)
    return cache[clave]
