"""Que se sienta: el latido que se oye, los pasos del alien y el susto.

No cambia nada de las reglas del juego; solo hace que lo que ya pasa se oiga y
se vea más fuerte:

- **Latido**: suena al ritmo del jugador más asustado (el de pulso más alto).
  Tranquilo apenas se oye; en pánico, fuerte y rápido. Un solo latido para
  todos, porque cuatro corazones a la vez serían ruido.
- **Pasos del alien**: se oyen cuando un alien camina cerca de alguien, más
  fuerte y más seguido entre más cerca y si está persiguiendo.
- **Susto**: al ser atrapado, golpe de sonido, destello rojo, la pantalla de ese
  jugador tiembla y aparece la cara del alien. Medio segundo, lo justo.

Los sonidos se piden por nombre a audio_manager; si no hay audio, no pasa nada.
"""

import math
import random

from juego.audio_manager import audio_manager


DURACION_SUSTO_MS = 750
ALCANCE_PASOS = 650          # a qué distancia se empiezan a oír los pasos
INTERVALO_PASO_MS = 520
INTERVALO_PASO_PERSIGUE_MS = 340
AMPLITUD_TEMBLOR = 14        # píxeles


def sonar(nombre, volumen=1.0):
    audio_manager.play_sfx(nombre, volumen)


class Ambiente:
    def __init__(self):
        self.fase_latido = 0.0
        self.pasos_ms = {}       # id(alien) -> ms hasta el próximo paso
        self.ultimos = []        # (nombre, volumen) de lo que sonó; lo leen las pruebas

    def sonar(self, nombre, volumen=1.0):
        self.ultimos.append((nombre, round(volumen, 2)))
        del self.ultimos[:-30]
        sonar(nombre, volumen)

    def susto(self, jugador):
        jugador.susto_ms = DURACION_SUSTO_MS
        self.sonar("captura", 1.0)

    def actualizar(self, dt, jugadores, aliens):
        for j in jugadores:
            j.susto_ms = max(0, getattr(j, "susto_ms", 0) - dt)

        libres = [j for j in jugadores if j.puede_moverse and j.preso is None
                  and not getattr(j, "eliminado", False)]
        if libres:
            asustado = max(libres, key=lambda j: j.pulso)
            self.fase_latido += asustado.latidos_por_minuto / 60 * dt / 1000
            if self.fase_latido >= 1:
                self.fase_latido %= 1
                fuerza = max(0.0, min(1.0, (asustado.pulso - 20) / 75))
                self.sonar("latido", 0.12 + 0.88 * fuerza)

        for alien in aliens:
            if alien.accion in ("DESCANSAR", "BUSCAR", "REVISAR_ESCONDITE", "ATRAPAR"):
                continue
            distancia = min((math.dist(alien.centro, j.hitbox.center) for j in libres), default=None)
            if distancia is None or distancia > ALCANCE_PASOS:
                continue
            clave = id(alien)
            self.pasos_ms[clave] = self.pasos_ms.get(clave, 0) - dt
            if self.pasos_ms[clave] <= 0:
                rapido = alien.accion == "PERSEGUIR" or alien.alerta
                self.pasos_ms[clave] = INTERVALO_PASO_PERSIGUE_MS if rapido else INTERVALO_PASO_MS
                self.sonar("paso_alien", 0.15 + 0.85 * (1 - distancia / ALCANCE_PASOS))


def temblor(jugador, tiempo_ms):
    """Desplazamiento de cámara mientras dura el susto (se apaga solo)."""
    restante = getattr(jugador, "susto_ms", 0)
    if restante <= 0:
        return 0, 0
    fuerza = AMPLITUD_TEMBLOR * restante / DURACION_SUSTO_MS
    azar = random.Random(int(tiempo_ms // 30))
    return int(azar.uniform(-fuerza, fuerza)), int(azar.uniform(-fuerza, fuerza))


def dibujar_susto(screen, vista, jugador):
    """Destello rojo y la cara del alien que se acerca, en la mitad del atrapado."""
    import pygame
    restante = getattr(jugador, "susto_ms", 0)
    if restante <= 0:
        return
    t = 1 - restante / DURACION_SUSTO_MS          # 0 al empezar, 1 al terminar
    rojo = pygame.Surface(vista.size, pygame.SRCALPHA)
    rojo.fill((200, 0, 20, int(190 * (1 - t))))
    screen.blit(rojo, vista.topleft)

    # La cara crece rápido y se desvanece.
    lado = int(min(vista.width, vista.height) * (0.45 + 0.5 * min(1, t * 2.5)))
    cara = pygame.Surface((lado, lado), pygame.SRCALPHA)
    alfa = int(255 * (1 - max(0, t - 0.55) / 0.45))
    c = lado // 2
    pygame.draw.ellipse(cara, (112, 214, 120, alfa), (lado * 0.12, lado * 0.05, lado * 0.76, lado * 0.92))
    for lado_ojo in (-1, 1):
        ojo = pygame.Rect(0, 0, int(lado * 0.24), int(lado * 0.32))
        ojo.center = (c + lado_ojo * int(lado * 0.17), int(lado * 0.42))
        pygame.draw.ellipse(cara, (10, 10, 18, alfa), ojo)
        pygame.draw.circle(cara, (255, 40, 40, alfa), (ojo.centerx, ojo.centery + 4), max(2, lado // 40))
    boca = pygame.Rect(0, 0, int(lado * 0.3), int(lado * 0.1))
    boca.center = (c, int(lado * 0.74))
    pygame.draw.ellipse(cara, (20, 40, 25, alfa), boca)
    screen.blit(cara, cara.get_rect(center=vista.center))
