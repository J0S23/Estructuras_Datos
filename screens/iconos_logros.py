"""El dibujo de cada logro (screens/logros.insignia): uno por logro, de lo que
se hace para conseguirlo (Mano verde: un brote; Pasos de gato: una huella de
gato; Electricista: un rayo...). Antes todos los de una rama llevaban el
mismo ícono (Mano verde, el de la rama de los aliens: una cabeza de alien).

Se dibujan con formas, como los íconos de las ramas, dentro de un cuadrado de
lado `s` centrado en `centro`; `color` es el del dibujo y `fondo` el de lo que
queda hueco (ojos, ventanas). `dibujar(sup, clave, centro, s, color, fondo)`
devuelve False si el logro no tiene dibujo propio (entonces va el de su rama).

Para agregar uno: una función `_clave(d)` aquí y su entrada en DIBUJOS.
"""

import math

import pygame


class _Lienzo:
    """Coordenadas relativas: (0, 0) es el centro y ±0.5 los bordes."""

    def __init__(self, sup, centro, s, color, fondo):
        self.sup, self.cx, self.cy, self.s = sup, centro[0], centro[1], s
        self.color, self.fondo = color, fondo
        self.g = max(2, int(s * 0.085))           # grosor de las líneas

    def p(self, x, y):
        return (self.cx + x * self.s, self.cy + y * self.s)

    def ps(self, puntos):
        return [self.p(x, y) for x, y in puntos]

    def r(self, v):
        return max(1, int(v * self.s))

    def tono(self, t):
        """Entre el color (0) y el fondo (1)."""
        return tuple(int(self.color[i] + (self.fondo[i] - self.color[i]) * t) for i in range(3))

    # Formas
    def circulo(self, x, y, radio, color=None, ancho=0):
        pygame.draw.circle(self.sup, color or self.color, [int(v) for v in self.p(x, y)], self.r(radio),
                           self.r(ancho) if ancho else 0)

    def poligono(self, puntos, color=None, ancho=0):
        pygame.draw.polygon(self.sup, color or self.color, self.ps(puntos), self.r(ancho) if ancho else 0)

    def linea(self, puntos, color=None, ancho=None, cerrada=False):
        pygame.draw.lines(self.sup, color or self.color, cerrada, self.ps(puntos),
                          self.r(ancho) if ancho else self.g)

    def rect(self, x, y, w, h, color=None, ancho=0, radio=0):
        caja = pygame.Rect(int(self.cx + x * self.s), int(self.cy + y * self.s), self.r(w), self.r(h))
        pygame.draw.rect(self.sup, color or self.color, caja, self.r(ancho) if ancho else 0,
                         border_radius=self.r(radio) if radio else 0)

    def elipse(self, x, y, w, h, color=None, ancho=0):
        caja = pygame.Rect(int(self.cx + x * self.s), int(self.cy + y * self.s), self.r(w), self.r(h))
        pygame.draw.ellipse(self.sup, color or self.color, caja, self.r(ancho) if ancho else 0)

    def arco(self, x, y, radio, desde, hasta, color=None, ancho=None, pasos=24):
        """Arco de `desde` a `hasta` (grados, 0 = derecha, contra el reloj)."""
        puntos = []
        for i in range(pasos + 1):
            a = math.radians(desde + (hasta - desde) * i / pasos)
            puntos.append((x + radio * math.cos(a), y - radio * math.sin(a)))
        self.linea(puntos, color, ancho)

    def estrella(self, x, y, r_fuera, r_dentro, puntas=5, color=None, giro=-90):
        puntos = []
        for i in range(puntas * 2):
            r = r_fuera if i % 2 == 0 else r_dentro
            a = math.radians(giro + i * 180 / puntas)
            puntos.append((x + r * math.cos(a), y + r * math.sin(a)))
        self.poligono(puntos, color)

    def palomita(self, x, y, tam, color=None, ancho=None):
        self.linea([(x - tam, y), (x - tam * 0.3, y + tam * 0.7), (x + tam, y - tam * 0.8)], color, ancho)

    def equis(self, x, y, tam, color=None, ancho=None):
        self.linea([(x - tam, y - tam), (x + tam, y + tam)], color, ancho)
        self.linea([(x + tam, y - tam), (x - tam, y + tam)], color, ancho)

    def persona(self, x, y, tam, color=None):
        """Cabeza y hombros, centrada en (x, y)."""
        self.circulo(x, y - tam * 0.42, tam * 0.3, color)
        self.elipse(x - tam * 0.5, y - tam * 0.05, tam, tam * 0.9, color)

    def cabeza_alien(self, x, y, tam, color=None, ojos=None):
        self.elipse(x - tam * 0.5, y - tam * 0.62, tam, tam * 0.88, color)
        self.poligono([(x - tam * 0.44, y - tam * 0.06), (x + tam * 0.44, y - tam * 0.06), (x, y + tam * 0.66)],
                      color)
        for lado in (-1, 1):
            self.poligono([(x + lado * tam * 0.4, y - tam * 0.24), (x + lado * tam * 0.07, y - tam * 0.03),
                           (x + lado * tam * 0.1, y + tam * 0.14), (x + lado * tam * 0.35, y + tam * 0.03)],
                          ojos or self.fondo)


# -- Inicio ---------------------------------------------------------------------------------

def _despertar(d):
    # El sol que sale por el horizonte.
    d.circulo(0, 0.14, 0.24)
    d.rect(-0.5, 0.14, 1.0, 0.4, d.fondo)
    d.linea([(-0.46, 0.16), (0.46, 0.16)])
    for a in (180, 150, 120, 90, 60, 30, 0):
        r = math.radians(a)
        d.linea([(0.33 * math.cos(r), 0.12 - 0.33 * math.sin(r)), (0.45 * math.cos(r), 0.12 - 0.45 * math.sin(r))])
    d.linea([(-0.3, 0.3), (0.3, 0.3)], d.tono(0.4))


# -- Sigilo ---------------------------------------------------------------------------------

def _sigiloso(d):
    # Un ojo entrecerrado (el de la rama).
    n = 20
    arriba = [(-0.46 + 0.92 * i / n, -0.2 * math.sin(math.pi * i / n)) for i in range(n + 1)]
    abajo = [(0.46 - 0.92 * i / n, 0.24 * math.sin(math.pi * i / n)) for i in range(n + 1)]
    d.poligono(arriba + abajo)
    d.circulo(0, 0.02, 0.16, d.fondo)
    d.circulo(0, 0.02, 0.07)
    d.linea([(-0.48, -0.08), (0.48, -0.08)], d.fondo, 0.06)


def _pasos_de_gato(d):
    # Una huella de gato.
    d.elipse(-0.22, 0.0, 0.44, 0.36)
    d.circulo(-0.13, 0.28, 0.1)
    d.circulo(0.13, 0.28, 0.1)
    for x, y in ((-0.34, -0.12), (-0.13, -0.3), (0.13, -0.3), (0.34, -0.12)):
        d.elipse(x - 0.09, y - 0.12, 0.18, 0.24)


def _shhh(d):
    # Un parlante en silencio.
    d.poligono([(-0.42, -0.12), (-0.24, -0.12), (-0.04, -0.32), (-0.04, 0.32), (-0.24, 0.12), (-0.42, 0.12)])
    d.equis(0.24, 0, 0.13)


def _fantasma(d):
    # Un fantasmita.
    d.circulo(0, -0.1, 0.32)
    d.rect(-0.32, -0.1, 0.64, 0.4)
    olas = [(-0.32, 0.3)]
    for i in range(4):
        x0 = -0.32 + 0.16 * i
        olas += [(x0 + 0.08, 0.44), (x0 + 0.16, 0.3)]
    d.poligono([(-0.32, 0.28)] + olas + [(0.32, 0.28)])
    d.elipse(-0.17, -0.18, 0.11, 0.17, d.fondo)
    d.elipse(0.06, -0.18, 0.11, 0.17, d.fondo)


# -- Escape ---------------------------------------------------------------------------------

def _codigo_roto(d):
    # El teclado de la puerta.
    d.rect(-0.32, -0.44, 0.64, 0.88, ancho=0.07, radio=0.07)
    d.rect(-0.2, -0.32, 0.4, 0.14, d.tono(0.35), radio=0.03)
    for fila in range(3):
        for col in range(3):
            d.circulo(-0.15 + col * 0.15, -0.04 + fila * 0.14, 0.05)


def _a_la_primera(d):
    # Una diana con la flecha en el centro.
    d.circulo(-0.04, 0.04, 0.38, ancho=0.07)
    d.circulo(-0.04, 0.04, 0.22, ancho=0.07)
    d.circulo(-0.04, 0.04, 0.07)
    d.linea([(-0.04, 0.04), (0.4, -0.4)], ancho=0.06)
    d.poligono([(0.4, -0.4), (0.24, -0.38), (0.38, -0.24)])
    d.poligono([(0.34, -0.46), (0.46, -0.34), (0.48, -0.48)])


def _sin_rumbo(d):
    # Una brújula con la aguja loca.
    d.circulo(0, 0, 0.42, ancho=0.07)
    for a in (0, 90, 180, 270):
        r = math.radians(a)
        d.linea([(0.3 * math.cos(r), 0.3 * math.sin(r)), (0.38 * math.cos(r), 0.38 * math.sin(r))], ancho=0.05)
    a = math.radians(35)
    ux, uy = math.cos(a), math.sin(a)
    d.poligono([(0.3 * ux, -0.3 * uy), (0.07 * uy, 0.07 * ux), (-0.3 * ux, 0.3 * uy), (-0.07 * uy, -0.07 * ux)])
    d.poligono([(-0.3 * ux, 0.3 * uy), (-0.07 * uy, -0.07 * ux), (0, 0), (0.07 * uy, 0.07 * ux)], d.tono(0.5))
    d.circulo(0, 0, 0.05, d.fondo)


def _sin_rastro(d):
    # Una huella de pie descalzo, tachada.
    d.elipse(-0.16, -0.14, 0.32, 0.56)
    for dx, dy, r in ((-0.13, -0.24, 0.075), (-0.03, -0.31, 0.06), (0.06, -0.31, 0.055), (0.14, -0.27, 0.05),
                      (0.2, -0.2, 0.045)):
        d.circulo(dx, dy, r)
    d.linea([(-0.42, 0.42), (0.42, -0.42)], d.fondo, 0.16)
    d.linea([(-0.42, 0.42), (0.42, -0.42)], ancho=0.07)


def _chatarrero(d):
    # Un engranaje.
    dientes = 8
    puntos = []
    for i in range(dientes * 4):
        a = math.radians(i * 360 / (dientes * 4))
        r = 0.44 if (i % 4) in (1, 2) else 0.32
        puntos.append((r * math.cos(a), r * math.sin(a)))
    d.poligono(puntos)
    d.circulo(0, 0, 0.13, d.fondo)


def _libertad(d):
    # El cohete (el de la rama).
    d.poligono([(-0.16, 0.0), (-0.34, 0.32), (-0.16, 0.24)])
    d.poligono([(0.16, 0.0), (0.34, 0.32), (0.16, 0.24)])
    d.poligono([(0, -0.47), (0.16, -0.18), (0.16, 0.24), (-0.16, 0.24), (-0.16, -0.18)])
    d.circulo(0, -0.08, 0.08, d.fondo)
    d.poligono([(-0.1, 0.3), (0.1, 0.3), (0, 0.48)])


def _todos_a_bordo(d):
    # La cápsula de escape, con tres ventanas (una por compañero) y su fuego.
    d.poligono([(0, -0.48), (0.2, -0.24), (0.2, 0.26), (-0.2, 0.26), (-0.2, -0.24)])
    d.poligono([(-0.2, 0.06), (-0.36, 0.34), (-0.2, 0.26)])
    d.poligono([(0.2, 0.06), (0.36, 0.34), (0.2, 0.26)])
    for y in (-0.2, -0.02, 0.16):
        d.circulo(0, y, 0.065, d.fondo)
    d.poligono([(-0.12, 0.3), (0.12, 0.3), (0.06, 0.4), (0, 0.48), (-0.06, 0.4)], d.tono(0.35))


def _nadie_me_vio(d):
    # Un ojo cerrado con pestañas.
    d.arco(0, -0.26, 0.42, 200, 340)
    for x in (-0.26, 0, 0.26):
        y = -0.26 + 0.42 * math.sin(math.acos(max(-1, min(1, x / 0.42))))
        d.linea([(x, y), (x * 1.25, y + 0.14)], ancho=0.06)


# -- NEXUS ----------------------------------------------------------------------------------

def _conectado(d):
    # El celular con señal.
    d.rect(-0.22, -0.44, 0.44, 0.88, ancho=0.07, radio=0.08)
    d.rect(-0.14, -0.32, 0.28, 0.56, d.tono(0.45))
    d.circulo(0, 0.35, 0.04)
    for r in (0.1, 0.18):
        d.arco(0, 0.06, r, 45, 135, ancho=0.05)
    d.circulo(0, 0.06, 0.035)


def _fact_checker(d):
    # Un globo de mensaje con una palomita.
    d.rect(-0.44, -0.38, 0.88, 0.62, radio=0.14)
    d.poligono([(-0.24, 0.2), (-0.3, 0.44), (-0.02, 0.2)])
    d.palomita(0, -0.07, 0.18, d.fondo, 0.09)


def _perfil_bajo(d):
    # Una cámara con las esquinas de recorte.
    d.rect(-0.38, -0.2, 0.76, 0.5, radio=0.07)
    d.rect(-0.14, -0.3, 0.28, 0.12, radio=0.03)
    d.circulo(0, 0.05, 0.16, d.fondo)
    d.circulo(0, 0.05, 0.09)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x, y = sx * 0.48, sy * 0.44
        d.linea([(x, y - sy * 0.14), (x, y), (x - sx * 0.14, y)], ancho=0.05)


def _planos(d):
    # Una hoja de planos con su cuadrícula y la cápsula dibujada.
    d.rect(-0.38, -0.42, 0.76, 0.84, radio=0.04)
    for i in range(1, 4):
        d.linea([(-0.38 + 0.19 * i, -0.4), (-0.38 + 0.19 * i, 0.4)], d.tono(0.55), 0.025)
        d.linea([(-0.36, -0.42 + 0.21 * i), (0.36, -0.42 + 0.21 * i)], d.tono(0.55), 0.025)
    d.elipse(-0.22, -0.12, 0.44, 0.26, d.fondo, ancho=0.05)


def _cazador_de_bots(d):
    # La cabeza de un robot en la mira.
    d.rect(-0.22, -0.18, 0.44, 0.36, radio=0.06)
    d.linea([(0, -0.18), (0, -0.3)], ancho=0.04)
    d.circulo(0, -0.31, 0.04)
    d.rect(-0.14, -0.08, 0.09, 0.09, d.fondo)
    d.rect(0.05, -0.08, 0.09, 0.09, d.fondo)
    d.rect(-0.1, 0.07, 0.2, 0.04, d.fondo)
    d.circulo(0, 0, 0.42, ancho=0.05)
    for x0, y0, x1, y1 in ((-0.48, 0, -0.34, 0), (0.34, 0, 0.48, 0), (0, -0.48, 0, -0.42), (0, 0.34, 0, 0.48)):
        d.linea([(x0, y0), (x1, y1)], ancho=0.05)


def _perfil_robado(d):
    # Una ficha de perfil con un antifaz.
    d.rect(-0.42, -0.34, 0.84, 0.68, ancho=0.06, radio=0.08)
    d.persona(-0.14, 0.04, 0.4)
    d.rect(-0.28, -0.17, 0.28, 0.08, d.fondo, radio=0.03)
    for y in (-0.12, 0.02, 0.16):
        d.linea([(0.1, y), (0.32, y)], ancho=0.05)


# -- Equipo ---------------------------------------------------------------------------------

def _una_mano(d):
    # Una mano abierta.
    d.rect(-0.22, -0.06, 0.42, 0.42, radio=0.12)
    for i, alto in enumerate((0.36, 0.44, 0.42, 0.34)):
        x = -0.22 + i * 0.105
        d.rect(x, 0.04 - alto, 0.09, alto + 0.1, radio=0.045)
    d.poligono([(-0.2, 0.06), (-0.42, -0.1), (-0.46, -0.04), (-0.24, 0.24)])
    d.circulo(-0.44, -0.07, 0.045)


def _nadie_atras(d):
    # Los barrotes de la celda, uno doblado para salir.
    d.rect(-0.4, -0.42, 0.8, 0.84, ancho=0.07, radio=0.05)
    for x in (-0.2, 0.2):
        d.linea([(x, -0.4), (x, 0.4)])
    d.linea([(0, -0.4), (0, -0.12), (0.1, 0.0), (0, 0.12), (0, 0.4)])
    d.persona(-0.0, 0.1, 0.2, d.tono(0.45))


def _segunda_oportunidad(d):
    # Un corazón con una cruz de "+1".
    d.circulo(-0.17, -0.1, 0.22)
    d.circulo(0.17, -0.1, 0.22)
    d.poligono([(-0.38, -0.02), (0.38, -0.02), (0, 0.42)])
    d.rect(-0.03, -0.24, 0.07, 0.3, d.fondo)
    d.rect(-0.14, -0.13, 0.29, 0.07, d.fondo)


def _trabajo_en_equipo(d):
    # Dos personas bajo el marco de la puerta para dos.
    d.linea([(-0.44, 0.44), (-0.44, -0.4), (0.44, -0.4), (0.44, 0.44)], d.tono(0.4), 0.06)
    d.persona(-0.18, 0.14, 0.4)
    d.persona(0.18, 0.14, 0.4)


def _rescate(d):
    # Un salvavidas.
    d.circulo(0, 0, 0.42)
    d.circulo(0, 0, 0.2, d.fondo)
    for a in (45, 135, 225, 315):
        r = math.radians(a)
        d.linea([(0.2 * math.cos(r), 0.2 * math.sin(r)), (0.42 * math.cos(r), 0.42 * math.sin(r))],
                d.fondo, 0.1)


def _medico(d):
    # La cruz de primeros auxilios en un botiquín.
    d.rect(-0.42, -0.3, 0.84, 0.66, radio=0.08)
    d.rect(-0.14, -0.42, 0.28, 0.14, ancho=0.06, radio=0.04)
    d.rect(-0.07, -0.2, 0.14, 0.46, d.fondo)
    d.rect(-0.23, -0.04, 0.46, 0.14, d.fondo)


# -- Nave -----------------------------------------------------------------------------------

def _a_oscuras(d):
    # Una luna menguante con estrellitas.
    d.circulo(-0.04, 0.02, 0.36)
    d.circulo(0.14, -0.08, 0.3, d.fondo)
    d.estrella(0.3, 0.22, 0.09, 0.035, 4)
    d.estrella(0.36, -0.34, 0.06, 0.025, 4)


def _hagase_la_luz(d):
    # Un bombillo encendido.
    d.circulo(0, -0.08, 0.26)
    d.poligono([(-0.18, 0.06), (0.18, 0.06), (0.12, 0.22), (-0.12, 0.22)])
    d.rect(-0.12, 0.24, 0.24, 0.06)
    d.rect(-0.09, 0.32, 0.18, 0.06)
    d.linea([(-0.06, -0.06), (0, 0.04), (0.06, -0.06)], d.fondo, 0.04)
    for a in (150, 110, 70, 30):
        r = math.radians(a)
        d.linea([(0.33 * math.cos(r), -0.08 - 0.33 * math.sin(r)), (0.45 * math.cos(r), -0.08 - 0.45 * math.sin(r))],
                ancho=0.05)


def _electricista(d):
    # Un rayo con un cronómetro.
    d.circulo(0.18, 0.18, 0.24, ancho=0.06)
    d.linea([(0.18, 0.18), (0.18, 0.04)], ancho=0.05)
    d.linea([(0.18, 0.18), (0.28, 0.22)], ancho=0.05)
    d.rect(0.13, -0.12, 0.1, 0.05)
    d.poligono([(-0.04, -0.47), (-0.36, 0.02), (-0.16, 0.02), (-0.26, 0.42), (0.06, -0.12), (-0.12, -0.12)])


def _luz_salvadora(d):
    # La caja de fusibles con la palanca arriba.
    d.rect(-0.36, -0.42, 0.72, 0.84, ancho=0.07, radio=0.06)
    d.rect(-0.08, -0.14, 0.16, 0.36, d.tono(0.4), radio=0.04)
    d.linea([(0, 0.0), (0.2, -0.3)], ancho=0.08)
    d.circulo(0.2, -0.3, 0.07)
    d.circulo(-0.2, -0.28, 0.05)
    d.circulo(-0.2, 0.28, 0.05)


def _sin_miedo(d):
    # Un escudo con una estrella.
    d.poligono([(0, -0.46), (0.38, -0.3), (0.34, 0.08), (0, 0.46), (-0.34, 0.08), (-0.38, -0.3)])
    d.estrella(0, -0.02, 0.2, 0.09, 5, d.fondo)


def _ojos_en_la_oscuridad(d):
    # Dos ojos que brillan en la oscuridad.
    for lado in (-1, 1):
        d.poligono([(lado * 0.42, -0.12), (lado * 0.08, -0.02), (lado * 0.12, 0.12), (lado * 0.38, 0.06)])
        d.elipse(lado * 0.24 - 0.03, -0.06, 0.06, 0.12, d.fondo)


def _no_parpadees(d):
    # Una linterna con su haz.
    d.poligono([(-0.46, 0.3), (-0.3, 0.46), (-0.08, 0.24), (-0.24, 0.08)])
    d.poligono([(-0.24, 0.08), (-0.08, 0.24), (0.0, 0.22), (-0.22, 0.0)])
    d.poligono([(-0.18, -0.04), (0.04, 0.18), (0.46, 0.0), (0.0, -0.46)], d.tono(0.55))
    d.linea([(-0.18, -0.04), (0.0, -0.46)], ancho=0.04)
    d.linea([(0.04, 0.18), (0.46, 0.0)], ancho=0.04)


# -- Aliens ---------------------------------------------------------------------------------

def _primer_encuentro(d):
    d.cabeza_alien(0, -0.02, 0.68)


def _agotalo(d):
    # Una batería casi vacía.
    d.rect(-0.42, -0.2, 0.76, 0.4, ancho=0.07, radio=0.06)
    d.rect(0.34, -0.09, 0.08, 0.18, radio=0.02)
    d.rect(-0.32, -0.1, 0.14, 0.2)
    d.poligono([(0.1, -0.44), (-0.02, -0.26), (0.06, -0.26), (-0.02, -0.12), (0.16, -0.32), (0.08, -0.32)])


def _apagado(d):
    # El símbolo de apagar.
    d.arco(0, 0.03, 0.36, 120, 420, ancho=0.09, pasos=30)
    d.linea([(0, -0.46), (0, -0.04)], ancho=0.1)


def _por_aqui_no(d):
    # Prohibido el paso.
    d.circulo(0, 0, 0.44)
    d.rect(-0.3, -0.08, 0.6, 0.16, d.fondo, radio=0.03)


def _titiritero(d):
    # La cruz del titiritero con sus hilos.
    d.linea([(-0.4, -0.3), (0.4, -0.3)], ancho=0.09)
    d.linea([(0, -0.46), (0, -0.14)], ancho=0.09)
    for x, y in ((-0.36, 0.22), (0.0, 0.36), (0.36, 0.22)):
        d.linea([(x if x else 0, -0.3 if x else -0.14), (x, y)], ancho=0.03)
        d.circulo(x, y + 0.04, 0.06)


def _canto_de_sirena(d):
    # Dos notas musicales.
    d.elipse(-0.38, 0.18, 0.24, 0.18)
    d.elipse(0.1, 0.08, 0.24, 0.18)
    d.linea([(-0.16, 0.26), (-0.16, -0.32)], ancho=0.06)
    d.linea([(0.32, 0.16), (0.32, -0.42)], ancho=0.06)
    d.poligono([(-0.18, -0.36), (0.34, -0.46), (0.34, -0.3), (-0.18, -0.2)])


def _jardinero(d):
    # Un brote: tallo y dos hojas.
    d.linea([(0, 0.4), (0, -0.06)], ancho=0.07)
    d.poligono([(0, -0.02), (-0.18, -0.24), (-0.44, -0.24), (-0.3, -0.04), (-0.1, 0.02)])
    d.poligono([(0, -0.12), (0.12, -0.36), (0.42, -0.44), (0.34, -0.18), (0.1, -0.06)])
    d.elipse(-0.3, 0.34, 0.6, 0.14, d.tono(0.4))


def _buen_provecho(d):
    # Una fruta con su hoja.
    d.circulo(-0.12, 0.1, 0.3)
    d.circulo(0.12, 0.1, 0.3)
    d.circulo(-0.14, 0.0, 0.08, d.tono(0.35))
    d.linea([(0, -0.18), (0.04, -0.38)], ancho=0.06)
    d.poligono([(0.04, -0.3), (0.2, -0.44), (0.38, -0.38), (0.2, -0.26)])


def _conoce_a_tu_enemigo(d):
    # Un libro abierto (el bestiario) con un alien en una página.
    d.poligono([(0, -0.3), (-0.2, -0.38), (-0.46, -0.32), (-0.46, 0.34), (-0.2, 0.28), (0, 0.36)])
    d.poligono([(0, -0.3), (0.2, -0.38), (0.46, -0.32), (0.46, 0.34), (0.2, 0.28), (0, 0.36)])
    d.linea([(0, -0.3), (0, 0.36)], d.fondo, 0.04)
    for y in (-0.18, -0.06, 0.06, 0.18):
        d.linea([(-0.38, y), (-0.1, y - 0.02)], d.fondo, 0.035)
    d.cabeza_alien(0.23, 0.0, 0.3, d.fondo, d.color)


# -- Cambiaformas ---------------------------------------------------------------------------

def _cara_a_cara(d):
    # La cara partida (la de la rama).
    d.circulo(0, 0, 0.42)
    pygame.draw.circle(d.sup, d.fondo, [int(v) for v in d.p(0, 0)], d.r(0.42) - d.g,
                       draw_top_right=True, draw_bottom_right=True)
    d.circulo(-0.17, -0.06, 0.07, d.fondo)
    d.circulo(0.17, -0.06, 0.07)
    d.linea([(-0.28, 0.17), (-0.06, 0.2)], d.fondo)
    d.linea([(0.06, 0.2), (0.28, 0.14)])


def _sobreviviente(d):
    # La línea del pulso sobre un corazón.
    d.circulo(-0.17, -0.08, 0.22, d.tono(0.45))
    d.circulo(0.17, -0.08, 0.22, d.tono(0.45))
    d.poligono([(-0.38, 0.0), (0.38, 0.0), (0, 0.42)], d.tono(0.45))
    d.linea([(-0.48, 0.04), (-0.2, 0.04), (-0.1, -0.24), (0.02, 0.3), (0.12, -0.04), (0.2, 0.04), (0.48, 0.04)],
            ancho=0.07)


def _en_manada(d):
    # Tres personas juntas.
    d.persona(-0.26, 0.04, 0.34, d.tono(0.35))
    d.persona(0.26, 0.04, 0.34, d.tono(0.35))
    d.persona(0, 0.14, 0.42)


def _no_me_enganas(d):
    # Un antifaz tachado.
    d.poligono([(-0.44, -0.16), (-0.1, -0.2), (0, -0.1), (0.1, -0.2), (0.44, -0.16), (0.4, 0.08),
                (0.16, 0.18), (0, 0.06), (-0.16, 0.18), (-0.4, 0.08)])
    d.elipse(-0.32, -0.1, 0.18, 0.12, d.fondo)
    d.elipse(0.14, -0.1, 0.18, 0.12, d.fondo)
    d.linea([(-0.42, 0.42), (0.42, -0.42)], d.fondo, 0.15)
    d.linea([(-0.42, 0.42), (0.42, -0.42)], ancho=0.07)


def _lobo_con_piel_de_oveja(d):
    # La cabeza de un lobo asomándose bajo la lana.
    d.poligono([(-0.3, -0.06), (-0.34, -0.46), (-0.08, -0.2)])
    d.poligono([(0.3, -0.06), (0.34, -0.46), (0.08, -0.2)])
    d.poligono([(-0.32, -0.16), (0.32, -0.16), (0.24, 0.16), (0, 0.44), (-0.24, 0.16)])
    d.poligono([(-0.2, -0.04), (-0.06, 0.0), (-0.18, 0.06)], d.fondo)
    d.poligono([(0.2, -0.04), (0.06, 0.0), (0.18, 0.06)], d.fondo)
    d.circulo(0, 0.3, 0.06, d.fondo)
    for x in (-0.36, -0.18, 0, 0.18, 0.36):
        d.circulo(x, -0.2, 0.1, d.tono(0.3))


# -- Caso -----------------------------------------------------------------------------------

def _algo_no_cuadra(d):
    # Un signo de pregunta.
    d.arco(0, -0.16, 0.2, 160, -60, ancho=0.11)
    d.linea([(0.1, -0.0), (0, 0.06), (0, 0.18)], ancho=0.11)
    d.circulo(0, 0.36, 0.07)


def _evidencia(d):
    # Una huella digital.
    for i, r in enumerate((0.08, 0.17, 0.26, 0.35)):
        d.arco(0, 0.08, r, 200 - i * 6, -20 + i * 6, ancho=0.05)
    d.linea([(-0.08, 0.08), (-0.1, 0.38)], ancho=0.05)
    d.linea([(0.08, 0.08), (0.1, 0.3)], ancho=0.05)


def _caso_cerrado(d):
    # El mazo del juez.
    d.poligono([(-0.32, -0.26), (-0.06, -0.48), (0.08, -0.32), (-0.18, -0.1)])
    d.linea([(-0.06, -0.24), (0.34, 0.16)], ancho=0.09)
    d.rect(-0.38, 0.26, 0.56, 0.12, radio=0.03)
    d.rect(-0.3, 0.18, 0.4, 0.1, radio=0.02)


def _corazonada(d):
    # Una nube de pensamiento con un "!".
    for x, y, r in ((-0.18, -0.08, 0.2), (0.06, -0.18, 0.24), (0.24, -0.02, 0.18), (0.0, 0.04, 0.22)):
        d.circulo(x, y, r)
    d.circulo(-0.3, 0.3, 0.07)
    d.circulo(-0.42, 0.42, 0.045)
    d.rect(0.0, -0.3, 0.08, 0.22, d.fondo, radio=0.03)
    d.circulo(0.04, 0.03, 0.045, d.fondo)


def _acusacion_falsa(d):
    # Una señal de advertencia.
    d.poligono([(0, -0.44), (0.46, 0.38), (-0.46, 0.38)])
    d.rect(-0.04, -0.16, 0.09, 0.32, d.fondo, radio=0.03)
    d.circulo(0, 0.26, 0.055, d.fondo)


# -- Los niños y el baúl --------------------------------------------------------------------

def _cepo(d):
    # El cepo, abierto: el aro con dientes y el plato del centro.
    d.circulo(0, 0.04, 0.42, ancho=0.08)
    for i in range(10):
        a = math.pi * 2 * i / 10
        x, y = math.cos(a), math.sin(a) * 0.9
        d.poligono([(x * 0.36, 0.04 + y * 0.36), (x * 0.18 + y * 0.07, 0.04 + y * 0.18 - x * 0.07),
                    (x * 0.18 - y * 0.07, 0.04 + y * 0.18 + x * 0.07)])
    d.circulo(0, 0.04, 0.1)


def _detras_de_la_pared(d):
    # La puerta partida en dos, con la luz saliendo por la rendija.
    d.rect(-0.42, -0.44, 0.34, 0.88, radio=0.04)
    d.rect(0.08, -0.44, 0.34, 0.88, radio=0.04)
    d.poligono([(-0.06, -0.44), (0.06, -0.44), (0.2, 0.44), (-0.2, 0.44)], d.tono(0.55))


def _eran_de_ellos(d):
    # La mochila.
    d.rect(-0.3, -0.26, 0.6, 0.7, radio=0.14)
    d.arco(0, -0.26, 0.16, 180, 0, ancho=0.06)
    d.rect(-0.2, 0.12, 0.4, 0.2, d.fondo, radio=0.05)
    d.linea([(-0.2, 0.2), (0.2, 0.2)], ancho=0.04)


def _llamadas_perdidas(d):
    # Un celular con la burbujita roja de las llamadas.
    d.rect(-0.24, -0.44, 0.48, 0.88, radio=0.08)
    d.rect(-0.18, -0.34, 0.36, 0.62, d.fondo, radio=0.03)
    d.circulo(0, 0.36, 0.04, d.fondo)
    d.circulo(0.24, -0.38, 0.16)
    d.circulo(0.24, -0.38, 0.1, d.fondo)
    d.circulo(0.24, -0.38, 0.05)


def _demasiado_tarde(d):
    # El monitor con la línea plana.
    d.rect(-0.44, -0.32, 0.88, 0.6, radio=0.06)
    d.rect(-0.36, -0.24, 0.72, 0.44, d.fondo, radio=0.03)
    d.linea([(-0.3, -0.02), (-0.12, -0.02), (-0.06, -0.14), (0.0, -0.02), (0.3, -0.02)], ancho=0.05)
    d.rect(-0.16, 0.3, 0.32, 0.1)


def _lo_vimos(d):
    # Un ojo bien abierto.
    n = 16
    arriba = [(-0.46 + 0.92 * i / n, -0.3 * math.sin(math.pi * i / n)) for i in range(n + 1)]
    abajo = [(0.46 - 0.92 * i / n, 0.3 * math.sin(math.pi * i / n)) for i in range(n + 1)]
    d.poligono(arriba + abajo)
    d.circulo(0, 0, 0.2, d.fondo)
    d.circulo(0, 0, 0.1)


def _no_los_dejamos(d):
    # Una persona grande abrazando a una chica.
    d.persona(-0.12, 0.08, 0.6, d.tono(0.3))
    d.persona(0.18, 0.2, 0.38)


def _letra_pequena(d):
    # Una nota con una lupa encima.
    d.rect(-0.42, -0.4, 0.56, 0.72, radio=0.04)
    for y in (-0.26, -0.14, -0.02):
        d.linea([(-0.34, y), (0.04, y)], d.fondo, 0.035)
    d.circulo(0.12, 0.1, 0.2, d.fondo)
    d.circulo(0.12, 0.1, 0.2, ancho=0.07)
    d.linea([(0.26, 0.24), (0.44, 0.42)], ancho=0.1)


def _ellos_primero(d):
    # Un agente con los brazos abiertos, tapando, y un niño que se va detrás.
    d.persona(-0.18, -0.02, 0.32, d.tono(0.4))
    d.persona(0.12, 0.1, 0.56)
    d.linea([(-0.2, 0.2), (0.44, 0.2)], ancho=0.07)


DIBUJOS = {
    "despertar": _despertar,
    "sigiloso": _sigiloso, "pasos_de_gato": _pasos_de_gato, "shhh": _shhh, "fantasma": _fantasma,
    "codigo_roto": _codigo_roto, "a_la_primera": _a_la_primera, "sin_rumbo": _sin_rumbo,
    "sin_rastro": _sin_rastro, "chatarrero": _chatarrero, "libertad": _libertad,
    "todos_a_bordo": _todos_a_bordo, "nadie_me_vio": _nadie_me_vio,
    "conectado": _conectado, "fact_checker": _fact_checker, "perfil_bajo": _perfil_bajo, "planos": _planos,
    "cazador_de_bots": _cazador_de_bots, "perfil_robado": _perfil_robado,
    "una_mano": _una_mano, "nadie_atras": _nadie_atras, "segunda_oportunidad": _segunda_oportunidad,
    "trabajo_en_equipo": _trabajo_en_equipo, "rescate": _rescate, "medico": _medico,
    "a_oscuras": _a_oscuras, "hagase_la_luz": _hagase_la_luz, "electricista": _electricista,
    "luz_salvadora": _luz_salvadora, "sin_miedo": _sin_miedo, "ojos_en_la_oscuridad": _ojos_en_la_oscuridad,
    "no_parpadees": _no_parpadees,
    "primer_encuentro": _primer_encuentro, "agotalo": _agotalo, "apagado": _apagado,
    "por_aqui_no": _por_aqui_no, "titiritero": _titiritero, "canto_de_sirena": _canto_de_sirena,
    "jardinero": _jardinero, "buen_provecho": _buen_provecho, "conoce_a_tu_enemigo": _conoce_a_tu_enemigo,
    "cara_a_cara": _cara_a_cara, "sobreviviente": _sobreviviente, "en_manada": _en_manada,
    "no_me_enganas": _no_me_enganas, "lobo_con_piel_de_oveja": _lobo_con_piel_de_oveja,
    "algo_no_cuadra": _algo_no_cuadra, "evidencia": _evidencia, "caso_cerrado": _caso_cerrado,
    "corazonada": _corazonada, "acusacion_falsa": _acusacion_falsa,
    "cepo": _cepo, "detras_de_la_pared": _detras_de_la_pared, "eran_de_ellos": _eran_de_ellos,
    "llamadas_perdidas": _llamadas_perdidas, "demasiado_tarde": _demasiado_tarde, "lo_vimos": _lo_vimos,
    "no_los_dejamos": _no_los_dejamos, "letra_pequena": _letra_pequena, "ellos_primero": _ellos_primero,
}


def dibujar(sup, clave, centro, s, color, fondo):
    """Dibuja el ícono del logro `clave`. False si no tiene uno propio."""
    funcion = DIBUJOS.get(clave)
    if funcion is None:
        return False
    funcion(_Lienzo(sup, centro, s, color, fondo))
    return True
