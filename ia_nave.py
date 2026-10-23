"""La IA de la nave: comenta lo que pasa y se burla de los prisioneros.

Habla poco para no cansar: después de cada frase espera unos segundos antes de
decir otra (salvo los eventos importantes, que se dicen igual). Si pasa mucho
rato sin nada, suelta una frase de ambiente. El texto aparece letra por letra
arriba de la pantalla, encima de las dos mitades, con su "voz" de chirridos.

Las frases están en data/ia_nave.py.
"""

import random

import pygame

from data.ia_nave import FRASES
from fuentes import fuente_de_tamano


DURACION_MS = 4800
ENFRIAMIENTO_MS = 9000
SILENCIO_PARA_AMBIENTE_MS = 40000
LETRAS_POR_SEGUNDO = 45

COLOR_IA = (190, 120, 255)
COLOR_TEXTO = (240, 236, 255)


class Narrador:
    def __init__(self, aleatorio=None, al_hablar=None):
        self.rng = aleatorio or random.Random()
        self.al_hablar = al_hablar      # para que suene la "voz" (lo pone el juego)
        self.texto = ""
        self.restante_ms = 0
        self.mostrado_ms = 0
        self.enfriamiento_ms = 0
        self.silencio_ms = 0
        self.dichas = []                # historial, para las pruebas

    @property
    def hablando(self):
        return self.restante_ms > 0

    def decir(self, evento, rol=None, forzar=False):
        """Dice una frase de ese evento. Devuelve True si la dijo."""
        if self.enfriamiento_ms > 0 and not forzar:
            return False
        opciones = FRASES.get(evento)
        if not opciones:
            return False
        texto = self.rng.choice(opciones).replace("{rol}", rol or "")
        self.texto = texto
        self.restante_ms = DURACION_MS
        self.mostrado_ms = 0
        self.enfriamiento_ms = ENFRIAMIENTO_MS
        self.silencio_ms = 0
        self.dichas.append((evento, texto))
        if self.al_hablar is not None:
            self.al_hablar()
        return True

    def actualizar(self, dt):
        self.restante_ms = max(0, self.restante_ms - dt)
        self.mostrado_ms += dt
        self.enfriamiento_ms = max(0, self.enfriamiento_ms - dt)
        self.silencio_ms += dt
        if self.silencio_ms >= SILENCIO_PARA_AMBIENTE_MS:
            self.decir("ambiente")
            self.silencio_ms = 0

    def dibujar(self, screen, bajar=0):
        if not self.hablando:
            return
        from screens.paneles import partir_lineas
        letras = int(self.mostrado_ms / 1000 * LETRAS_POR_SEGUNDO)
        ancho_pantalla = screen.get_width()
        f = fuente_de_tamano(max(14, min(20, ancho_pantalla // 70)))
        f_etiqueta = fuente_de_tamano(max(11, min(14, ancho_pantalla // 100)))

        etiqueta = f_etiqueta.render("IA DE LA NAVE", True, COLOR_IA)
        lineas = partir_lineas(self.texto, f, min(ancho_pantalla - 80, 760))
        ancho = max(f.size(l)[0] for l in lineas)
        ancho = max(ancho, etiqueta.get_width()) + 36
        alto = etiqueta.get_height() + f.get_linesize() * len(lineas) + 22
        caja = pygame.Rect(0, 0, ancho, alto)
        caja.midtop = (ancho_pantalla // 2, 100 + bajar)   # debajo del HUD y de la barra de confianza

        # Letra por letra, línea por línea, como una terminal.
        visibles, quedan = [], letras
        for linea in lineas:
            visibles.append(linea[:max(0, quedan)])
            quedan -= len(linea) + 1

        # Se desvanece en el último medio segundo.
        alfa = 230 if self.restante_ms > 500 else int(230 * self.restante_ms / 500)
        fondo = pygame.Surface(caja.size, pygame.SRCALPHA)
        fondo.fill((20, 10, 34, alfa))
        screen.blit(fondo, caja.topleft)
        borde = pygame.Surface(caja.size, pygame.SRCALPHA)
        pygame.draw.rect(borde, (*COLOR_IA, alfa), borde.get_rect(), 2, border_radius=6)
        screen.blit(borde, caja.topleft)

        etiqueta.set_alpha(alfa)
        screen.blit(etiqueta, (caja.x + 18, caja.y + 8))
        y = caja.y + 12 + etiqueta.get_height()
        for linea in visibles:
            if linea:
                cuerpo = f.render(linea, True, COLOR_TEXTO)
                cuerpo.set_alpha(alfa)
                screen.blit(cuerpo, (caja.x + 18, y))
            y += f.get_linesize()
