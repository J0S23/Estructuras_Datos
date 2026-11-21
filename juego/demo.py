"""La pantalla de atracción de la feria: si nadie toca el menú un rato, el
juego se juega solo.

Solo con el modo feria (Menú > Opciones). Con el menú quieto ESPERA_MENU_S,
arranca una partida en modo feria (en Fácil) con dos jugadores al azar que
maneja este piloto automático (`Demo`), con un letrero de "Presiona
cualquier botón para jugar". A los PARTIDA_S (o si se termina)
sale el ranking (screens/ranking.py) RANKING_S y vuelve al menú, y así. Lo
que sea que se toque (una tecla, un botón del mando, un clic) vuelve al menú
de una (`Game.salir_demo`). Una partida de demo no anota logros ni entra al
ranking (`Game.admin_usado`).

El piloto juega "con lo que ya hay": cada jugador va a donde marca su flecha
amarilla (`Mision.punto_objetivo`, la misma que ven los jugadores) por el
camino de la navegación, mantiene la tecla de interactuar al llegar (en la
demo las tareas son de mantener la tecla, sin minijuegos), sigue la flecha
roja en un apagón, saca el celular de vez en cuando y, si se traba, pasea un
rato. La puerta con código la abre al llegar (no lee las notas: es una demo).
"""

import math
import random

import pygame

ESPERA_MENU_S = 30          # menú quieto -> empieza la demo
PARTIDA_S = 80              # cuánto dura cada partida de demo
RANKING_S = 12              # el ranking, entre partida y menú
JUGADORES = 2
RECALCULAR_MS = 1500        # vuelve a buscar el camino
LLEGA_PX = 26               # "llegó" al objetivo
TRABADO_MS = 2200           # sin moverse esto -> pasea un rato
PASEO_MS = 4000
CELULAR_CADA_MS = 26000     # saca el celular (para que se vea NEXUS)
CELULAR_DURA_MS = 4200
CERRAR_PANEL_MS = 1600      # otro panel abierto (una nota, un aviso): lo cierra
ABRIR_PRISION_MS = 9000     # (la demo no busca el código en las notas)
TAMANO_NAV = (48, 19)       # la navegación del tamaño de un jugador: por donde pasa un
                            # prisionero (34x20) un jugador a veces no cabe


class Teclas(dict):
    """Lo que el juego cree que es `pygame.key.get_pressed()`."""

    def __getitem__(self, tecla):
        return self.get(tecla, False)


def _teclas_de(jugador, accion):
    return tuple(jugador.teclas.get(accion, ())) + tuple(jugador.personaje.controles.get(accion, ()))


class Piloto:
    """Lo que hace un jugador de la demo."""

    def __init__(self, jugador, desfase_ms):
        self.jugador = jugador
        self.camino = []
        self.destino = None
        self.al_final = False         # ya recorrió todo el camino (parcial: hasta donde se puede)
        self.buscar_ms = 0
        self.quieto_ms = 0
        self.ultima = jugador.hitbox.center
        self.paseo_ms = 0
        self.paseo = None
        self.celular_ms = CELULAR_CADA_MS * 0.5 + desfase_ms
        self.panel_ms = 0
        self.ms = 0
        self.rng = random.Random(jugador.puesto * 97 + 13)

    # -- A dónde va --------------------------------------------------------------------

    def _objetivo(self, juego):
        j = self.jugador
        eventos = getattr(juego, "eventos", None)
        caja = getattr(eventos, "caja", None) if eventos is not None and eventos.apagon else None
        if caja is not None:
            return caja.get("pie") or caja["rect"].center
        mision = getattr(juego, "mision", None)
        if mision is not None and mision.activa:
            obj = mision.punto_objetivo(j)
            if obj is not None:
                return obj[0]
        return None

    def _paseo(self, juego, nav):
        """Un punto al azar al que se puede llegar caminando."""
        libres = getattr(nav, "_libres_lista", None)
        if libres is None:
            libres = nav._libres_lista = list(nav.libre)
        pie = self.jugador.hitbox.center
        for _ in range(12):
            c = self.rng.choice(libres)
            punto = (c[0] + nav.ancho // 2, c[1] + nav.alto // 2)
            if 200 < math.dist(punto, pie) < 1400 and nav.conectados(pie, punto, sellos=False):
                return punto
        return None

    # -- Cada cuadro -------------------------------------------------------------------

    def actualizar(self, juego, dt, teclas, pulsar):
        j = self.jugador
        if j.preso is not None or getattr(j, "eliminado", False) or j.escondido:
            return
        self._paneles(juego, dt, pulsar)
        if j.panel is not None:
            return
        from juego import navegacion
        nav = navegacion.de_mundo(juego.mundo, *TAMANO_NAV)
        pie = j.hitbox.center

        # La puerta con código: la demo no lee las notas (a los ABRIR_PRISION_MS
        # se abre la de la prisión; las otras, al llegar a ellas).
        mision = getattr(juego, "mision", None)
        if mision is not None and mision.activa:
            for i, puerta in enumerate(mision.puertas):
                if not puerta["abierta"] and (math.dist(puerta["rect"].center, pie) < 150 or (
                        i == 0 and mision.fase == "prision" and self.ms > ABRIR_PRISION_MS)):
                    mision.abrir_puerta(j, i=i)
                    break
        self.ms += dt

        self.paseo_ms -= dt
        destino = self.paseo if self.paseo_ms > 0 and self.paseo is not None else self._objetivo(juego)
        if destino is None:
            if self.paseo is None or math.dist(pie, self.paseo) < LLEGA_PX:
                self.paseo = self._paseo(juego, nav)
            destino = self.paseo
        if destino is None:
            return
        destino = (int(destino[0]), int(destino[1]))

        # Otro destino: el camino de antes ya no sirve (se busca uno nuevo).
        if self.destino is None or math.dist(self.destino, destino) > 60:
            self.destino, self.camino, self.al_final, self.buscar_ms = destino, [], False, 0
        llego = math.dist(destino, pie) < LLEGA_PX
        if not llego and self.al_final and math.dist(destino, pie) < 260:
            if nav.libre_entre(pie, destino):
                self.camino = [destino]     # (lo último, derecho: pisar la pieza, el kit)
            else:
                llego = True                # (hasta donde se puede: la celda, detrás de las rejas)

        # ¿Se trabó (quieto sin haber llegado)? Pasea un rato a otro lado.
        if math.dist(pie, self.ultima) > 6 or llego:
            self.ultima, self.quieto_ms = pie, 0
        else:
            self.quieto_ms += dt
        if self.quieto_ms > TRABADO_MS and self.paseo_ms <= 0:
            self.paseo, self.paseo_ms, self.quieto_ms = self._paseo(juego, nav), PASEO_MS, 0
            self.destino = None
            return

        # Llegó (o hasta donde se puede): mantiene la tecla (consolas, cápsula,
        # fusibles) y la pulsa de vez en cuando (piezas, prisioneros, celdas).
        if llego:
            for k in _teclas_de(j, "interactuar"):
                teclas[k] = True
            if self.rng.random() < dt / 900:
                pulsar.append((j, "interactuar"))
            return

        # El camino (por partes, como las flechas), desde donde está. Si se
        # desvió y ya no ve el siguiente punto, otro.
        self.buscar_ms -= dt
        if self.camino and not nav.libre_entre(pie, self.camino[0]):
            self.buscar_ms = 0
        if self.buscar_ms <= 0 or (not self.camino and not self.al_final):
            nuevo = nav.camino(pie, destino, parcial=True, sellos=False, por_partes=True,
                               quien=("demo", j.puesto))
            if nuevo is not None:
                self.camino, self.buscar_ms = list(nuevo), RECALCULAR_MS
                while len(self.camino) > 1 and not nav.libre_entre(pie, self.camino[0]):
                    self.camino.pop(0)          # (salió de donde empezó a buscar)
            elif not nav.ocupada:
                # Sin camino de su tamaño (parado donde la cuadrícula no tiene
                # celda libre): el de los prisioneros, como la flecha.
                otro = navegacion.de_mundo(juego.mundo, 34, 20).camino(pie, destino, parcial=True, sellos=False)
                self.camino, self.buscar_ms = list(otro or [destino]), RECALCULAR_MS
        while self.camino and math.dist(self.camino[0], pie) < 18:
            self.camino.pop(0)
            if not self.camino:
                self.al_final = True
        if not self.camino:
            return                      # (esperando el camino)
        siguiente = self.camino[0]
        dx, dy = siguiente[0] - pie[0], siguiente[1] - pie[1]
        for accion, activo in (("derecha", dx > 6), ("izquierda", dx < -6),
                               ("abajo", dy > 6), ("arriba", dy < -6)):
            if activo:
                for k in _teclas_de(j, accion):
                    teclas[k] = True
        # Con un alien cerca, en sigilo (se ve que la tecla existe).
        if any(math.dist(a.hitbox.center, pie) < 420 for a in juego.aliens
               if not getattr(a, "oculta", False)):
            for k in _teclas_de(j, "sigilo"):
                teclas[k] = True

    def _paneles(self, juego, dt, pulsar):
        """El celular de vez en cuando; los demás paneles se cierran solos."""
        j = self.jugador
        panel = j.panel
        if panel is not None:
            self.panel_ms += dt
            if panel.get("tipo") == "celular":
                if self.panel_ms > CELULAR_DURA_MS:
                    j.cerrar_panel()
                elif int((self.panel_ms - dt) / 1300) != int(self.panel_ms / 1300):
                    pulsar.append((j, "abajo"))
            elif self.panel_ms > CERRAR_PANEL_MS:
                j.cerrar_panel()
            return
        self.panel_ms = 0
        self.celular_ms -= dt
        if self.celular_ms <= 0 and getattr(juego, "nexus", None) is not None:
            self.celular_ms = CELULAR_CADA_MS
            pulsar.append((j, "celular"))


class Demo:
    """La demo en curso: en qué parte va y los pilotos de los jugadores."""

    def __init__(self, guardado):
        self.guardado = guardado     # lo que había en el juego antes (Game._entrar_demo)
        self.parte = "cargando"      # cargando -> partida -> ranking
        self.ms = 0
        self.pilotos = []
        self.salir = False           # tocaron algo mientras cargaba: al menú en cuanto termine

    def empezar_partida(self, juego):
        self.parte, self.ms = "partida", 0
        from juego import navegacion
        navegacion.de_mundo(juego.mundo, *TAMANO_NAV)      # (armada ya, en la carga)
        self.pilotos = [Piloto(j, k * CELULAR_CADA_MS / 2) for k, j in enumerate(juego.jugadores)]

    def teclas(self, juego, dt):
        """Las teclas "presionadas" de este cuadro (y las de una vez van directo
        a `Game._tecla_en_partida`, como si se hubieran presionado)."""
        teclas, pulsar = Teclas(), []
        for piloto in self.pilotos:
            piloto.actualizar(juego, dt, teclas, pulsar)
        for jugador, accion in pulsar:
            for k in jugador.teclas.get(accion, ())[:1]:
                juego._tecla_en_partida(k)
        return teclas


def letrero(screen, ms):
    """El letrero de la demo, abajo al centro: que se note que se puede jugar."""
    from juego.fuentes import fuente_de_tamano
    from juego import cache_dibujo
    ancho, alto = screen.get_size()
    f = fuente_de_tamano(max(18, min(34, alto // 26)))
    fc = fuente_de_tamano(max(13, min(20, alto // 44)))
    pulso = round((0.5 + 0.5 * math.sin(ms / 1000 * math.pi * 1.4)) * 6) / 6     # (6 tonos: la caché de textos)
    titulo = cache_dibujo.texto(f, "PRESIONA CUALQUIER BOTÓN PARA JUGAR",
                                tuple(int(150 + 105 * pulso) for _ in range(3)))
    sub = cache_dibujo.texto(fc, "NEXUS · demo: así se juega · escapen de la nave sin creerse todo lo que circula",
                             (190, 210, 245))
    caja = pygame.Rect(0, 0, max(titulo.get_width(), sub.get_width()) + 48,
                       titulo.get_height() + sub.get_height() + 22)
    caja.midbottom = (ancho // 2, alto - max(18, alto // 30))
    screen.blit(cache_dibujo.capa(caja.size, (8, 10, 24, 200)), caja.topleft)
    pygame.draw.rect(screen, (90, 200, 255), caja, 2, border_radius=10)
    screen.blit(titulo, titulo.get_rect(midtop=(caja.centerx, caja.y + 8)))
    screen.blit(sub, sub.get_rect(midtop=(caja.centerx, caja.y + 12 + titulo.get_height())))
