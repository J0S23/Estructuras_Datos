"""Punto de entrada gráfico de Alcalde Digital.

Arranca la ventana de Pygame y conecta las pantallas con las estructuras
de datos del proyecto: el ABB (Estructuras/abb_publicaciones.py) decide en
qué orden aparecen las publicaciones dudosas, y el árbol de decisión
(Estructuras/arbol_decision.py) modela las opciones del jugador y sus
consecuencias sobre los indicadores de la ciudad.
"""

import sys

import pygame

from config import DEFAULT_FPS
from game_state import GameState
from transition_manager import TransitionManager

from Estructuras.arbol_decision import ArbolDecision
from Estructuras.abb_publicaciones import ArbolPublicaciones
from data.publicaciones_ejemplo import PUBLICACIONES_EJEMPLO

from fuentes import construir_fuentes
from ui_components import construir_botones

from screens.menu import render_menu, OPCIONES_MENU
from screens.ciudad import render_ciudad
from screens.ayuda import render_ayuda
from screens.creditos import render_creditos
from screens.publicacion import render_publicacion


ANCHO, ALTO = 960, 600
OPCION_TECLAS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Alcalde Digital")
        self.screen = pygame.display.set_mode((ANCHO, ALTO))
        self.clock = pygame.time.Clock()

        # Tipografía pixel del juego (Fuentes/), con respaldo a fuente del sistema.
        self.fuentes = construir_fuentes()
        self.font = self.fuentes["subtitle"]
        self.small_font = self.fuentes["small"]

        self.state = GameState()
        self.transitions = TransitionManager()
        self.current_screen = "menu"
        self.menu_buttons = construir_botones(OPCIONES_MENU, ANCHO, ALTO)
        self.menu_selected = 0
        self.pantalla_anterior = "ciudad"  # a dónde vuelven ayuda/créditos

        self._construir_arboles()
        self.nodo_publicacion_actual = None
        self.nodo_actual = None
        self.credit_scroll = 0

        self.running = True

    # -- Estructuras de datos -------------------------------------------------

    def _construir_arboles(self):
        """Construye el ABB de publicaciones y un árbol de decisión por publicación."""
        self.arbol_publicaciones = ArbolPublicaciones()
        self._arboles_decision = {}

        for item in PUBLICACIONES_EJEMPLO:
            veracidad = self._estimar_veracidad(item)
            # Si dos publicaciones estiman la misma veracidad, se desplaza para no chocar en el ABB.
            while self.arbol_publicaciones.buscar(veracidad) is not None:
                veracidad += 1
            self.arbol_publicaciones.insertar(veracidad, item["texto"], item.get("tipo", "publicacion"))

            arbol = ArbolDecision(item)
            raiz = arbol.construir_desde_dict(item)
            self._arboles_decision[veracidad] = raiz

    @staticmethod
    def _estimar_veracidad(item):
        """Traduce los efectos declarados de una publicación en un puntaje de veracidad 0-100.

        Más 'desinformacion' o menos 'informacion_verificada' en sus efectos => publicación más dudosa.
        Esto es lo que justifica el ABB: ordenar y priorizar publicaciones por qué tan confiables son.
        """
        efectos = item.get("efectos", {})
        veracidad = 50 - efectos.get("desinformacion", 0) + efectos.get("informacion_verificada", 0)
        return max(0, min(100, veracidad))

    def iniciar_siguiente_publicacion(self):
        """Saca del ABB la publicación con menor veracidad (la más dudosa) y arranca su árbol de decisión."""
        pendientes = self.arbol_publicaciones.recorrido_inorden()
        if not pendientes:
            return
        objetivo = pendientes[0]
        raiz = self._arboles_decision.pop(objetivo["veracidad"], None)
        self.arbol_publicaciones.eliminar(objetivo["veracidad"])
        if raiz is None:
            return
        self.nodo_publicacion_actual = raiz
        self.nodo_actual = raiz
        self.state.publicaciones_vistas.append(raiz.texto)
        self.transitions.request(self, "publicacion")

    def elegir_opcion(self, indice):
        """Avanza el árbol de decisión según la opción elegida por el jugador y aplica sus efectos."""
        if self.nodo_actual is None or indice >= len(self.nodo_actual.hijos):
            return
        arbol = ArbolDecision(None)
        hijo = self.nodo_actual.hijos[indice]
        arbol.aplicar_efectos(hijo, self.state.indicadores)

        if hijo.hijos:
            consecuencia = hijo.hijos[0]
            arbol.aplicar_efectos(consecuencia, self.state.indicadores)
            self.nodo_actual = consecuencia
        else:
            self.nodo_actual = hijo

        self.state.puntaje += 10

    # -- Loop principal ---------------------------------------------------------

    def run(self):
        while self.running:
            dt = self.clock.tick(DEFAULT_FPS)
            self._manejar_eventos()
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
        if key == pygame.K_ESCAPE:
            self.running = False
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

        elif self.current_screen == "ciudad":
            if key == pygame.K_e:
                self.iniciar_siguiente_publicacion()
            elif key == pygame.K_h:
                self.pantalla_anterior = "ciudad"
                self.transitions.request(self, "ayuda")
            elif key == pygame.K_c:
                self.pantalla_anterior = "ciudad"
                self.transitions.request(self, "creditos")

        elif self.current_screen == "publicacion":
            en_raiz = self.nodo_actual is self.nodo_publicacion_actual
            if en_raiz and key in OPCION_TECLAS:
                indice = OPCION_TECLAS.index(key)
                self.elegir_opcion(indice)
            elif not en_raiz and key == pygame.K_RETURN:
                self.transitions.request(self, "ciudad")

        elif self.current_screen in ("ayuda", "creditos"):
            if key in (pygame.K_RETURN, pygame.K_BACKSPACE):
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
            self.transitions.request(self, "ciudad")
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
        elif self.current_screen == "ciudad":
            render_ciudad(self.screen, self.font, self.state, self.small_font)
        elif self.current_screen == "publicacion":
            render_publicacion(self.screen, self.font, self.nodo_publicacion_actual, self.nodo_actual, self.small_font)
        elif self.current_screen == "ayuda":
            render_ayuda(self.screen, self.small_font)
        elif self.current_screen == "creditos":
            self.credit_scroll = render_creditos(self.screen, self.small_font, self.credit_scroll)

        self.transitions.draw(self.screen)


if __name__ == "__main__":
    Game().run()
