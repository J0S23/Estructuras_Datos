"""Prototipo del MUNDO de Alcalde Digital: mapa, personajes y pantalla dividida.

Se corre con `python main.py`.

Carga el mapa con sus colisiones (mundo.py), crea un personaje por jugador
—P1 Ciudadano con WASD y P2 Candidato con flechas— y dibuja un viewport por
jugador con su propia cámara (screens/partida.py), de modo que cada uno ve al
otro moverse por el mapa.

La lógica del juego y las estructuras de datos (el ABB de publicaciones y los
árboles de decisión y de diálogo) van aparte, en App_estructuras.py /
main_estructuras.py. Los dos se van a fusionar más adelante; por ahora se
ejecutan por separado para poder trabajar en cada uno sin romper el otro.
"""

import os
import sys

import pygame

from config import DEFAULT_FPS
from game_state import GameState
from transition_manager import TransitionManager

from fuentes import construir_fuentes
from ui_components import construir_botones

from mundo import Mundo
from Movimiento.Personaje import Personaje, CONTROLES_WASD, CONTROLES_FLECHAS

from screens.menu import render_menu, OPCIONES_MENU
from screens.partida import render_partida
from screens.ayuda import render_ayuda
from screens.creditos import render_creditos


# Tamaño de la ventana cuando NO está en pantalla completa (tecla F11).
ANCHO_VENTANA, ALTO_VENTANA = 960, 600

MAPA_PRUEBA = "Colegio"

# Jugadores de la partida local. El orden define el viewport que le toca a
# cada uno (ver screens/partida.py y CLAUDE.md).
JUGADORES = [
    {"carpeta": "P1", "rol": "Ciudadano", "controles": CONTROLES_WASD, "controles_nombre": "WASD"},
    {"carpeta": "P2", "rol": "Candidato", "controles": CONTROLES_FLECHAS, "controles_nombre": "Flechas"},
]


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Alcalde Digital")
        self.pantalla_completa = True
        self.screen = self._crear_ventana()
        self.ancho, self.alto = self.screen.get_size()
        self.clock = pygame.time.Clock()

        # Tipografía pixel del juego (Fuentes/), con respaldo a fuente del sistema.
        self.fuentes = construir_fuentes()
        self.font = self.fuentes["subtitle"]
        self.small_font = self.fuentes["small"]

        self.state = GameState()
        self.transitions = TransitionManager()
        self.current_screen = "menu"
        self.menu_buttons = construir_botones(OPCIONES_MENU, self.ancho, self.alto)
        self.menu_selected = 0
        self.pantalla_anterior = "partida"  # a dónde vuelven ayuda/créditos

        self.mundo = None
        self.jugadores = []
        self.mostrar_hitboxes = False
        self.credit_scroll = 0

        self.running = True

    # -- Ventana -----------------------------------------------------------------

    @staticmethod
    def _tamano_escritorio():
        """Resolución del escritorio, para dimensionar la ventana sin bordes."""
        try:
            tamanos = pygame.display.get_desktop_sizes()
            if tamanos:
                return tamanos[0]
        except (AttributeError, pygame.error):
            pass
        info = pygame.display.Info()
        return info.current_w, info.current_h

    def _crear_ventana(self):
        """Pantalla completa sin bordes, o ventana normal si se alterna con F11.

        Se usa NOFRAME (una ventana sin marco del tamaño del escritorio) y no
        pygame.FULLSCREEN a propósito: la pantalla completa exclusiva cambia el
        modo de video del monitor, y Windows reacomoda las ventanas de las
        demás aplicaciones para que quepan en la resolución temporal, dejándolas
        descolocadas al salir. Sin bordes se ve igual y no afecta a nada más.

        Se arranca maximizado para aprovechar todo el espacio: con cuatro
        jugadores la pantalla se parte en cuatro y cada viewport queda muy
        chico si la ventana es pequeña.
        """
        if self.pantalla_completa:
            return pygame.display.set_mode(self._tamano_escritorio(), pygame.NOFRAME)
        return pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))

    def _aplicar_tamano(self):
        """Recalcula lo que depende del tamaño de la ventana."""
        self.ancho, self.alto = self.screen.get_size()
        self.menu_buttons = construir_botones(OPCIONES_MENU, self.ancho, self.alto)
        self.menu_selected = min(self.menu_selected, len(self.menu_buttons) - 1)

    def alternar_pantalla_completa(self):
        self.pantalla_completa = not self.pantalla_completa
        self.screen = self._crear_ventana()
        self._aplicar_tamano()

    # -- Partida -----------------------------------------------------------------

    def iniciar_partida(self):
        """Carga el mapa y crea los personajes en una posición libre."""
        if self.mundo is None:
            self.mundo = Mundo(MAPA_PRUEBA)

        self.jugadores = []
        centro = (self.mundo.ancho // 2, self.mundo.alto // 2)
        for i, datos in enumerate(JUGADORES):
            ruta = os.path.join("Imagenes", "Personajes", datos["carpeta"])
            jugador = Personaje(0, 0, ruta, velocidad=4, controles=datos["controles"])
            jugador.rol = datos["rol"]
            jugador.controles_nombre = datos["controles_nombre"]

            # Se separan un poco para que no aparezcan encimados.
            preferido = (centro[0] + (i - 0.5) * 120, centro[1])
            x, y = self.mundo.punto_libre(preferido, jugador.hitbox_w, jugador.hitbox_h)
            jugador.hitbox.topleft = (int(x), int(y))
            jugador.sync_sprite_from_hitbox()
            self.jugadores.append(jugador)

        self.transitions.request(self, "partida")

    def _actualizar_partida(self):
        if not self.jugadores or self.mundo is None:
            return
        teclas = pygame.key.get_pressed()
        for jugador in self.jugadores:
            jugador.actualizar(teclas, colisiona=self.mundo.colisiona)

    # -- Loop principal ---------------------------------------------------------

    def run(self):
        while self.running:
            dt = self.clock.tick(DEFAULT_FPS)
            self._manejar_eventos()
            if self.current_screen == "partida" and self.transitions.is_idle():
                self._actualizar_partida()
            self.transitions.update(self, dt)
            self._dibujar()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.running = False
            elif evento.type == pygame.KEYDOWN:
                self._manejar_tecla(evento.key)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._manejar_click(evento.pos)

    def _manejar_tecla(self, key):
        if key == pygame.K_F11:
            self.alternar_pantalla_completa()
            return
        if self.transitions.active:
            return  # ignora entradas mientras hay un fundido en curso

        if self.current_screen == "menu":
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_selected = (self.menu_selected - 1) % len(self.menu_buttons)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selected = (self.menu_selected + 1) % len(self.menu_buttons)
            elif key == pygame.K_RETURN:
                self._activar_opcion_menu(self.menu_buttons[self.menu_selected].action)
            elif key == pygame.K_ESCAPE:
                self.running = False

        elif self.current_screen == "partida":
            if key == pygame.K_h:
                self.mostrar_hitboxes = not self.mostrar_hitboxes
            elif key == pygame.K_ESCAPE:
                self.transitions.request(self, "menu")

        elif self.current_screen in ("ayuda", "creditos"):
            if key in (pygame.K_RETURN, pygame.K_BACKSPACE, pygame.K_ESCAPE):
                self.transitions.request(self, self.pantalla_anterior)

    def _manejar_click(self, pos):
        """Click del mouse: por ahora solo lo usa el menú principal."""
        if self.current_screen != "menu" or self.transitions.active:
            return
        for i, boton in enumerate(self.menu_buttons):
            if boton.contains(pos):
                self.menu_selected = i
                self._activar_opcion_menu(boton.action)
                return

    def _activar_opcion_menu(self, accion):
        if accion == "jugar":
            self.pantalla_anterior = "partida"
            self.iniciar_partida()
        elif accion == "salir":
            self.running = False
        else:
            # ayuda / creditos: se vuelve al menú al salir de ellas
            self.pantalla_anterior = "menu"
            self.transitions.request(self, accion)

    # -- Dibujo -----------------------------------------------------------------

    def _dibujar(self):
        if self.current_screen == "menu":
            render_menu(self.screen, self.menu_buttons, self.menu_selected)
        elif self.current_screen == "partida":
            render_partida(self.screen, self.mundo, self.jugadores, self.mostrar_hitboxes)
        elif self.current_screen == "ayuda":
            render_ayuda(self.screen, self.small_font)
        elif self.current_screen == "creditos":
            self.credit_scroll = render_creditos(self.screen, self.small_font, self.credit_scroll)

        self.transitions.draw(self.screen)


if __name__ == "__main__":
    Game().run()
