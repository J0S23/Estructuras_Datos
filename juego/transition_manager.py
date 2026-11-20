"""
Gestor de transiciones de pantalla para NEXUS.
Aplica un fade-out seguido de un fade-in al cambiar de pantalla.
Si no hay surface disponible, falla silenciosamente.

Además del fundido a negro de siempre hay tres estilos (`estilo=` en
`request`), solo con los efectos visuales prendidos (juego/efectos.py):
- "glitch": la IA de la nave "se mete" al entrar a la partida: franjas de la
  imagen corridas a los lados, teñidas de cian y magenta, rayas de
  interferencia; se oscurece y vuelve igual.
- "iris": al perder, un círculo negro se cierra sobre el centro (con un aro
  rojo) y se vuelve a abrir sobre las celdas.
- "destello": al escapar, todo se vuelve blanco (el salto de la cápsula) y
  aparece el espacio.
"""

import math
import random

import pygame
from juego.config import TRANSITION_DURATION_MS

# (salida, entrada) en ms de cada estilo.
DURACIONES = {"glitch": (340, 560), "iris": (700, 650), "destello": (520, 950)}


class TransitionManager:
    """
    Aplica fade-out → cambio de pantalla → fade-in en TRANSITION_DURATION_MS ms.

    Uso:
        # Solicitar un cambio con transición:
        game.transitions.request(game, "partida")

        # En el loop principal, antes de flip():
        game.transitions.update(game, dt_ms)
        game.transitions.draw(game.screen)
    """

    def __init__(self):
        self._phase = "idle"      # idle | fade_out | fade_in
        self._elapsed = 0
        self._pending_screen = None
        self._pending_callback = None
        self._overlay = None      # pygame.Surface creada bajo demanda
        self._duration_override = None   # None -> usa TRANSITION_DURATION_MS
        self._estilo = None       # None (fundido) | "glitch" | "iris" | "destello"
        self._capas = {}          # superficies guardadas de los estilos

    @property
    def active(self):
        return self._phase != "idle"

    def is_idle(self):
        return self._phase == "idle"

    def request(self, game, new_screen, callback=None, duration_ms=None, estilo=None):
        """
        Solicita una transición hacia new_screen.
        callback opcional se llama justo al completar el fade-out (antes del fade-in).
        duration_ms anula TRANSITION_DURATION_MS solo para esta transición.
        estilo: None (fundido), "glitch", "iris" o "destello" (ver arriba).
        Si ya hay una transición activa, la ignora.
        """
        if self._phase != "idle":
            return
        from juego import efectos
        self._estilo = estilo if (estilo in DURACIONES and efectos.ACTIVOS) else None
        self._pending_screen = new_screen
        self._pending_callback = callback
        self._duration_override = duration_ms
        self._phase = "fade_out"
        self._elapsed = 0

    def _dur(self):
        if self._duration_override is not None:
            return self._duration_override
        if self._estilo is not None:
            salida, entrada = DURACIONES[self._estilo]
            return salida if self._phase == "fade_out" else entrada
        return TRANSITION_DURATION_MS

    def update(self, game, dt_ms):
        """Avanza la transición. Debe llamarse cada frame."""
        if self._phase == "idle":
            return

        self._elapsed += dt_ms
        dur = self._dur()

        if self._phase == "fade_out" and self._elapsed >= dur:
            if self._pending_screen is not None:
                game.current_screen = self._pending_screen
            if self._pending_callback:
                self._pending_callback()
            self._phase = "fade_in"
            self._elapsed = 0

        elif self._phase == "fade_in" and self._elapsed >= dur:
            self._phase = "idle"
            self._elapsed = 0
            self._pending_screen = None
            self._pending_callback = None
            self._duration_override = None
            self._estilo = None

    def draw(self, screen):
        """Dibuja el overlay de transición sobre el screen ya renderizado. Llamar justo antes de pygame.display.flip()."""
        if self._phase == "idle":
            return

        dur = self._dur()
        progress = min(1.0, self._elapsed / max(1, dur))

        if self._estilo is not None:
            # Cuánto "tapa" la transición: 0 = nada, 1 = la pantalla del todo.
            k = progress if self._phase == "fade_out" else 1.0 - progress
            getattr(self, "_dibujar_" + self._estilo)(screen, k)
            return

        if self._phase == "fade_out":
            alpha = int(255 * progress)
        else:  # fade_in
            alpha = int(255 * (1.0 - progress))

        # alfa 0 no tapa nada; 255 es negro entero: un fill. Las dos puntas
        # eran lo más caro: en pygame 2.6 pegar una capa con set_alpha(255)
        # va por un camino lento (~11 ms a 1536x960 en la nube, varias veces
        # más en la laptop), y así quedaba todo el cuadro en que la pantalla
        # está negra del todo (y en las dos pantallas).
        if alpha <= 0:
            return
        if alpha >= 255:
            screen.fill((0, 0, 0))
            return

        w, h = screen.get_size()
        if self._overlay is None or self._overlay.get_size() != (w, h):
            self._overlay = pygame.Surface((w, h))
            self._overlay.fill((0, 0, 0))

        self._overlay.set_alpha(alpha)
        screen.blit(self._overlay, (0, 0))

    # -- Estilos ---------------------------------------------------------------------

    def _velo(self, screen, alpha, color=(0, 0, 0)):
        """Una capa de un color con `alpha` (255 = un fill: el camino rápido)."""
        if alpha <= 0:
            return
        if alpha >= 255:
            screen.fill(color)
            return
        clave = ("velo", screen.get_size(), color)
        capa = self._capas.get(clave)
        if capa is None:
            capa = self._capas[clave] = pygame.Surface(screen.get_size())
            capa.fill(color)
        capa.set_alpha(alpha)
        screen.blit(capa, (0, 0))

    def _tinte(self, ancho, color):
        """Una franja de color para sumar (cian o magenta del glitch)."""
        clave = ("tinte", ancho, color)
        capa = self._capas.get(clave)
        if capa is None:
            capa = self._capas[clave] = pygame.Surface((ancho, 90))
            capa.fill(color)
        return capa

    def _dibujar_glitch(self, screen, k):
        """Franjas corridas y teñidas que cambian cada 45 ms, rayas de
        interferencia, y oscuro en el medio (cuando cambia la pantalla)."""
        if k <= 0.02:
            return
        w, h = screen.get_size()
        copia = screen.copy()
        azar = random.Random(int(self._elapsed // 45) + (0 if self._phase == "fade_out" else 999))
        fuerza = min(1.0, k * 1.4)
        for _ in range(int(4 + 12 * fuerza)):
            alto = int(azar.uniform(0.01, 0.07) * h)
            y = azar.randrange(0, max(1, h - alto))
            dx = int(azar.uniform(-1, 1) * fuerza * w * 0.06)
            screen.blit(copia, (dx, y), pygame.Rect(0, y, w, alto))
            if azar.random() < 0.6:
                color = (0, 60, 80) if azar.random() < 0.5 else (70, 0, 80)
                screen.blit(self._tinte(w, color), (0, y), pygame.Rect(0, 0, w, min(alto, 90)),
                            special_flags=pygame.BLEND_RGB_ADD)
        # Unas rayas finas claras (interferencia).
        for _ in range(int(3 + 8 * fuerza)):
            y = azar.randrange(0, h)
            x0 = azar.randrange(0, w)
            largo = int(azar.uniform(0.1, 0.5) * w)
            v = int(120 + 120 * azar.random())
            pygame.draw.line(screen, (v, v, min(255, v + 20)), (x0, y), (min(w, x0 + largo), y), 1)
        self._velo(screen, int(255 * max(0.0, (k - 0.35) / 0.65) ** 1.4))

    def _dibujar_iris(self, screen, k):
        """Un círculo negro que se cierra (o se abre) sobre el centro, con un
        aro rojo en el borde."""
        w, h = screen.get_size()
        radio_max = math.hypot(w, h) / 2 + 4
        u = 1 - (1 - k) ** 2 if self._phase == "fade_out" else k ** 0.8
        radio = int(radio_max * (1 - u))
        if radio <= 0:
            screen.fill((0, 0, 0))
            return
        clave = ("iris", (w, h))
        capa = self._capas.get(clave)
        if capa is None:
            capa = self._capas[clave] = pygame.Surface((w, h))
            capa.set_colorkey((255, 0, 255))
        capa.fill((0, 0, 0))
        centro = (w // 2, h // 2)
        pygame.draw.circle(capa, (255, 0, 255), centro, radio)
        screen.blit(capa, (0, 0))
        if radio < radio_max - 4:
            pygame.draw.circle(screen, (200, 30, 40), centro, radio + 3, 4)
            pygame.draw.circle(screen, (90, 10, 20), centro, radio + 9, 3)

    def _dibujar_destello(self, screen, k):
        """Todo se vuelve blanco y del blanco sale la pantalla nueva."""
        if self._phase == "fade_out":
            self._velo(screen, int(255 * k ** 1.6), (255, 255, 255))
        else:
            self._velo(screen, int(255 * k ** 1.3), (255, 255, 255))
