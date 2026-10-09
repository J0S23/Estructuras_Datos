"""Los aliens: patrullan, ven, oyen latidos y persiguen.

Cada alien hace dos cosas por frame:

1. `percibir()` traduce lo que pasa a su alrededor en respuestas de sí o no
   ("¿ve a un jugador?", "¿oyó un latido?"...).
2. Con esas respuestas recorre el árbol de comportamiento
   (Estructuras/arbol_comportamiento.py) de la raíz a una hoja, y la hoja dice
   qué acción ejecutar en ese frame.

El árbol es el mismo para todos los aliens (es contenido, vive en
data/comportamiento_alien.py); lo que cambia es la ruta de cada uno y lo que
percibe. Cada alien guarda el último camino que recorrió en el árbol para que
la vista del árbol ([B] en partida) lo resalte en vivo.

Para volver a su ruta después de perseguir a alguien, el alien deja un
**rastro**: una pila de puntos por donde pasó desde que salió de la ruta. Al
volver los va sacando de la pila (el último en entrar es el primero en salir),
así que deshace su camino exacto y nunca intenta atravesar una pared para
regresar.

Todavía no hay sprite del alien: se dibuja una figura provisional con formas.
"""

import math

import pygame

from fuentes import fuente_de_tamano


# Velocidades en píxeles por frame a 60 FPS. Los jugadores caminan a 4: el
# alien que persigue es un poco más lento, así que escapar es posible pero
# hay que moverse.
VEL_PATRULLA = 1.7
VEL_INVESTIGAR = 2.4
VEL_PERSEGUIR = 3.3

# Visión: un cono hacia donde mira.
ALCANCE_VISION = 300
MEDIO_ANGULO_VISION = math.radians(38)

DISTANCIA_ATRAPAR = 46
DISTANCIA_REVISAR = 80           # a esta distancia del escondite se pone a revisarlo
ENFRIAMIENTO_ESCONDITE_MS = 7000 # tras rendirse, cuánto ignora ese escondite
DURACION_BUSQUEDA_MS = 3000      # cuánto busca después de perder el rastro
DURACION_DESCANSO_MS = 2500      # cuánto se queda quieto tras atrapar a alguien
SEPARACION_RASTRO = 36           # cada cuánto deja un punto en el rastro
TIEMPO_ATASCADO_MS = 900         # sin avanzar este tiempo = se rinde

ANCHO_HITBOX, ALTO_HITBOX = 34, 20

# Color del cono según lo que está haciendo.
COLOR_CONO = {
    "PATRULLAR": (200, 230, 255),
    "VOLVER": (200, 230, 255),
    "INVESTIGAR": (255, 214, 64),
    "BUSCAR": (255, 214, 64),
    "PERSEGUIR": (240, 70, 60),
    "ATRAPAR": (240, 70, 60),
    "DESCANSAR": (150, 150, 170),
    "REVISAR_ESCONDITE": (240, 70, 60),
}


def _distancia(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class Alien:
    def __init__(self, numero, ruta, arbol):
        """`ruta` es una lista de puntos (x, y) en píxeles del mundo."""
        self.numero = numero
        self.nombre = f"Alien {numero}"
        self.ruta = list(ruta)
        self.arbol = arbol
        self.indice_ruta = 1 % len(self.ruta)

        self.hitbox = pygame.Rect(0, 0, ANCHO_HITBOX, ALTO_HITBOX)
        self.hitbox.center = self.ruta[0]
        self.angulo = 0.0                 # hacia dónde mira, en radianes

        self.accion = "PATRULLAR"
        self.camino = []                  # nodos recorridos en el árbol este frame

        self.objetivo = None              # jugador que está viendo
        self.punto_ruido = None           # a dónde va a investigar
        self.escondite_objetivo = None    # escondite de donde salió el latido
        self.rastro = []                  # pila de puntos para volver a la ruta
        self.busqueda_ms = 0
        self.descanso_ms = 0
        self.aturdido = False             # el descanso viene de un hackeo
        self.atascado_ms = 0
        self.tiempo_ms = 0                # reloj propio, para animaciones

    # -- Percepción ---------------------------------------------------------------

    @property
    def centro(self):
        return self.hitbox.center

    def puede_ver(self, punto, mundo):
        """True si `punto` está dentro del cono y no hay una pared en medio."""
        dx, dy = punto[0] - self.centro[0], punto[1] - self.centro[1]
        distancia = math.hypot(dx, dy)
        if distancia > ALCANCE_VISION:
            return False
        if distancia > 1:
            diferencia = (math.atan2(dy, dx) - self.angulo + math.pi) % (2 * math.pi) - math.pi
            if abs(diferencia) > MEDIO_ANGULO_VISION:
                return False
        return mundo.linea_libre(self.centro, punto)

    @staticmethod
    def escondite_disponible(escondite, alien=None):
        """Si un alien puede ir a revisar este escondite ahora."""
        if escondite.get("enfriamiento_ms", 0) > 0:
            return False
        dueño = escondite.get("revisado_por")
        return dueño is None or dueño is alien

    def percibir(self, jugadores, mundo, escondites=()):
        """Responde las preguntas del árbol con lo que pasa en este frame."""
        visibles = [j for j in jugadores
                    if j.cazable and not j.escondido
                    and self.puede_ver(j.hitbox.center, mundo)]
        self.objetivo = min(visibles, key=lambda j: _distancia(self.centro, j.hitbox.center),
                            default=None)

        if self.objetivo is not None:
            # Lo último que vio: si lo pierde, va a buscar ahí.
            self.punto_ruido = self.objetivo.hitbox.center
        else:
            # Un latido fuerte se oye aunque no haya línea de vista: el pulso de
            # cada jugador decide qué tan lejos llega su ruido.
            for jugador in jugadores:
                if not jugador.cazable:
                    continue
                if _distancia(self.centro, jugador.hitbox.center) > jugador.radio_ruido:
                    continue
                if jugador.escondido:
                    if not self.escondite_disponible(jugador.escondite, self):
                        continue
                    self.escondite_objetivo = jugador.escondite
                self.punto_ruido = jugador.hitbox.center
                break

        # Si va hacia un escondite ocupado (porque lo oyó, o porque vio a
        # alguien meterse ahí), lo recuerda para revisarlo al llegar.
        if self.punto_ruido is not None and self.escondite_objetivo is None:
            for escondite in escondites:
                if (escondite.get("ocupante") is not None
                        and self.escondite_disponible(escondite, self)
                        and escondite["rect"].inflate(60, 60).collidepoint(self.punto_ruido)):
                    self.escondite_objetivo = escondite
                    break
        if self.escondite_objetivo is not None and (
                self.escondite_objetivo.get("ocupante") is None
                or not self.escondite_disponible(self.escondite_objetivo, self)):
            self.escondite_objetivo = None

        al_alcance = (self.objetivo is not None and
                      _distancia(self.centro, self.objetivo.hitbox.center) <= DISTANCIA_ATRAPAR)
        return {
            "recuperandose": self.descanso_ms > 0,
            "ve_jugador": self.objetivo is not None,
            "jugador_al_alcance": al_alcance,
            "oye_ruido": self.punto_ruido is not None,
            "en_escondite": (self.escondite_objetivo is not None and
                             _distancia(self.centro, self.escondite_objetivo["rect"].center)
                             <= DISTANCIA_REVISAR),
            "rastro_reciente": self.busqueda_ms > 0,
            "fuera_de_ruta": bool(self.rastro),
        }

    # -- Frame --------------------------------------------------------------------

    def actualizar(self, dt, mundo, jugadores, al_atrapar=None, escondites=(),
                   al_revisar=None):
        """Percibe, decide con el árbol y ejecuta la acción de la hoja.

        `al_atrapar(jugador, alien)` y `al_revisar(jugador, alien, escondite)`
        los pone el juego: lo que pasa al atrapar a alguien o al empezar a
        revisar un escondite no es asunto del alien.
        """
        self.tiempo_ms += dt
        factor = min(3.0, dt / (1000 / 60)) if dt else 1.0
        self.descanso_ms = max(0, self.descanso_ms - dt)
        if self.descanso_ms == 0:
            self.aturdido = False

        condiciones = self.percibir(jugadores, mundo, escondites)
        self.accion, self.camino = self.arbol.decidir(condiciones)
        self._ejecutar(self.accion, dt, factor, mundo, al_atrapar, al_revisar)

    # -- Lo que les hacen las habilidades de los jugadores ----------------------------

    def aturdir(self, ms):
        """Hackeo del Tecnomante: queda fuera de combate `ms` milisegundos.

        Si estaba revisando un escondite, lo suelta: el juego ve que ya no lo
        revisa y termina el minijuego de quien estaba adentro.
        """
        if self.escondite_objetivo is not None:
            self.rendirse()
        self.descanso_ms = max(self.descanso_ms, ms)
        self.aturdido = True
        self.punto_ruido = None
        self.busqueda_ms = 0

    def oir(self, punto):
        """Un ruido que no viene de un latido: señuelo o señal falsa.

        Si está persiguiendo a alguien, revisando un escondite o fuera de
        combate, no le hace caso: una distracción no le gana a lo que tiene
        enfrente.
        """
        if self.descanso_ms > 0 or self.accion in ("PERSEGUIR", "ATRAPAR", "REVISAR_ESCONDITE"):
            return False
        self.punto_ruido = (int(punto[0]), int(punto[1]))
        self.escondite_objetivo = None
        return True

    def rendirse(self):
        """El jugador ganó el minijuego: deja el escondite en paz un rato."""
        escondite = self.escondite_objetivo
        if escondite is not None:
            escondite["revisado_por"] = None
            escondite["enfriamiento_ms"] = ENFRIAMIENTO_ESCONDITE_MS
        self.escondite_objetivo = None
        self.punto_ruido = None
        self.busqueda_ms = DURACION_BUSQUEDA_MS

    def entrar_al_escondite(self):
        """El jugador perdió el minijuego: el alien abre el escondite."""
        escondite = self.escondite_objetivo
        if escondite is not None:
            escondite["revisado_por"] = None
            escondite["enfriamiento_ms"] = ENFRIAMIENTO_ESCONDITE_MS
        self.escondite_objetivo = None
        self.punto_ruido = None
        self.busqueda_ms = 0
        self.descanso_ms = DURACION_DESCANSO_MS

    def _ejecutar(self, accion, dt, factor, mundo, al_atrapar, al_revisar=None):
        if accion in ("PERSEGUIR", "INVESTIGAR", "BUSCAR", "ATRAPAR", "REVISAR_ESCONDITE"):
            self._dejar_rastro()

        if accion == "DESCANSAR":
            return

        if accion == "REVISAR_ESCONDITE":
            # Se queda frente al escondite mirándolo. La primera vez avisa al
            # juego, que arranca el minijuego del que está adentro; el alien
            # espera aquí hasta que el juego llame a rendirse() o a
            # entrar_al_escondite().
            escondite = self.escondite_objetivo
            centro = escondite["rect"].center
            self.angulo = math.atan2(centro[1] - self.centro[1], centro[0] - self.centro[0])
            if escondite.get("revisado_por") is None:
                escondite["revisado_por"] = self
                if al_revisar is not None:
                    al_revisar(escondite.get("ocupante"), self, escondite)
            return

        if accion == "ATRAPAR":
            if al_atrapar is not None:
                al_atrapar(self.objetivo, self)
            self.descanso_ms = DURACION_DESCANSO_MS
            self.punto_ruido = None
            self.busqueda_ms = 0
            return

        if accion == "PERSEGUIR":
            self.busqueda_ms = DURACION_BUSQUEDA_MS
            self._ir_hacia(self.objetivo.hitbox.center, VEL_PERSEGUIR * factor, dt, mundo)
            return

        if accion == "INVESTIGAR":
            llego = self._ir_hacia(self.punto_ruido, VEL_INVESTIGAR * factor, dt, mundo)
            if llego or self.atascado_ms > TIEMPO_ATASCADO_MS:
                # Llegó (o no puede llegar): ahora busca alrededor un rato.
                self.punto_ruido = None
                self.escondite_objetivo = None
                self.busqueda_ms = DURACION_BUSQUEDA_MS
                self.atascado_ms = 0
            return

        if accion == "BUSCAR":
            # Quieto, mirando a un lado y al otro.
            self.busqueda_ms = max(0, self.busqueda_ms - dt)
            self.angulo += math.sin(self.tiempo_ms / 420) * 0.045 * factor
            return

        if accion == "VOLVER":
            # Deshace el camino sacando puntos de la pila.
            if self._ir_hacia(self.rastro[-1], VEL_INVESTIGAR * factor, dt, mundo, 6):
                self.rastro.pop()
            return

        # PATRULLAR
        destino = self.ruta[self.indice_ruta]
        if self._ir_hacia(destino, VEL_PATRULLA * factor, dt, mundo, 6):
            self.indice_ruta = (self.indice_ruta + 1) % len(self.ruta)

    def _dejar_rastro(self):
        """Apila un punto cada SEPARACION_RASTRO píxeles mientras está fuera."""
        if not self.rastro or _distancia(self.rastro[-1], self.centro) >= SEPARACION_RASTRO:
            self.rastro.append(self.centro)

    def _ir_hacia(self, destino, velocidad, dt, mundo, tolerancia=10):
        """Da un paso hacia `destino`. Devuelve True si ya llegó.

        Se mueve primero en X y luego en Y, como los jugadores, para que pueda
        deslizarse por una pared en vez de quedarse pegado.
        """
        dx, dy = destino[0] - self.centro[0], destino[1] - self.centro[1]
        distancia = math.hypot(dx, dy)
        if distancia <= tolerancia:
            self.atascado_ms = 0
            return True

        objetivo_angulo = math.atan2(dy, dx)
        diferencia = (objetivo_angulo - self.angulo + math.pi) % (2 * math.pi) - math.pi
        self.angulo += diferencia * 0.25   # gira suave, no de golpe

        paso = min(velocidad, distancia)
        antes = self.hitbox.center
        for eje_x, eje_y in ((dx / distancia * paso, 0), (0, dy / distancia * paso)):
            previo = self.hitbox.copy()
            self._mover(eje_x, eje_y)
            if mundo.colisiona(self.hitbox):
                self.hitbox = previo
        if self.hitbox.center == antes:
            self.atascado_ms += dt
        else:
            self.atascado_ms = 0
        return False

    def _mover(self, dx, dy):
        # Rect solo guarda enteros: se acumula lo fraccionario aparte para que
        # las velocidades como 1.7 no se redondeen a 1.
        self._resto = getattr(self, "_resto", [0.0, 0.0])
        self._resto[0] += dx
        self._resto[1] += dy
        enteros = int(self._resto[0]), int(self._resto[1])
        self._resto[0] -= enteros[0]
        self._resto[1] -= enteros[1]
        self.hitbox.move_ip(*enteros)

    # -- Dibujo -------------------------------------------------------------------

    def dibujar_vision(self, screen, offset):
        """El cono de visión, translúcido, en el piso."""
        cx, cy = self.centro[0] - offset[0], self.centro[1] - offset[1]
        puntos = [(cx, cy)]
        pasos = 12
        for i in range(pasos + 1):
            a = self.angulo - MEDIO_ANGULO_VISION + 2 * MEDIO_ANGULO_VISION * i / pasos
            puntos.append((cx + math.cos(a) * ALCANCE_VISION, cy + math.sin(a) * ALCANCE_VISION))
        # La capa se recorta a lo que ocupa el cono, y solo a la parte que cae
        # en pantalla: antes era un cuadrado de 600x600 nuevo por alien, por
        # viewport y por frame, y eso pesaba.
        xs = [p[0] for p in puntos]
        ys = [p[1] for p in puntos]
        caja = pygame.Rect(int(min(xs)) - 2, int(min(ys)) - 2,
                           int(max(xs) - min(xs)) + 5, int(max(ys) - min(ys)) + 5)
        visible = caja.clip(screen.get_clip())
        if visible.width <= 0 or visible.height <= 0:
            return
        capa = pygame.Surface(visible.size, pygame.SRCALPHA)
        locales = [(x - visible.x, y - visible.y) for x, y in puntos]
        color = COLOR_CONO.get(self.accion, (255, 255, 255))
        pygame.draw.polygon(capa, (*color, 46), locales)
        pygame.draw.polygon(capa, (*color, 110), locales, 2)
        screen.blit(capa, visible.topleft)

    def dibujar(self, screen, offset):
        """Figura provisional hasta que llegue el sprite de PixelLab."""
        pie_x, pie_y = self.hitbox.centerx - offset[0], self.hitbox.bottom - offset[1]
        flote = math.sin(self.tiempo_ms / 260) * 3

        pygame.draw.ellipse(screen, (10, 12, 20), (pie_x - 22, pie_y - 8, 44, 14))
        cuerpo = pygame.Rect(0, 0, 46, 62)
        cuerpo.midbottom = (pie_x, pie_y - 4 + flote)
        pygame.draw.ellipse(screen, (112, 214, 120), cuerpo)
        pygame.draw.ellipse(screen, (30, 70, 40), cuerpo, 3)

        # Ojos grandes que miran hacia donde va.
        mira_x = math.cos(self.angulo) * 4
        mira_y = math.sin(self.angulo) * 3
        for lado in (-1, 1):
            ojo = pygame.Rect(0, 0, 15, 20)
            ojo.center = (cuerpo.centerx + lado * 10 + mira_x, cuerpo.y + 22 + mira_y)
            pygame.draw.ellipse(screen, (12, 12, 20), ojo)
            pygame.draw.circle(screen, (230, 240, 255), (ojo.centerx - 3, ojo.y + 6), 3)

        # Antenas.
        for lado in (-1, 1):
            base = (cuerpo.centerx + lado * 8, cuerpo.y + 4)
            punta = (cuerpo.centerx + lado * 16, cuerpo.y - 14)
            pygame.draw.line(screen, (30, 70, 40), base, punta, 3)
            pygame.draw.circle(screen, (255, 120, 200), punta, 5)

        # "!" si persigue, "?" si investiga o busca.
        signo = {"PERSEGUIR": "!", "ATRAPAR": "!", "REVISAR_ESCONDITE": "!",
                 "INVESTIGAR": "?", "BUSCAR": "?"}.get(self.accion)
        if self.accion == "DESCANSAR" and self.aturdido:
            signo = "zZ"
            # Chispas: lo apagó un hackeo.
            for i in range(3):
                a = self.tiempo_ms / 150 + i * 2.1
                px = cuerpo.centerx + math.cos(a) * 26
                py = cuerpo.y + 10 + math.sin(a) * 12
                pygame.draw.line(screen, (150, 200, 255), (px - 4, py), (px + 4, py), 2)
                pygame.draw.line(screen, (150, 200, 255), (px, py - 4), (px, py + 4), 2)
        if signo:
            color = {"!": (240, 70, 60), "?": (255, 214, 64)}.get(signo, (150, 200, 255))
            f = fuente_de_tamano(30)
            texto = f.render(signo, True, color)
            sombra = f.render(signo, True, (12, 11, 23))
            pos = (cuerpo.centerx - texto.get_width() // 2, cuerpo.y - 46)
            screen.blit(sombra, (pos[0] + 2, pos[1] + 2))
            screen.blit(texto, pos)
