"""La IA de la nave, Neila: comenta lo que pasa y se burla de los prisioneros.

Habla poco para no cansar: después de cada frase espera unos segundos antes de
decir otra (salvo los eventos importantes, que se dicen igual). Si pasa mucho
rato sin nada, suelta una frase de ambiente. El texto aparece letra por letra
arriba de la pantalla, encima de las dos mitades, con su "voz" de chirridos.

Las frases están en data/ia_nave.py.
"""

import random

import pygame

from data.ia_nave import FRASES
from juego.fuentes import fuente_de_tamano
from juego import cache_dibujo


DURACION_MS = 4800
ENFRIAMIENTO_MS = 9000
SILENCIO_PARA_AMBIENTE_MS = 40000
LETRAS_POR_SEGUNDO = 45

COLOR_IA = (190, 120, 255)

# Cómo se llama la IA de la nave (sale en su cartel). Antes decía "IA DE LA NAVE".
NOMBRE = "NEILA"
COLOR_TEXTO = (240, 236, 255)


_bordes = {}      # (tamaño, alfa) -> el borde del cartel


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

    def dibujar(self, screen, centro_x=None, arriba=60, ancho_max=None):
        """El cartel, centrado en `centro_x` desde `arriba` y sin pasarse de
        `ancho_max`. Lo pone la app en la columna de lo global
        (celular.columna_avisos): debajo de la barra de confianza y del aviso
        del evento, o en el cuarto cuadro con 3 jugadores."""
        if not self.hablando:
            return
        from screens.paneles import partir_lineas
        letras = int(self.mostrado_ms / 1000 * LETRAS_POR_SEGUNDO)
        ancho_pantalla = screen.get_width()
        if centro_x is None:
            centro_x = ancho_pantalla // 2
        if ancho_max is None:
            ancho_max = min(ancho_pantalla - 80, 760)
        f = fuente_de_tamano(max(14, min(19, ancho_pantalla // 72)))
        f_etiqueta = fuente_de_tamano(max(11, min(13, ancho_pantalla // 110)))

        etiqueta = cache_dibujo.texto(f_etiqueta, NOMBRE, COLOR_IA).copy()
        # Partir el texto en líneas y medirlas: una vez por frase (antes en
        # cada cuadro mientras habla).
        from juego import idioma
        clave = (self.texto, id(f), max(120, ancho_max - 32), idioma.IDIOMA)
        if getattr(self, "_lineas", (None,))[0] != clave:
            lineas = partir_lineas(self.texto, f, clave[2])
            self._lineas = (clave, lineas, max(f.size(l)[0] for l in lineas))
        _, lineas, ancho = self._lineas
        ancho = max(ancho, etiqueta.get_width()) + 32
        alto = etiqueta.get_height() + f.get_linesize() * len(lineas) + 20
        caja = pygame.Rect(0, 0, ancho, alto)
        caja.midtop = (centro_x, arriba)

        # Letra por letra, línea por línea, como una terminal.
        visibles, quedan = [], letras
        for linea in lineas:
            visibles.append(linea[:max(0, quedan)])
            quedan -= len(linea) + 1

        # Se desvanece en el último medio segundo.
        alfa = 230 if self.restante_ms > 500 else int(230 * self.restante_ms / 500)
        from juego import efectos
        if efectos.ACTIVOS:
            self._dibujar_vivo(screen, caja, etiqueta, f, visibles, lineas, alfa)
            return
        # (El fondo y el borde, guardados por tamaño y alfa: antes eran dos
        # superficies nuevas en cada cuadro mientras habla.)
        screen.blit(cache_dibujo.capa(caja.size, (20, 10, 34, alfa)), caja.topleft)
        clave = (tuple(caja.size), alfa)
        borde = _bordes.get(clave)
        if borde is None:
            if len(_bordes) > 64:
                _bordes.clear()
            borde = _bordes[clave] = pygame.Surface(caja.size, pygame.SRCALPHA)
            pygame.draw.rect(borde, (*COLOR_IA, alfa), borde.get_rect(), 2, border_radius=6)
        screen.blit(borde, caja.topleft)

        etiqueta.set_alpha(alfa)
        screen.blit(etiqueta, (caja.x + 16, caja.y + 7))
        y = caja.y + 10 + etiqueta.get_height()
        for linea in visibles:
            if linea:
                # (guardada: las líneas ya completas se repiten cada cuadro)
                cuerpo = cache_dibujo.texto(f, linea, COLOR_TEXTO).copy()
                cuerpo.set_alpha(alfa)
                screen.blit(cuerpo, (caja.x + 16, y))
            y += f.get_linesize()

    # -- Con los efectos visuales: interferencia, onda de voz y cursor ---------------

    def _dibujar_vivo(self, screen, caja, etiqueta, f, visibles, lineas, alfa):
        """El cartel de vidrio de la IA. Al empezar a hablar entra con
        interferencia (se corre, parpadea, rayas); mientras escribe, una onda
        de voz al lado del nombre y un cursor al final del texto. Todo sale de
        `mostrado_ms` (el estado que también recibe la otra laptop)."""
        import math
        from screens import vidrio
        t = self.mostrado_ms
        alfa = max(0, min(230, alfa)) // 23 * 23           # (pocos niveles: se guardan)
        if alfa <= 0:
            return
        entrando = t < 380
        azar = random.Random(int(t // 40))
        if entrando:
            if azar.random() < 0.25:
                return                                   # parpadea
            caja = caja.move(int(azar.uniform(-1, 1) * 6 * (1 - t / 380)), 0)
        vidrio.caja(screen, caja, COLOR_IA, alfa, 8)
        screen.blit(_rayas(caja.size), caja.topleft)
        if entrando:
            for _ in range(4):
                y = caja.y + azar.randrange(4, max(5, caja.height - 4))
                x0 = caja.x + azar.randrange(0, max(1, caja.width // 2))
                pygame.draw.line(screen, (210, 170, 255), (x0, y), (x0 + azar.randrange(20, max(21, caja.width // 2)), y), 1)
        # El nombre (con una copia corrida en cian al entrar) y la onda de voz.
        x_etq, y_etq = caja.x + 16, caja.y + 7
        if entrando:
            fantasma = etiqueta.copy()
            fantasma.fill((0, 255, 255, 120), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(fantasma, (x_etq + 2, y_etq))
        etiqueta.set_alpha(alfa)
        screen.blit(etiqueta, (x_etq, y_etq))
        escribiendo = sum(len(v) for v in visibles) < sum(len(l) for l in lineas)
        x_onda = x_etq + etiqueta.get_width() + 10
        cy = y_etq + etiqueta.get_height() // 2
        for i in range(9):
            if escribiendo:
                alto = 2 + int(abs(math.sin(t / 70 + i * 1.3) * math.sin(t / 190 + i * 0.7)) * 9)
            else:
                alto = 2 + int((1 + math.sin(t / 400 + i)) * 0.8)
            c = tuple(int(v * alfa / 230) for v in COLOR_IA)
            pygame.draw.rect(screen, c, (x_onda + i * 4, cy - alto // 2, 2, alto))
        # El texto.
        y = caja.y + 10 + etiqueta.get_height()
        ultimo = None
        for linea in visibles:
            if linea:
                cuerpo = cache_dibujo.texto(f, linea, COLOR_TEXTO).copy()
                cuerpo.set_alpha(alfa)
                screen.blit(cuerpo, (caja.x + 16, y))
                ultimo = (caja.x + 16 + cuerpo.get_width(), y)
            y += f.get_linesize()
        # El cursor de terminal: fijo mientras escribe, parpadea al terminar.
        if ultimo is None:
            ultimo = (caja.x + 16, caja.y + 10 + etiqueta.get_height())
        if escribiendo or (t // 380) % 2 == 0:
            alto_cursor = f.get_height() - 4
            pygame.draw.rect(screen, tuple(int(v * alfa / 230) for v in COLOR_IA),
                             (ultimo[0] + 2, ultimo[1] + 2, max(3, alto_cursor // 2), alto_cursor))


_capas_rayas = {}


def _rayas(tam):
    """Unas líneas de barrido muy tenues (como una pantalla vieja)."""
    capa = _capas_rayas.get(tam)
    if capa is None:
        if len(_capas_rayas) > 30:
            _capas_rayas.clear()
        capa = pygame.Surface(tam, pygame.SRCALPHA)
        for y in range(3, tam[1] - 3, 3):
            pygame.draw.line(capa, (190, 120, 255, 14), (3, y), (tam[0] - 4, y))
        _capas_rayas[tam] = capa
    return capa
