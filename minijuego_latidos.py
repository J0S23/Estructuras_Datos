"""Minijuego de calmar los latidos, cuando un alien revisa tu escondite.

Hay dos barras:

- **La de timing**: una aguja va y viene de lado a lado, y hay una franja
  verde. Presionar la tecla de interactuar con la aguja dentro de la franja es
  un acierto.
- **La de amenaza** (al lado): qué tan cerca está el alien de abrir el
  escondite. Sube sola todo el tiempo y SOLO baja con un acierto. Si llega
  arriba, el alien entra y te atrapa; si la bajas hasta cero, el alien se
  rinde y se va.

Un fallo sube la amenaza un poco: si no, apretar la tecla sin parar ganaría
siempre. El pulso del jugador también entra: entre más alto, más angosta la
franja y más rápida la aguja; cada acierto lo baja y cada fallo lo sube. Por
eso "calmar los latidos" es literalmente lo que te salva.

Esta clase solo tiene la lógica (nada de pygame), así que se prueba sin
ventana. La dibuja screens/paneles.render_minijuego.
"""

import random


# Calibrado con una simulación de jugadores que presionan con error de timing:
# alguien atento gana en unos 5-9 s; alguien que va tarde o se pone nervioso
# (pulso alto = aguja rápida y franja angosta) pierde. Para la feria conviene
# que se pueda ganar pero que asuste. Si se siente muy fácil o muy difícil, se
# toca aquí y nada más.
AMENAZA_INICIAL = 50.0
AMENAZA_SUBE_POR_S = 7.0
AMENAZA_POR_ACIERTO = 14.0
AMENAZA_POR_FALLO = 7.0

PULSO_POR_ACIERTO = 12.0
PULSO_POR_FALLO = 6.0

ANCHO_ZONA_CALMADO = 0.28     # ancho de la franja verde con el pulso en 0
ANCHO_ZONA_PANICO = 0.12      # ...y con el pulso en 100
VELOCIDAD_CALMADO = 0.55      # barridos por segundo con el pulso en 0
VELOCIDAD_PANICO = 1.0        # ...y con el pulso en 100

DURACION_DESTELLO_MS = 280


class MinijuegoLatidos:
    def __init__(self, pulso, alien=None, escondite=None, aleatorio=None):
        self.alien = alien
        self.escondite = escondite
        self.aleatorio = aleatorio or random.Random()

        self.amenaza = AMENAZA_INICIAL
        self.aguja = 0.0
        self.sentido = 1
        self.resultado = None          # None mientras dura, "calmado" o "atrapado"
        self.aciertos = 0
        self.fallos = 0
        self.destello = None           # "acierto" / "fallo", para el dibujo
        self.destello_ms = 0

        self.ancho_zona = ANCHO_ZONA_CALMADO
        self.velocidad = VELOCIDAD_CALMADO
        self.centro_zona = 0.5
        self.ajustar_al_pulso(pulso)
        self._mover_zona()

    # -- Estado ---------------------------------------------------------------------

    @property
    def terminado(self):
        return self.resultado is not None

    @property
    def zona(self):
        """(inicio, fin) de la franja verde, de 0 a 1."""
        mitad = self.ancho_zona / 2
        return self.centro_zona - mitad, self.centro_zona + mitad

    def aguja_en_zona(self):
        inicio, fin = self.zona
        return inicio <= self.aguja <= fin

    def ajustar_al_pulso(self, pulso):
        t = max(0.0, min(1.0, pulso / 100))
        self.ancho_zona = ANCHO_ZONA_CALMADO + (ANCHO_ZONA_PANICO - ANCHO_ZONA_CALMADO) * t
        self.velocidad = VELOCIDAD_CALMADO + (VELOCIDAD_PANICO - VELOCIDAD_CALMADO) * t

    def _mover_zona(self):
        """La franja cambia de sitio en cada acierto, para que no se memorice."""
        mitad = self.ancho_zona / 2
        self.centro_zona = self.aleatorio.uniform(mitad + 0.05, 1 - mitad - 0.05)

    # -- Frame ----------------------------------------------------------------------

    def actualizar(self, dt):
        if self.terminado:
            return
        segundos = dt / 1000
        self.destello_ms = max(0, self.destello_ms - dt)

        # La aguja rebota de punta a punta.
        self.aguja += self.sentido * self.velocidad * segundos
        if self.aguja >= 1:
            self.aguja, self.sentido = 2 - self.aguja, -1
        elif self.aguja <= 0:
            self.aguja, self.sentido = -self.aguja, 1

        self.amenaza = min(100.0, self.amenaza + AMENAZA_SUBE_POR_S * segundos)
        if self.amenaza >= 100:
            self.resultado = "atrapado"

    def presionar(self, jugador=None):
        """El jugador presionó su tecla. Devuelve True si fue un acierto."""
        if self.terminado:
            return False
        acierto = self.aguja_en_zona()
        if acierto:
            self.aciertos += 1
            self.amenaza = max(0.0, self.amenaza - AMENAZA_POR_ACIERTO)
            if jugador is not None:
                jugador.pulso = max(0.0, jugador.pulso - PULSO_POR_ACIERTO)
        else:
            self.fallos += 1
            self.amenaza = min(100.0, self.amenaza + AMENAZA_POR_FALLO)
            if jugador is not None:
                jugador.pulso = min(100.0, jugador.pulso + PULSO_POR_FALLO)

        if jugador is not None:
            self.ajustar_al_pulso(jugador.pulso)
        if acierto:
            self._mover_zona()

        self.destello = "acierto" if acierto else "fallo"
        self.destello_ms = DURACION_DESTELLO_MS

        if self.amenaza <= 0:
            self.resultado = "calmado"
        elif self.amenaza >= 100:
            self.resultado = "atrapado"
        return acierto
