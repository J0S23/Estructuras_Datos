"""Minijuegos de las tareas (juego/tareas.py): en vez de mantener la tecla,
cada tarea tiene su minijuego, que se juega en la vista de quien lo hace.

- **Cables** (reparar la cápsula, paneles, la puerta del pasillo): girar las
  piezas de una cuadrícula hasta que la corriente pase de la izquierda a la
  derecha.
- **Interruptores** (caja de fusibles): subir todas las palancas; cada una
  mueve también las de los lados.
- **Señal** (consolas de navegación, terminales): igualar la onda (frecuencia
  y amplitud) con la objetivo y "inyectar".
- **Abono** (la planta de la Biosfera): el saco se mece sobre la maceta;
  soltar el abono justo encima.
- **Ganzúa** (candados y cerraduras): subir los pines uno por uno justo a la
  línea.

Cada uno recibe acciones ("arriba", "abajo", "izquierda", "derecha", "ok"),
se actualiza con `dt` y se dibuja con `dibujar(screen, vista, jugador)`.
`listo` es True cuando se ganó (y ya se vio el "¡Listo!"). `facil` es para
el rol que sabe hacerlo (el Forjador con los cables, etc.): más corto.

Mientras se juega, el jugador no se mueve (es un panel, "tarea"): si un
alien llega, lo atrapa.
"""

import math
import random

import pygame

from juego.fuentes import fuente_de_tamano

N, E, S, O = 1, 2, 4, 8
DIRECCIONES = {N: (0, -1), E: (1, 0), S: (0, 1), O: (-1, 0)}
OPUESTA = {N: S, S: N, E: O, O: E}

COLOR_TEXTO = (240, 242, 252)
COLOR_TENUE = (160, 168, 206)
COLOR_BIEN = (110, 230, 150)
COLOR_MAL = (245, 110, 100)
COLOR_CURSOR = (255, 214, 64)
FIN_MS = 750          # cuánto se ve el "¡Listo!" antes de cerrar


def girar(mascara, veces=1):
    """La pieza girada 90° a la derecha `veces` veces (N->E->S->O)."""
    for _ in range(veces % 4):
        mascara = ((mascara << 1) | (mascara >> 3)) & 15
    return mascara


class Minijuego:
    titulo = ""
    color = (120, 200, 255)

    def __init__(self, facil=False, rng=None):
        self.facil = facil
        self.rng = rng or random.Random()
        self.estado = "jugando"        # "jugando" o "ganado"
        self.fin_ms = 0
        self.error_ms = 0
        self.t = 0

    @property
    def ganado(self):
        return self.estado == "ganado"

    @property
    def listo(self):
        return self.ganado and self.fin_ms >= FIN_MS

    def tecla(self, accion):
        """Una acción del jugador. Devuelve el sonido que va ("menu_mover",
        "acierto", "fallo"...) o None."""
        if self.ganado:
            return None
        return self._tecla(accion)

    def _tecla(self, accion):
        return None

    def actualizar(self, dt):
        self.t += dt
        self.error_ms = max(0, self.error_ms - dt)
        if self.ganado:
            self.fin_ms += dt
        else:
            self._actualizar(dt)

    def _actualizar(self, dt):
        pass

    def _ganar(self):
        self.estado = "ganado"
        self.fin_ms = 0

    def _fallar(self):
        self.error_ms = 280

    # -- Dibujo -----------------------------------------------------------------------

    def ayuda(self, jugador):
        """La línea de teclas de abajo."""
        return ""

    def dibujar(self, screen, vista, jugador):
        from screens import vidrio, estilo
        ancho = max(260, min(vista.width - 40, 560))
        alto = max(220, min(vista.height - 190, 400))
        caja = pygame.Rect(0, 0, ancho, alto)
        caja.center = (vista.centerx, vista.centery - 10)
        color = COLOR_MAL if self.error_ms > 0 else (COLOR_BIEN if self.ganado else self.color)
        vidrio.brillo(screen, caja.center, max(caja.w, caja.h) * 0.55, tuple(c // 8 for c in color))
        vidrio.caja(screen, caja, color, 244, 14)
        e = max(0.75, min(1.3, ancho / 520))
        f_titulo = fuente_de_tamano(int(19 * e))
        f = fuente_de_tamano(int(15 * e))
        titulo = f_titulo.render(self.titulo, True, self.color)
        screen.blit(titulo, (caja.x + 16, caja.y + 12))
        extra = self.contador()
        if extra:
            img = f.render(extra, True, COLOR_TENUE)
            screen.blit(img, img.get_rect(topright=(caja.right - 16, caja.y + 14)))
        contenido = pygame.Rect(caja.x + 16, caja.y + 18 + titulo.get_height(),
                                caja.w - 32, caja.h - 18 - titulo.get_height() - 44)
        if self.error_ms > 0:
            # Falló: todo tiembla un poquito.
            contenido.x += int(math.sin(self.t / 16) * 4 * self.error_ms / 280)
        recorte = screen.get_clip()
        screen.set_clip(contenido.inflate(16, 16).clip(caja).clip(recorte))
        self._dibujar(screen, contenido, f)
        screen.set_clip(recorte)
        estilo.pie(screen, self.ayuda(jugador), caja.bottom - 22, fuente_de_tamano(int(13 * e)),
                   COLOR_TENUE, x=caja.centerx)
        if self.ganado:
            k = min(1.0, self.fin_ms / 250)
            # Una pastilla oscura detrás, para que se lea encima del dibujo.
            fondo = pygame.Rect(0, 0, int(min(contenido.w, 260 * e) * (0.6 + 0.4 * k)), int(64 * e))
            fondo.center = (caja.centerx, contenido.centery)
            vidrio.caja(screen, fondo, COLOR_BIEN, 235, 14)
            estilo.titulo(screen, "¡Listo!", (caja.centerx, contenido.centery), int(34 * e * (0.7 + 0.3 * k)),
                          COLOR_BIEN, COLOR_BIEN, adorno=False)

    def contador(self):
        return ""

    def _dibujar(self, screen, rect, f):
        pass


# =====================================================================================
# Dibujo: piezas que comparten los minijuegos (guardadas ya armadas)
# =====================================================================================

_guardados = {}


def _guardado(clave, armar):
    img = _guardados.get(clave)
    if img is None:
        if len(_guardados) > 160:
            _guardados.clear()
        img = _guardados[clave] = armar()
    return img


def _suave(k):
    """0 a 1 que frena al final (para las animaciones)."""
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


def _mezcla(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _placa(w, h, arriba, abajo, radio=8, borde=None, tornillos=False):
    """Una placa con degradado de arriba a abajo, el canto de arriba claro y,
    si se pide, cuatro tornillos en las esquinas (guardada por todo)."""
    def armar():
        img = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            pygame.draw.line(img, _mezcla(arriba, abajo, y / max(1, h - 1)), (0, y), (w, y))
        mascara = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mascara, (255, 255, 255, 255), (0, 0, w, h), border_radius=radio)
        img.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        claro = _mezcla(arriba, (255, 255, 255), 0.25)
        pygame.draw.line(img, claro, (radio, 1), (w - radio, 1))
        pygame.draw.rect(img, borde or _mezcla(abajo, (0, 0, 0), 0.5), (0, 0, w, h), 1, border_radius=radio)
        if tornillos and w > 40 and h > 40:
            m = max(6, min(11, min(w, h) // 9))
            for x, y in ((m, m), (w - m, m), (m, h - m), (w - m, h - m)):
                _tornillo(img, (x, y), max(2, min(4, m // 2)))
        return img
    return _guardado(("placa", w, h, arriba, abajo, radio, borde, tornillos), armar)


def _tornillo(screen, c, r):
    pygame.draw.circle(screen, (16, 16, 22), (c[0] + 1, c[1] + 1), r)
    pygame.draw.circle(screen, (150, 156, 172), c, r)
    pygame.draw.circle(screen, (200, 206, 222), (c[0] - r // 3, c[1] - r // 3), max(1, r // 3))
    pygame.draw.line(screen, (60, 64, 78), (c[0] - r + 1, c[1] + r - 1), (c[0] + r - 1, c[1] - r + 1), 1)


def _tubo(screen, puntos, ancho, cuerpo, borde, brillo):
    """Un cable grueso: borde oscuro, la goma y un reflejo arriba a la izquierda
    (con círculos en cada punto para que las uniones queden redondas)."""
    if len(puntos) < 2:
        return
    a = ancho + 4
    pygame.draw.lines(screen, borde, False, puntos, a)
    for p in puntos:
        pygame.draw.circle(screen, borde, (int(p[0]), int(p[1])), a // 2)
    pygame.draw.lines(screen, cuerpo, False, puntos, ancho)
    for p in puntos:
        pygame.draw.circle(screen, cuerpo, (int(p[0]), int(p[1])), ancho // 2)
    d = max(1, ancho // 4)
    reflejo = [(p[0] - d, p[1] - d) for p in puntos]
    pygame.draw.lines(screen, brillo, False, reflejo, max(1, ancho // 4))


def _rayo(screen, c, tam, color):
    """El dibujo de un rayo (corriente)."""
    x, y = c
    puntos = [(x + tam * 0.15, y - tam), (x - tam * 0.45, y + tam * 0.1), (x - tam * 0.02, y + tam * 0.1),
              (x - tam * 0.2, y + tam), (x + tam * 0.45, y - tam * 0.15), (x + tam * 0.02, y - tam * 0.15)]
    pygame.draw.polygon(screen, color, puntos)


def _chispas(screen, c, semilla, k, largo, color=(255, 230, 140)):
    """Chispas que saltan de `c` (k de 0 a 1: cuánto llevan)."""
    if k >= 1:
        return
    azar = random.Random(semilla)
    for _ in range(7):
        a = azar.uniform(0, math.tau)
        v = azar.uniform(0.5, 1.0) * largo
        x = c[0] + math.cos(a) * v * k
        y = c[1] + math.sin(a) * v * k + largo * 0.6 * k * k
        cola = (c[0] + math.cos(a) * v * max(0.0, k - 0.18), c[1] + math.sin(a) * v * max(0.0, k - 0.18))
        pygame.draw.line(screen, _mezcla(color, (255, 120, 40), k), cola, (x, y), 2)


def brillo(screen, centro, radio, color):
    from screens.vidrio import brillo as _brillo
    _brillo(screen, centro, radio, color)


def _teclas(jugador, *acciones):
    return "".join(jugador.nombre_tecla(a) for a in acciones)


def _mover4(jugador):
    if getattr(jugador, "con_mando", False):
        return "Cruceta"
    nombre = jugador.pista_mover()
    if nombre == "Flechas":
        return "Flechas"
    return _teclas(jugador, "arriba", "izquierda", "abajo", "derecha")


def _mover2(jugador, a="izquierda", b="derecha"):
    if getattr(jugador, "con_mando", False):
        return "Cruceta"
    if jugador.pista_mover() == "Flechas":
        return "Flechas"
    return f"{jugador.nombre_tecla(a)}/{jugador.nombre_tecla(b)}"


def _salir(jugador):
    return f"[{jugador.nombre_tecla('habilidades')}] salir"


# =====================================================================================
# Cables: girar piezas hasta conectar la corriente
# =====================================================================================

class Cables(Minijuego):
    titulo = "Conecta los cables"
    color = (255, 170, 70)

    def __init__(self, facil=False, rng=None, titulo=None):
        super().__init__(facil, rng)
        if titulo:
            self.titulo = titulo
        self.cols, self.filas = (4, 3) if facil else (5, 4)
        self._giros = {}            # pieza -> cuándo se giró (para animar el giro)
        self._armar()

    def _armar(self):
        r = self.rng
        cols, filas = self.cols, self.filas
        # Un camino de la izquierda (fila de entrada) a la derecha: avanza a
        # la derecha y, en cada columna, sube o baja un poco.
        fila = r.randrange(filas)
        self.entrada = fila
        camino = []
        visitadas = set()
        x, y = 0, fila
        entra = O
        for col in range(cols):
            x = col
            pasos_vert = r.choice((0, 0, 1, 2)) if col < cols - 1 else r.choice((0, 1))
            direccion = r.choice((-1, 1))
            celdas = [(x, y)]
            for _ in range(pasos_vert):
                ny = y + direccion
                if 0 <= ny < filas and (x, ny) not in visitadas:
                    y = ny
                    celdas.append((x, y))
                else:
                    break
            for i, (cx, cy) in enumerate(celdas):
                visitadas.add((cx, cy))
                if i + 1 < len(celdas):
                    sale = S if celdas[i + 1][1] > cy else N
                else:
                    sale = E
                camino.append(((cx, cy), entra, sale))
                entra = OPUESTA[sale]
        self.salida = y
        self.base = {}
        for (c, entra, sale) in camino:
            self.base[c] = entra | sale
        for x in range(cols):
            for y in range(filas):
                if (x, y) not in self.base:
                    self.base[(x, y)] = r.choice((N | S, N | E, N | E, N | S))
        # Todas giradas al azar, y que no empiece resuelto.
        self.rot = {c: r.randrange(4) for c in self.base}
        while self._conectado():
            c = r.choice(list(self.base))
            self.rot[c] = (self.rot[c] + 1) % 4
        self.cursor = [0, self.entrada]
        self.encendidas = self._flujo()

    def mascara(self, c):
        return girar(self.base[c], self.rot[c])

    def _flujo(self):
        """Las piezas por donde pasa la corriente (desde la entrada)."""
        inicio = (0, self.entrada)
        if not self.mascara(inicio) & O:
            return set()
        vistas = {inicio}
        pila = [inicio]
        while pila:
            c = pila.pop()
            m = self.mascara(c)
            for d, (dx, dy) in DIRECCIONES.items():
                if not m & d:
                    continue
                v = (c[0] + dx, c[1] + dy)
                if v in self.base and v not in vistas and self.mascara(v) & OPUESTA[d]:
                    vistas.add(v)
                    pila.append(v)
        return vistas

    def _conectado(self):
        fin = (self.cols - 1, self.salida)
        return fin in self._flujo() and bool(self.mascara(fin) & E)

    def _tecla(self, accion):
        dx, dy = {"izquierda": (-1, 0), "derecha": (1, 0), "arriba": (0, -1), "abajo": (0, 1)}.get(accion, (0, 0))
        if dx or dy:
            self.cursor[0] = max(0, min(self.cols - 1, self.cursor[0] + dx))
            self.cursor[1] = max(0, min(self.filas - 1, self.cursor[1] + dy))
            return "menu_mover"
        if accion == "ok":
            c = tuple(self.cursor)
            self.rot[c] = (self.rot[c] + 1) % 4
            self._giros[c] = self.t
            self.encendidas = self._flujo()
            if self._conectado():
                self._ganar()
                return "acierto"
            return "girar"
        return None

    def ayuda(self, jugador):
        return f"[{_mover4(jugador)}] mover   [{jugador.nombre_tecla('interactuar')}] girar   {_salir(jugador)}"

    def _distancias(self):
        """Saltos desde la entrada de cada pieza con corriente (para que los
        pulsos de luz avancen en el sentido de la corriente)."""
        inicio = (0, self.entrada)
        if inicio not in self.encendidas:
            return {}
        dist = {inicio: 0}
        cola = [inicio]
        while cola:
            c = cola.pop(0)
            m = self.mascara(c)
            for d, (dx, dy) in DIRECCIONES.items():
                v = (c[0] + dx, c[1] + dy)
                if m & d and v in self.encendidas and v not in dist and self.mascara(v) & OPUESTA[d]:
                    dist[v] = dist[c] + 1
                    cola.append(v)
        return dist

    def _camino_pieza(self, c, centro, lado, dist):
        """Los puntos del cable de una pieza (recto o en curva), del lado por
        donde entra la corriente al lado por donde sale."""
        m = self.mascara(c)
        lados = [d for d in (N, E, S, O) if m & d]
        if len(lados) != 2:
            return [], lados
        a, b = lados
        # Primero el lado por donde le llega la corriente.
        def entra_por(d):
            if c == (0, self.entrada) and d == O:
                return True
            dx, dy = DIRECCIONES[d]
            v = (c[0] + dx, c[1] + dy)
            return v in dist and c in dist and dist[v] == dist[c] - 1 and bool(self.mascara(v) & OPUESTA[d])
        if entra_por(b):
            a, b = b, a
        cx, cy = centro
        h = lado / 2
        pa = (cx + DIRECCIONES[a][0] * h, cy + DIRECCIONES[a][1] * h)
        pb = (cx + DIRECCIONES[b][0] * h, cy + DIRECCIONES[b][1] * h)
        if OPUESTA[a] == b:
            return [pa, ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2), pb], (a, b)
        # Curva: un cuarto de círculo con centro en la esquina entre los dos lados.
        kx = cx + (DIRECCIONES[a][0] + DIRECCIONES[b][0]) * h
        ky = cy + (DIRECCIONES[a][1] + DIRECCIONES[b][1]) * h
        ang_a = math.atan2(pa[1] - ky, pa[0] - kx)
        ang_b = math.atan2(pb[1] - ky, pb[0] - kx)
        diff = (ang_b - ang_a + math.pi) % math.tau - math.pi
        return [(kx + math.cos(ang_a + diff * i / 10) * h, ky + math.sin(ang_a + diff * i / 10) * h)
                for i in range(11)], (a, b)

    @staticmethod
    def _en_camino(puntos, u):
        """El punto a la fracción `u` del largo del camino."""
        largos = [math.dist(p, q) for p, q in zip(puntos, puntos[1:])]
        total = sum(largos) or 1
        falta = u * total
        for (p, q), l in zip(zip(puntos, puntos[1:]), largos):
            if falta <= l:
                k = falta / l if l else 0
                return (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)
            falta -= l
        return puntos[-1]

    def _dibujar(self, screen, rect, f):
        lado = int(min(rect.w / (self.cols + 2.1), (rect.h - 18) / self.filas))
        ox = rect.centerx - lado * self.cols // 2
        oy = rect.centery - lado * self.filas // 2
        grosor = max(5, lado // 6)
        dist = self._distancias()
        fase = (self.t / 520) % 1.0
        todo = self.ganado
        # El fondo: la tapa abierta del tablero, con su cuadrícula.
        tablero = pygame.Rect(ox - 8, oy - 8, lado * self.cols + 16, lado * self.filas + 16)
        screen.blit(_placa(tablero.w, tablero.h, (36, 40, 56), (20, 22, 32), 12, (70, 78, 108)), tablero)
        for (x, y) in self.base:
            celda = pygame.Rect(ox + x * lado + 3, oy + y * lado + 3, lado - 6, lado - 6)
            on = (x, y) in self.encendidas or todo
            arriba, abajo = ((70, 52, 38), (40, 30, 24)) if on else ((48, 52, 72), (28, 30, 44))
            screen.blit(_placa(celda.w, celda.h, arriba, abajo, 7, None, lado >= 56), celda)
        # La fuente de la corriente (izquierda) y el bombillo (derecha).
        yin = oy + self.entrada * lado + lado // 2
        yout = oy + self.salida * lado + lado // 2
        xo = ox + self.cols * lado
        fin = (self.cols - 1, self.salida)
        conectado = todo or (fin in self.encendidas and bool(self.mascara(fin) & E))
        caliente = ((255, 176, 64), (96, 44, 10), (255, 238, 180))
        frio = ((84, 92, 128), (14, 14, 22), (136, 146, 186))
        _tubo(screen, [(ox - lado * 0.55, yin), (ox + 2, yin)], grosor, *caliente)
        _tubo(screen, [(xo - 2, yout), (xo + lado * 0.42, yout)], grosor, *(caliente if conectado else frio))
        # Las piezas, con su giro animado.
        giros = getattr(self, "_giros", {})
        for c in self.base:
            x, y = c
            centro = (ox + x * lado + lado / 2, oy + y * lado + lado / 2)
            puntos, (a, b) = self._camino_pieza(c, centro, lado, dist)
            k = (self.t - giros[c]) / 150 if c in giros else 1.0
            if k < 1:
                ang = -math.pi / 2 * (1 - _suave(k))
                co, si = math.cos(ang), math.sin(ang)
                puntos = [(centro[0] + (px - centro[0]) * co - (py - centro[1]) * si,
                           centro[1] + (px - centro[0]) * si + (py - centro[1]) * co) for px, py in puntos]
            on = c in self.encendidas or todo
            if on:
                brillo(screen, centro, lado * 0.62, (52, 30, 8))
            colores = caliente if on else frio
            _tubo(screen, puntos, grosor, *colores)
            # La abrazadera del medio (con un tornillito).
            medio = self._en_camino(puntos, 0.5)
            r = max(4, int(grosor * 0.85))
            pygame.draw.circle(screen, (14, 14, 20), (int(medio[0]) + 1, int(medio[1]) + 1), r + 1)
            pygame.draw.circle(screen, (128, 134, 152) if not on else (200, 160, 110), (int(medio[0]), int(medio[1])), r)
            pygame.draw.circle(screen, (40, 42, 54), (int(medio[0]), int(medio[1])), max(1, r // 3))
            # Las puntas de cobre que no tocan nada.
            if k >= 1:
                for d, p in ((a, puntos[0]), (b, puntos[-1])):
                    v = (x + DIRECCIONES[d][0], y + DIRECCIONES[d][1])
                    unida = (v in self.base and bool(self.mascara(v) & OPUESTA[d])) \
                        or (c == (0, self.entrada) and d == O) or (c == fin and d == E)
                    if not unida:
                        pygame.draw.circle(screen, (210, 128, 60), (int(p[0]), int(p[1])), max(2, grosor // 2))
                        pygame.draw.circle(screen, (255, 200, 140), (int(p[0]) - 1, int(p[1]) - 1), max(1, grosor // 5))
            # Los pulsos de luz que corren por el cable encendido.
            if on and k >= 1:
                for u in (fase, (fase + 0.5) % 1):
                    p = self._en_camino(puntos, u)
                    pygame.draw.circle(screen, (255, 250, 220), (int(p[0]), int(p[1])), max(2, grosor // 3))
            if [x, y] == self.cursor and not self.ganado:
                celda = pygame.Rect(ox + x * lado + 1, oy + y * lado + 1, lado - 2, lado - 2)
                late = int(2 * math.sin(self.t / 140))
                largo = lado // 4
                for sx, sy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    px = celda.x - late if sx == 0 else celda.right + late
                    py = celda.y - late if sy == 0 else celda.bottom + late
                    dx = largo if sx == 0 else -largo
                    dy = largo if sy == 0 else -largo
                    pygame.draw.line(screen, COLOR_CURSOR, (px, py), (px + dx, py), 3)
                    pygame.draw.line(screen, COLOR_CURSOR, (px, py), (px, py + dy), 3)
        # La fuente: una caja con un rayo que late y chisporrotea.
        caja = pygame.Rect(0, 0, int(lado * 0.55), int(lado * 0.7))
        caja.midright = (int(ox - lado * 0.48), yin)
        brillo(screen, caja.center, lado * 0.7, (70, 50, 10))
        screen.blit(_placa(caja.w, caja.h, (70, 74, 92), (36, 38, 50), 6), caja)
        _rayo(screen, caja.center, caja.h * 0.3, (255, 214, 64))
        _chispas(screen, (caja.right, yin), int(self.t // 300), (self.t % 300) / 300, lado * 0.3)
        # El bombillo: se prende cuando la corriente llega.
        r = int(lado * 0.26)
        bc = (int(xo + lado * 0.42 + r), yout)
        rosca = pygame.Rect(0, 0, int(r * 0.8), int(r * 0.9))
        rosca.midright = (bc[0] - r + 3, yout)
        pygame.draw.rect(screen, (150, 154, 168), rosca, border_radius=3)
        for i in range(1, 3):
            xx = rosca.x + rosca.w * i // 3
            pygame.draw.line(screen, (90, 94, 108), (xx, rosca.y), (xx, rosca.bottom), 1)
        if conectado:
            brillo(screen, bc, r * 4, (120, 100, 30))
            pygame.draw.circle(screen, (255, 244, 170), bc, r)
            pygame.draw.circle(screen, (255, 255, 235), (bc[0] - r // 3, bc[1] - r // 3), max(2, r // 3))
        else:
            pygame.draw.circle(screen, (60, 66, 84), bc, r)
            pygame.draw.circle(screen, (110, 118, 150), bc, r, 2)
            pygame.draw.lines(screen, (150, 120, 80), False,
                              [(bc[0] - r // 2, bc[1]), (bc[0] - r // 6, bc[1] - r // 3),
                               (bc[0] + r // 6, bc[1]), (bc[0] + r // 2, bc[1] - r // 3)], 2)


# =====================================================================================
# Interruptores: subir todas las palancas (cada una mueve también las vecinas)
# =====================================================================================

class Interruptores(Minijuego):
    titulo = "Sube todas las palancas"
    color = (255, 214, 64)

    def __init__(self, facil=False, rng=None, titulo=None):
        super().__init__(facil, rng)
        if titulo:
            self.titulo = titulo
        self.n = 5 if facil else 6
        self.arriba = [True] * self.n
        golpes = self.rng.sample(range(self.n), 2 if facil else 3)
        for i in golpes:
            self._mover(i)
        if all(self.arriba):
            self._mover(0)
        self.cursor = 0
        self.movidas = 0
        self._movidas = {}          # palanca -> cuándo se movió (para animarla)

    def _mover(self, i):
        for j in (i - 1, i, i + 1):
            if 0 <= j < self.n:
                self.arriba[j] = not self.arriba[j]

    def _tecla(self, accion):
        if accion in ("izquierda", "arriba"):
            self.cursor = (self.cursor - 1) % self.n
            return "menu_mover"
        if accion in ("derecha", "abajo"):
            self.cursor = (self.cursor + 1) % self.n
            return "menu_mover"
        if accion == "ok":
            self._mover(self.cursor)
            self.movidas += 1
            for j in (self.cursor - 1, self.cursor, self.cursor + 1):
                if 0 <= j < self.n:
                    self._movidas[j] = self.t
            if all(self.arriba):
                self._ganar()
                return "acierto"
            return "palanca"
        return None

    def contador(self):
        return f"{sum(self.arriba)}/{self.n} arriba"

    def ayuda(self, jugador):
        return f"[{_mover2(jugador)}] elegir   [{jugador.nombre_tecla('interactuar')}] mover palanca   {_salir(jugador)}"

    def _dibujar(self, screen, rect, f):
        nota = f.render("Cada palanca mueve también las de los lados.", True, COLOR_TENUE)
        screen.blit(nota, nota.get_rect(midtop=(rect.centerx, rect.y)))
        arriba = rect.y + nota.get_height() + 8
        # La caja de fusibles: metal con franjas de peligro arriba.
        ancho = min(rect.w - 10, 74 * self.n + 40)
        caja = pygame.Rect(0, 0, ancho, rect.bottom - arriba - 4)
        caja.midtop = (rect.centerx, arriba)
        screen.blit(_placa(caja.w, caja.h, (66, 70, 84), (36, 38, 50), 10, (110, 116, 138), True), caja)
        franja = pygame.Rect(caja.x + 24, caja.y + 9, caja.w - 48, max(8, caja.h // 16))
        recorte = screen.get_clip()
        screen.set_clip(franja.clip(recorte))
        pygame.draw.rect(screen, (230, 190, 40), franja)
        for x in range(franja.x - franja.h, franja.right + franja.h, franja.h * 2):
            pygame.draw.polygon(screen, (24, 22, 20), [(x, franja.bottom), (x + franja.h, franja.y),
                                                       (x + franja.h * 2, franja.y), (x + franja.h, franja.bottom)])
        screen.set_clip(recorte)
        # La barra de cobre que une todo (se prende cuando todas suben).
        paso = (caja.w - 28) / self.n
        alto_mod = int(min(caja.h - franja.h - 64, 210))
        y_mod = franja.bottom + 30
        y_barra = franja.bottom + 14
        todas = all(self.arriba)
        if todas:
            brillo(screen, (caja.centerx, y_barra), caja.w * 0.45, (60, 50, 10))
        pygame.draw.line(screen, (40, 26, 14), (caja.x + 20, y_barra + 2), (caja.right - 20, y_barra + 2), 6)
        pygame.draw.line(screen, (226, 150, 80) if todas else (150, 96, 60),
                         (caja.x + 20, y_barra), (caja.right - 20, y_barra), 5)
        movidas = getattr(self, "_movidas", {})
        f_num = fuente_de_tamano(max(11, int(paso * 0.24)))
        for i, sube in enumerate(self.arriba):
            cx = int(caja.x + 14 + paso * (i + 0.5))
            w = int(min(paso * 0.7, 54))
            modulo = pygame.Rect(0, 0, w, alto_mod)
            modulo.midtop = (cx, y_mod)
            # Cable del módulo a la barra.
            pygame.draw.line(screen, (150, 96, 60), (cx, y_barra), (cx, modulo.y), 3)
            screen.blit(_placa(modulo.w, modulo.h, (34, 36, 46), (18, 19, 26), 8, (74, 80, 104)), modulo)
            # La luz de arriba del módulo.
            luz = (90, 240, 140) if sube else (250, 80, 70)
            led = (cx, modulo.y + 12)
            brillo(screen, led, 26, tuple(c // 4 for c in luz))
            pygame.draw.circle(screen, luz, led, 5)
            pygame.draw.circle(screen, (255, 255, 255), (led[0] - 1, led[1] - 2), 1)
            # La ranura y la palanca (se desliza al moverla).
            ranura = pygame.Rect(0, 0, max(8, w // 5), modulo.h - 50)
            ranura.midtop = (cx, modulo.y + 26)
            pygame.draw.rect(screen, (6, 6, 10), ranura, border_radius=4)
            k = (self.t - movidas[i]) / 140 if i in movidas else 1.0
            pos = 1.0 if sube else 0.0
            if k < 1:
                pos = (1 - pos) + (pos - (1 - pos)) * _suave(k)
            y = ranura.bottom - 10 - (ranura.h - 20) * pos
            mango = pygame.Rect(0, 0, w - 10, max(14, ranura.h // 5))
            mango.center = (cx, int(y))
            pygame.draw.line(screen, (90, 94, 110), (cx, ranura.centery), (cx, mango.centery), 4)
            screen.blit(_placa(mango.w, mango.h, (226, 230, 240) if sube else (150, 154, 168),
                               (150, 156, 172) if sube else (92, 96, 110), 5), mango)
            tapa = pygame.Rect(mango.x + 3, mango.y + 3, mango.w - 6, max(3, mango.h // 3))
            pygame.draw.rect(screen, (70, 200, 120) if sube else (200, 70, 60), tapa, border_radius=3)
            # Chispazo al moverla.
            if i in movidas:
                _chispas(screen, (cx, mango.centery), i * 100003 + int(movidas[i]), (self.t - movidas[i]) / 280, w * 0.9)
            num = f_num.render(str(i + 1), True, (200, 206, 226))
            screen.blit(num, num.get_rect(midtop=(cx, modulo.bottom - num.get_height() - 4)))
            if i == self.cursor and not self.ganado:
                late = 2 + int(2 * math.sin(self.t / 150))
                pygame.draw.rect(screen, COLOR_CURSOR, modulo.inflate(6 + late * 2, 6 + late * 2), 3, border_radius=10)
                punta = modulo.bottom + 6 + late
                pygame.draw.polygon(screen, COLOR_CURSOR, [(cx, punta), (cx - 7, punta + 9), (cx + 7, punta + 9)])


# =====================================================================================
# Señal: igualar la onda y "inyectar"
# =====================================================================================

class Senal(Minijuego):
    titulo = "Sintoniza la señal"
    color = (110, 220, 255)
    FRECUENCIAS = 6
    AMPLITUDES = 5

    def __init__(self, facil=False, rng=None, titulo=None):
        super().__init__(facil, rng)
        if titulo:
            self.titulo = titulo
        self.rondas = 1 if facil else 2
        self.ronda = 0
        self._nueva()

    def _nueva(self):
        r = self.rng
        self.objetivo = (r.randrange(1, self.FRECUENCIAS + 1), r.randrange(1, self.AMPLITUDES + 1))
        while True:
            self.f, self.a = r.randrange(1, self.FRECUENCIAS + 1), r.randrange(1, self.AMPLITUDES + 1)
            if (self.f, self.a) != self.objetivo:
                break

    @property
    def igual(self):
        return (self.f, self.a) == self.objetivo

    def _tecla(self, accion):
        if accion == "izquierda":
            self.f = max(1, self.f - 1)
            return "menu_mover"
        if accion == "derecha":
            self.f = min(self.FRECUENCIAS, self.f + 1)
            return "menu_mover"
        if accion == "arriba":
            self.a = min(self.AMPLITUDES, self.a + 1)
            return "menu_mover"
        if accion == "abajo":
            self.a = max(1, self.a - 1)
            return "menu_mover"
        if accion == "ok":
            if not self.igual:
                self._fallar()
                return "fallo"
            self.ronda += 1
            if self.ronda >= self.rondas:
                self._ganar()
            else:
                self._nueva()
            return "acierto"
        return None

    def contador(self):
        return f"{min(self.ronda + 1, self.rondas)}/{self.rondas}" if self.rondas > 1 else ""

    def ayuda(self, jugador):
        return (f"[{_mover4(jugador)}] frecuencia y fuerza   "
                f"[{jugador.nombre_tecla('interactuar')}] inyectar   {_salir(jugador)}")

    def _onda(self, superficie, w, h, f, a, fase):
        puntos = []
        for i in range(0, w + 1, 3):
            y = h / 2 - math.sin(i / w * math.pi * 2 * f + fase) * a / self.AMPLITUDES * h * 0.4
            puntos.append((i, y))
        return puntos

    @staticmethod
    def _pantalla_crt(w, h):
        """El fondo del osciloscopio: fósforo verde oscuro, cuadrícula, rayas
        de barrido y las esquinas más oscuras (guardado por tamaño)."""
        def armar():
            img = pygame.Surface((w, h))
            img.fill((4, 18, 14))
            for k in range(10):
                pygame.draw.rect(img, _mezcla((4, 18, 14), (0, 3, 2), 1 - k / 10), (k * 2, k * 2, w - k * 4, h - k * 4), 2,
                                 border_radius=14)
            for i in range(1, 8):
                x = w * i // 8
                pygame.draw.line(img, (14, 48, 36), (x, 6), (x, h - 6))
            for j in range(1, 6):
                y = h * j // 6
                pygame.draw.line(img, (14, 48, 36), (6, y), (w - 6, y))
            pygame.draw.line(img, (24, 74, 54), (6, h // 2), (w - 6, h // 2))
            for x in range(6, w - 6, max(6, w // 40)):
                pygame.draw.line(img, (24, 74, 54), (x, h // 2 - 3), (x, h // 2 + 3))
            for y in range(0, h, 3):
                pygame.draw.line(img, (0, 6, 4), (0, y), (w, y))
            return img
        return _guardado(("crt", w, h), armar)

    def _perilla(self, screen, c, r, valor, maximo, color, etiqueta, f):
        """Una perilla con sus marcas: las que van hasta el valor, prendidas."""
        pygame.draw.circle(screen, (10, 10, 14), (c[0] + 2, c[1] + 3), r + 2)
        for k in range(6):
            pygame.draw.circle(screen, _mezcla((40, 44, 58), (160, 166, 186), k / 5), c, int(r * (1 - k * 0.12)))
        for i in range(maximo):
            a = math.radians(225 - 270 * i / max(1, maximo - 1))
            p1 = (c[0] + math.cos(a) * (r + 5), c[1] - math.sin(a) * (r + 5))
            p2 = (c[0] + math.cos(a) * (r + 11), c[1] - math.sin(a) * (r + 11))
            pygame.draw.line(screen, color if i < valor else (50, 56, 74), p1, p2, 3)
        a = math.radians(225 - 270 * (valor - 1) / max(1, maximo - 1))
        pygame.draw.line(screen, (250, 252, 255), c, (c[0] + math.cos(a) * r * 0.8, c[1] - math.sin(a) * r * 0.8), 3)
        pygame.draw.circle(screen, (30, 32, 42), c, max(2, r // 5))
        img = f.render(etiqueta, True, COLOR_TENUE)
        screen.blit(img, img.get_rect(midtop=(c[0], c[1] + r + 8)))

    def _dibujar(self, screen, rect, f):
        f_chica = fuente_de_tamano(max(11, f.get_height() - 3))
        alto_texto = f.get_linesize() + 2
        r = int(max(12, min(26, rect.h * 0.085)))
        alto_perillas = (r + 12) + r + 8 + f_chica.get_linesize() + 4
        pantalla = pygame.Rect(rect.x + 8, rect.y + 8, rect.w - 16, rect.h - alto_perillas - alto_texto - 22)
        # El marco de metal y el vidrio.
        screen.blit(_placa(pantalla.w + 16, pantalla.h + 16, (90, 96, 116), (46, 50, 64), 14, None, True),
                    pantalla.move(-8, -8).topleft)
        screen.blit(self._pantalla_crt(pantalla.w, pantalla.h), pantalla)
        # Las ondas, sumadas como luz de fósforo.
        luz = pygame.Surface(pantalla.size)
        luz.fill((0, 0, 0))
        fase = self.t / 240
        fantasma = self._onda(luz, pantalla.w, pantalla.h, *self.objetivo, fase)
        pygame.draw.lines(luz, (10, 40, 22), False, fantasma, 11)
        pygame.draw.lines(luz, (26, 100, 52), False, fantasma, 5)
        mia = self._onda(luz, pantalla.w, pantalla.h, self.f, self.a, fase)
        color = (110, 255, 160) if self.igual else self.color
        pygame.draw.lines(luz, tuple(c // 6 for c in color), False, mia, 12)
        pygame.draw.lines(luz, tuple(c // 3 for c in color), False, mia, 6)
        pygame.draw.lines(luz, color, False, mia, 2)
        # La línea que barre la pantalla, con su estela.
        x = int((self.t / 1500 % 1) * pantalla.w)
        for k in range(5):
            pygame.draw.line(luz, (0, 18 - k * 3, 13 - k * 2), (x - k * 4, 0), (x - k * 4, pantalla.h), 2)
        screen.blit(luz, pantalla, special_flags=pygame.BLEND_RGB_ADD)
        if self.igual:
            parpadeo = (self.t // 300) % 2 == 0
            marca = pygame.Rect(0, 0, 16, 16)
            marca.topright = (pantalla.right - 10, pantalla.y + 10)
            pygame.draw.circle(screen, (110, 255, 160) if parpadeo else (40, 110, 70), marca.center, 7)
        # Las perillas y, en medio, qué tan cerca está.
        y = pantalla.bottom + 10 + r + 12
        self._perilla(screen, (rect.x + int(rect.w * 0.16), y), r, self.f, self.FRECUENCIAS, self.color,
                      "Frecuencia", f_chica)
        self._perilla(screen, (rect.right - int(rect.w * 0.16), y), r, self.a, self.AMPLITUDES, self.color,
                      "Fuerza", f_chica)
        cerca = 1 - (abs(self.f - self.objetivo[0]) / (self.FRECUENCIAS - 1)
                     + abs(self.a - self.objetivo[1]) / (self.AMPLITUDES - 1)) / 2
        medidor = pygame.Rect(0, 0, int(rect.w * 0.36), 14)
        medidor.center = (rect.centerx, y)
        segmentos = 10
        ancho_seg = medidor.w / segmentos
        prendidos = int(round(cerca * segmentos))
        for i in range(segmentos):
            seg = pygame.Rect(int(medidor.x + i * ancho_seg + 1), medidor.y, int(ancho_seg - 2), medidor.h)
            col = _mezcla((250, 90, 70), (110, 255, 160), i / (segmentos - 1))
            pygame.draw.rect(screen, col if i < prendidos else (34, 38, 52), seg, border_radius=3)
        # Las rondas (las de las consolas difíciles).
        if self.rondas > 1:
            for i in range(self.rondas):
                c = (rect.centerx + (i - (self.rondas - 1) / 2) * 20, medidor.bottom + 14)
                pygame.draw.circle(screen, (110, 255, 160) if i < self.ronda else (50, 56, 74), (int(c[0]), int(c[1])), 5)
        texto = ("¡Igualita! Inyéctala." if self.igual
                 else "Iguala tu onda (clara) con la de la consola (verde oscuro).")
        letra = f if f.size(texto)[0] <= rect.w else f_chica
        img = letra.render(texto, True, COLOR_BIEN if self.igual else COLOR_TENUE)
        screen.blit(img, img.get_rect(midbottom=(rect.centerx, rect.bottom)))


# =====================================================================================
# Abono: soltar el abono cuando el saco está encima de la maceta
# =====================================================================================

class Abono(Minijuego):
    titulo = "Echa el abono en la maceta"
    color = (120, 220, 130)
    CAIDA_MS = 420

    def __init__(self, facil=False, rng=None, titulo=None):
        super().__init__(facil, rng)
        if titulo:
            self.titulo = titulo
        self.necesarios = 2 if facil else 3
        self.aciertos = 0
        self.caida = None           # (x relativa, ms) del abono que va cayendo
        self.fase = self.rng.uniform(0, 6.28)
        self.velocidad = 1.0
        self.ultimo = None          # "bien" o "mal": lo que pasó con el último
        self._golpes = []           # (x, cuándo, bien): el polvo de cada golpe
        self._acierto_t = None      # cuándo fue el último acierto (la planta crece)
        self.al_acertar = None      # función(avance 0-1): la planta de verdad crece (tareas.py)

    def empezar_en(self, progreso):
        """Seguir desde donde iba la planta (si alguien lo dejó a medias)."""
        self.aciertos = max(0, min(self.necesarios - 1, int(progreso * self.necesarios + 1e-6)))

    def avance(self):
        """Lo que va creciendo la planta en el dibujo (0 a 1), animado."""
        hecho = self.aciertos / self.necesarios
        if self._acierto_t is None:
            return hecho
        antes = (self.aciertos - 1) / self.necesarios
        return antes + (hecho - antes) * _suave((self.t - self._acierto_t) / 700)

    def _dibujar_planta(self, screen, base, alto_vista, ancho_maceta):
        """La planta parada en la tierra; devuelve hasta dónde llega (y)."""
        from misiones import guardia
        hojas = guardia.imagenes_planta()
        if hojas is None:
            alto = 16 + 70 * self.avance()
            pygame.draw.line(screen, (40, 120, 60), base, (base[0], base[1] - alto), 5)
            pygame.draw.line(screen, (100, 210, 110), base, (base[0], base[1] - alto), 3)
            return int(base[1] - alto)
        cuadros = hojas[0]
        k = (self.t - self._acierto_t) / 700 if self._acierto_t is not None else 1.0
        if self.ganado and k >= 1:
            i = len(cuadros) - 1           # ya crecida, con su fruta
        else:
            i = guardia.cuadro_planta(self.avance(), len(cuadros))
        # Agrandada a un múltiplo entero de sus 64 px (que el pixel art no se deforme).
        lado = max(64, int(min(alto_vista * 0.62, ancho_maceta * 2.6)) // 64 * 64)
        if k < 1:
            brillo(screen, (base[0], base[1] - lado // 3), lado * 0.6 * (1 - k * 0.5), (24, 60, 30))
        img = _guardado(("planta", i, lado), lambda: pygame.transform.scale(
            pygame.transform.scale(cuadros[i], (64, 64)), (lado, lado)))
        caja = img.get_rect(midbottom=base)
        screen.blit(img, caja)
        recorte = img.get_bounding_rect()
        return caja.y + recorte.y

    def x_saco(self):
        """Dónde está el saco (de -1 a 1; 0 = sobre la maceta)."""
        return math.sin(self.fase)

    def _actualizar(self, dt):
        self.fase += dt / 1000 * (2.1 + 0.55 * self.aciertos) * self.velocidad
        if self.caida is not None:
            x, ms = self.caida
            ms += dt
            if ms >= self.CAIDA_MS:
                self.caida = None
                self._golpes = self._golpes[-3:] + [(x, self.t, abs(x) <= 0.2)]
                if abs(x) <= 0.2:
                    self.aciertos += 1
                    self._acierto_t = self.t
                    self.ultimo = "bien"
                    if self.al_acertar is not None:
                        self.al_acertar(self.aciertos / self.necesarios)
                    if self.aciertos >= self.necesarios:
                        self._ganar()
                else:
                    self.ultimo = "mal"
                    self._fallar()
            else:
                self.caida = (x, ms)

    def _tecla(self, accion):
        if accion == "ok" and self.caida is None:
            self.caida = (self.x_saco(), 0)
            return "soltar"
        return None

    def contador(self):
        return f"{self.aciertos}/{self.necesarios}"

    def ayuda(self, jugador):
        return f"[{jugador.nombre_tecla('interactuar')}] soltar el abono   {_salir(jugador)}"

    def _dibujar(self, screen, rect, f):
        # El invernadero de fondo.
        fondo = _placa(rect.w, rect.h, (20, 44, 34), (10, 22, 18), 10, (40, 80, 60))
        screen.blit(fondo, rect)
        for i in range(1, 5):
            x = rect.x + rect.w * i // 5
            pygame.draw.line(screen, (26, 56, 44), (x, rect.y + 4), (x - rect.w // 14, rect.bottom - 4), 2)
        piso = rect.bottom - 10
        # Matas de fondo en las esquinas y la luz de cultivo sobre la maceta.
        azar = random.Random(3)
        for lado_x in (rect.x + 10, rect.right - 10):
            for _ in range(9):
                hoja = pygame.Rect(0, 0, azar.randint(16, 30), azar.randint(8, 14))
                hoja.center = (int(lado_x + azar.uniform(-8, 34) * (1 if lado_x < rect.centerx else -1)),
                               int(piso - azar.uniform(4, rect.h * 0.28)))
                pygame.draw.ellipse(screen, azar.choice(((24, 70, 40), (30, 86, 48), (20, 58, 34))), hoja)
        brillo(screen, (rect.centerx, piso - rect.h * 0.25), rect.h * 0.5, (30, 14, 34))
        pygame.draw.rect(screen, (34, 28, 22), (rect.x + 2, piso, rect.w - 4, 8), border_radius=3)
        mitad = (rect.w - 90) / 2
        cx = rect.centerx
        # El riel de arriba (una viga de metal).
        riel_y = rect.y + 16
        pygame.draw.rect(screen, (10, 12, 16), (rect.x + 8, riel_y - 3, rect.w - 16, 10), border_radius=3)
        pygame.draw.rect(screen, (120, 126, 146), (rect.x + 8, riel_y - 5, rect.w - 16, 8), border_radius=3)
        pygame.draw.line(screen, (190, 196, 214), (rect.x + 12, riel_y - 4), (rect.right - 12, riel_y - 4), 1)
        # La maceta (barro) con la tierra.
        maceta = pygame.Rect(0, 0, int(max(70, mitad * 0.5)), int(min(56, rect.h * 0.2)))
        maceta.midbottom = (cx, piso)
        cuerpo = [(maceta.x, maceta.y), (maceta.right, maceta.y),
                  (maceta.right - maceta.w // 7, maceta.bottom), (maceta.x + maceta.w // 7, maceta.bottom)]
        pygame.draw.polygon(screen, (168, 92, 56), cuerpo)
        pygame.draw.polygon(screen, (196, 116, 74), [cuerpo[0], (cx - maceta.w // 6, maceta.y),
                                                     (cx - maceta.w // 5, maceta.bottom), cuerpo[3]])
        pygame.draw.polygon(screen, (90, 46, 28), cuerpo, 2)
        borde = pygame.Rect(maceta.x - 6, maceta.y - 9, maceta.w + 12, 12)
        screen.blit(_placa(borde.w, borde.h, (206, 124, 80), (146, 78, 46), 4), borde)
        tierra = pygame.Rect(maceta.x - 2, maceta.y - 13, maceta.w + 4, 10)
        pygame.draw.ellipse(screen, (58, 38, 26), tierra)
        azar = random.Random(7)
        for _ in range(12):
            px = tierra.x + 6 + azar.random() * (tierra.w - 12)
            pygame.draw.circle(screen, (90, 62, 40), (int(px), int(tierra.centery + azar.uniform(-2, 2))), 1)
        # La zona buena: donde el abono cae dentro (late en verde).
        zona = pygame.Rect(0, 0, int(mitad * 0.4), 10)
        zona.center = tierra.center
        late = 0.5 + 0.5 * math.sin(self.t / 220)
        pygame.draw.ellipse(screen, _mezcla((40, 90, 50), (120, 240, 140), late), zona, 2)
        # La planta: la misma de la Biosfera (misiones/guardia.py), que crece
        # cuadro por cuadro con cada acierto.
        tope_planta = self._dibujar_planta(screen, (cx, tierra.centery + 3), rect.h, maceta.w)
        # El carrito del riel, la cuerda y el saco (que se inclina al mecerse).
        sx = cx + self.x_saco() * mitad
        inclina = -math.cos(self.fase) * 0.28
        carro = pygame.Rect(0, 0, 30, 12)
        carro.midtop = (int(sx), riel_y - 12)
        pygame.draw.rect(screen, (70, 76, 96), carro, border_radius=3)
        for dx in (-9, 9):
            pygame.draw.circle(screen, (24, 26, 34), (carro.centerx + dx, riel_y - 6), 4)
            pygame.draw.circle(screen, (150, 156, 176), (carro.centerx + dx, riel_y - 6), 2)
        cuelga = (sx, riel_y + 4)
        largo = 26
        e = max(1.0, min(1.6, rect.h / 200))

        def girado(px, py):
            px, py = px * e, py * e
            co, si = math.cos(inclina), math.sin(inclina)
            return (cuelga[0] + px * co - py * si, cuelga[1] + px * si + py * co)
        nudo = girado(0, largo)
        pygame.draw.line(screen, (150, 120, 80), cuelga, nudo, 2)
        saco = [girado(*p) for p in ((-6, largo), (6, largo), (20, largo + 14), (22, largo + 40),
                                     (14, largo + 50), (-14, largo + 50), (-22, largo + 40), (-20, largo + 14))]
        pygame.draw.polygon(screen, (196, 160, 110), saco)
        lado_claro = [girado(*p) for p in ((-6, largo), (0, largo), (-4, largo + 50), (-14, largo + 50),
                                           (-22, largo + 40), (-20, largo + 14))]
        pygame.draw.polygon(screen, (214, 182, 132), lado_claro)
        pygame.draw.polygon(screen, (120, 88, 56), saco, 2)
        # El amarre de arriba y las costuras.
        pygame.draw.line(screen, (120, 88, 56), girado(-8, largo + 4), girado(8, largo + 4), 3)
        for py in (largo + 22, largo + 38):
            puntos = [girado(x, py + (2 if (x // 4) % 2 else 0)) for x in range(-18, 20, 4)]
            pygame.draw.lines(screen, (150, 116, 76), False, puntos, 1)
        # Una hojita pintada: es abono.
        centro_hoja = girado(0, largo + 30)
        pygame.draw.circle(screen, (70, 160, 80), (int(centro_hoja[0]), int(centro_hoja[1])), int(5 * e))
        pygame.draw.circle(screen, (130, 220, 130), (int(centro_hoja[0]) - 1, int(centro_hoja[1]) - 1), max(1, int(2 * e)))
        boca = girado(0, largo + 50)
        # La guía: dónde caería si lo suelta ahora.
        dentro = abs(self.x_saco()) <= 0.2
        for yy in range(int(boca[1]) + 8, tierra.y - 4, 10):
            pygame.draw.line(screen, (110, 230, 140) if dentro else (80, 90, 110), (sx, yy), (sx, yy + 4), 2)
        # El abono cayendo (granitos con algo de dispersión).
        if self.caida is not None:
            x, ms = self.caida
            k = ms / self.CAIDA_MS
            px = cx + x * mitad
            py = boca[1] + (tierra.centery - boca[1]) * k * k
            azar = random.Random(int(x * 1000))
            for i in range(9):
                dx = azar.uniform(-1, 1) * (3 + 10 * k)
                dy = azar.uniform(-6, 6)
                pygame.draw.circle(screen, (110, 76, 44), (int(px + dx), int(py + dy)), 3)
                pygame.draw.circle(screen, (150, 110, 70), (int(px + dx) - 1, int(py + dy) - 1), 1)
        # El polvo de cada golpe.
        for x, t0, bien in getattr(self, "_golpes", []):
            k = (self.t - t0) / 450
            if k >= 1:
                continue
            px = cx + x * mitad
            py = tierra.centery if bien else piso
            azar = random.Random(int(t0))
            for _ in range(10):
                a = azar.uniform(math.pi, math.tau)
                v = azar.uniform(8, 26) * _suave(k)
                color = (120, 230, 140) if bien else (140, 110, 80)
                pygame.draw.circle(screen, _mezcla(color, (20, 30, 24), k),
                                   (int(px + math.cos(a) * v), int(py + math.sin(a) * v * 0.6)), max(1, int(3 * (1 - k))))
        if self.ultimo == "mal" and self.error_ms > 0:
            img = f.render("Se cayó afuera...", True, COLOR_MAL)
            screen.blit(img, img.get_rect(midbottom=(cx, max(rect.y + 60, tope_planta - 8))))


# =====================================================================================
# Ganzúa: subir los pines justo a la línea
# =====================================================================================

class Ganzua(Minijuego):
    titulo = "Fuerza el candado"
    color = (200, 170, 255)
    ZONA = (0.72, 0.9)

    def __init__(self, facil=False, rng=None, titulo=None):
        super().__init__(facil, rng)
        if titulo:
            self.titulo = titulo
        self.n = 3 if facil else 4
        self.puestos = 0
        self.velocidades = [self.rng.uniform(1.6, 2.6) for _ in range(self.n)]
        self.fases = [self.rng.uniform(0, 6.28) for _ in range(self.n)]

    def altura(self, i):
        """0 (abajo) a 1 (arriba) del pin i mientras se mueve."""
        return 0.5 + 0.5 * math.sin(self.fases[i])

    def _actualizar(self, dt):
        if self.puestos < self.n:
            i = self.puestos
            self.fases[i] += dt / 1000 * self.velocidades[i] * 2

    def _tecla(self, accion):
        if accion != "ok" or self.puestos >= self.n:
            return None
        a, b = self.ZONA
        if a <= self.altura(self.puestos) <= b:
            self.puestos += 1
            if self.puestos >= self.n:
                self._ganar()
            return "acierto"
        self._fallar()
        if self.puestos > 0:
            self.puestos -= 1           # el anterior se cae
        return "fallo"

    def contador(self):
        return f"{self.puestos}/{self.n} pines"

    def ayuda(self, jugador):
        return f"[{jugador.nombre_tecla('interactuar')}] fijar el pin cuando toque la línea   {_salir(jugador)}"

    def _dibujar(self, screen, rect, f):
        a, b = self.ZONA
        cuerpo = pygame.Rect(0, 0, min(rect.w - 80, 76 * self.n + 60), rect.h - 10)
        cuerpo.midtop = (rect.centerx + 26, rect.y + 2)
        # El cilindro de bronce, cortado por la mitad.
        screen.blit(_placa(cuerpo.w, cuerpo.h, (190, 152, 72), (112, 84, 34), 14, (70, 50, 20), True), cuerpo)
        arriba = cuerpo.y + 18
        alto_canal = max(12, cuerpo.h // 10)
        canal = pygame.Rect(cuerpo.x + 18, cuerpo.bottom - 16 - alto_canal, cuerpo.w - 36, alto_canal)
        H = canal.y - arriba
        largo_pin, sube_max, largo_empuja = int(H * 0.26), H * 0.42, int(H * 0.14)

        def tope_pin(altura):
            return canal.y - largo_pin - sube_max * altura
        corte = int(tope_pin((a + b) / 2))
        # El rotor (abajo de la línea de corte) es más claro: gira cuando todos
        # los pines quedan justo en la línea.
        rotor = pygame.Rect(cuerpo.x + 12, corte, cuerpo.w - 24, cuerpo.bottom - 10 - corte)
        screen.blit(_placa(rotor.w, rotor.h, (222, 184, 98), (160, 124, 54), 8, (96, 70, 28)), rotor)
        pygame.draw.rect(screen, (30, 22, 10), canal, border_radius=5)
        pygame.draw.line(screen, (60, 44, 20), (canal.x + 4, canal.y + 2), (canal.right - 4, canal.y + 2), 1)
        en_zona = self.puestos < self.n and a <= self.altura(self.puestos) <= b
        paso = canal.w / self.n
        ancho = max(10, int(paso * 0.32))
        banda_y, banda_h = int(tope_pin(b)), int(tope_pin(a) - tope_pin(b))
        punta = None
        for i in range(self.n):
            cx = int(canal.x + paso * (i + 0.5))
            camara = pygame.Rect(0, 0, ancho + 8, canal.y - arriba)
            camara.midtop = (cx, arriba)
            pygame.draw.rect(screen, (26, 18, 8), camara, border_radius=4)
            pygame.draw.line(screen, (12, 8, 4), camara.topleft, camara.bottomleft, 2)
            # La franja buena dentro de la cámara.
            zona = pygame.Rect(camara.x + 2, banda_y, camara.w - 4, banda_h)
            pygame.draw.rect(screen, (40, 110, 60) if (i == self.puestos and en_zona) else (24, 60, 34), zona)
            if i < self.puestos:
                altura = (a + b) / 2
            elif i == self.puestos:
                altura = self.altura(i)
            else:
                altura = 0.0
            fijo = i < self.puestos or self.ganado
            actual = i == self.puestos and not self.ganado
            y = int(tope_pin(altura))
            # El pin de abajo (bronce, con la punta hacia la llave).
            pin = pygame.Rect(0, 0, ancho, largo_pin)
            pin.midtop = (cx, y)
            colores = (((150, 240, 160), (70, 160, 90)) if fijo else
                       ((255, 226, 120), (200, 150, 50)) if actual else ((226, 190, 110), (156, 120, 60)))
            screen.blit(_placa(pin.w, pin.h, colores[0], colores[1], 4), pin)
            pygame.draw.polygon(screen, colores[1], [(pin.x + 1, pin.bottom - 2), (pin.right - 1, pin.bottom - 2),
                                                     (cx, pin.bottom + 5)])
            # El de arriba (plateado) y el resorte hasta el techo.
            empuja = pygame.Rect(0, 0, ancho, largo_empuja)
            empuja.midbottom = (cx, y - 1)
            screen.blit(_placa(empuja.w, empuja.h, (226, 230, 240), (136, 142, 158), 4), empuja)
            tope = camara.y + 2
            if empuja.y - tope > 4:
                puntos = [(cx + (ancho // 2 - 1) * (1 if k % 2 else -1), tope + (empuja.y - tope) * k / 12)
                          for k in range(13)]
                pygame.draw.lines(screen, (176, 182, 200), False, puntos, 2)
            if fijo:
                brillo(screen, (cx, corte), ancho * 1.4, (16, 60, 26))
            if actual:
                punta = (cx, pin.bottom + 5)
        # La línea de corte.
        pygame.draw.line(screen, (130, 255, 160) if en_zona else (70, 180, 100), (rotor.x, corte), (rotor.right, corte), 2)
        # La llave de tensión (la L) y la ganzúa, que levanta el pin que toca.
        llave = [(cuerpo.x - 34, canal.bottom + 14), (cuerpo.x - 34, canal.bottom - 3), (canal.x + 16, canal.bottom - 3)]
        pygame.draw.lines(screen, (20, 22, 28), False, [(p[0] + 1, p[1] + 2) for p in llave], 7)
        pygame.draw.lines(screen, (120, 126, 144), False, llave, 5)
        if punta is not None:
            sacude = int(math.sin(self.t / 18) * 3) if self.error_ms > 0 else 0
            y_canal = canal.centery + sacude
            mango = (rect.x + 4, y_canal + 2)
            gancho = [mango, (canal.x + 6, y_canal), (punta[0] - 12, y_canal), (punta[0], punta[1] + 1)]
            pygame.draw.lines(screen, (20, 22, 28), False, [(p[0] + 1, p[1] + 2) for p in gancho], 5)
            pygame.draw.lines(screen, (210, 214, 230), False, gancho, 3)
            agarre = pygame.Rect(0, 0, 36, 13)
            agarre.midleft = mango
            screen.blit(_placa(agarre.w, agarre.h, (110, 76, 170), (60, 36, 100), 5), agarre)
        if self.ganado:
            brillo(screen, (cuerpo.centerx, corte), cuerpo.w * 0.45, (20, 60, 30))


TIPOS = {"cables": Cables, "interruptores": Interruptores, "senal": Senal, "abono": Abono, "ganzua": Ganzua}


def crear(tipo, facil=False, rng=None, titulo=None):
    return TIPOS[tipo](facil, rng, titulo)
