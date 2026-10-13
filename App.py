"""NEXUS: el juego. Mundo, personajes y estructuras de datos, juntos.

Se corre con `python main.py`.

Aquí se unieron los dos prototipos que antes iban por separado. En una misma
partida conviven:

- el **mapa** con sus colisiones y una cámara por jugador (mundo.py,
  screens/partida.py),
- la **misión** de la nave (mision.py) con su tutorial, eventos y puertas,
- el **árbol de comportamiento** de los aliens (Estructuras/arbol_comportamiento.py),
- la red social **NEXUS** y su misión del infiltrado (infiltrado.py),
- el **árbol de logros** de la partida (logros.py),
- y el **árbol binario de habilidades** de cada rol
  (Estructuras/arbol_habilidades.py), que es lo que hace que subir de nivel
  cambie las opciones que el jugador ve, no solo un número.

La ronda dura unos minutos y termina en una pantalla de resultados. Cada
jugador juega en su mitad de la pantalla con sus propias teclas, incluidas las
de navegar paneles: la partida es local y los dos comparten teclado.
"""

import math
import os
import sys

import pygame

from config import DEFAULT_FPS
from transition_manager import TransitionManager

from fuentes import construir_fuentes
from ui_components import construir_botones

from mundo import Mundo
from jugador import Jugador, TECLAS_POR_PUESTO, NOMBRE_CONTROLES
from Movimiento.Personaje import Personaje, CONTROLES_WASD, CONTROLES_FLECHAS

from Estructuras.arbol_comportamiento import ArbolComportamiento

from alien import Alien
import acciones_rol
from minijuego_latidos import MinijuegoLatidos
from mision import Mision, Equipo, DURACION_MISION_S
from ambiente import Ambiente
from ia_nave import Narrador
from mandos import Mandos, tecla_virtual, PUESTOS_CON_MANDO
from tutorial import Tutorial
from pausa import MenuPausa
from audio_manager import audio_manager
from infiltrado import CasoInfiltrado
from logros import GestorLogros
from eventos import GestorEventos, crear_cajas
import puertas

from data.roles import ROLES, MINIMO_JUGADORES
from data.comportamiento_alien import ARBOL_ALIEN
from data.escondites import ANCHO_ENTRADA, ALTO_ENTRADA
import objetos_mapa

from screens.menu import render_menu, OPCIONES_MENU
from screens.partida import render_partida, calcular_viewports
from screens.seleccion import render_cantidad, render_roles, OPCIONES
from screens.arbol_alien import render_arbol_alien
from screens.panel_habilidades import precargar_iconos
from screens.resultados import render_resultados
from screens.ayuda import render_ayuda
from screens.creditos import render_creditos, reiniciar_scroll
from screens.pausa import render_pausa
from screens.logros import render_aviso_logro


ANCHO_VENTANA, ALTO_VENTANA = 960, 600

# El mapa ya no se fija aquí: lo dice Hitboxes/mapa_activo.json, que se cambia
# desde el editor de mapa (Editores/editor_mapa.py, tecla M).
DURACION_RONDA_S = 300  # cinco minutos, como pide el diseño

# Tutorial de 30 s al empezar (tutorial.py). Solo en mapas con misión.
TUTORIAL_ACTIVO = True

# Teclas que suenan en los menús (menú, cantidad, roles y pausa).
TECLAS_MOVER_MENU = {pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_w, pygame.K_s}
TECLAS_OK_MENU = {pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e}

# Lo que cuesta que te atrape un alien.
PUNTOS_POR_SER_ATRAPADO = 10

# Controles de movimiento de cada puesto. Los puestos 3 y 4 van sin controles a
# propósito: se dibujan en el mapa y se animan, pero no caminan, porque les toca
# mando y eso todavía no está hecho.
def _controles_mando(puesto):
    return {d: (tecla_virtual(puesto, d),) for d in ("arriba", "abajo", "izquierda", "derecha")}


CONTROLES_POR_PUESTO = [CONTROLES_WASD, CONTROLES_FLECHAS,
                        _controles_mando(2), _controles_mando(3)]


def botones_menu(ancho, alto):
    """Los botones del menú van a la derecha, debajo del título NEXUS del
    fondo, para no tapar a los cuatro personajes ni el planeta."""
    return construir_botones(OPCIONES_MENU, ancho, alto,
                             centro_x=ancho * 0.765, centro_y=alto * 0.56,
                             ancho=min(380, int(ancho * 0.26)), alto=46, separacion=12)


def _nombre(tecla):
    """Nombre corto de una tecla, para las pistas de la selección de rol."""
    nombres = {
        pygame.K_w: "W", pygame.K_s: "S", pygame.K_e: "E",
        pygame.K_UP: "ARRIBA", pygame.K_DOWN: "ABAJO", pygame.K_RETURN: "ENTER",
        pygame.K_i: "I", pygame.K_k: "K", pygame.K_o: "O",
        pygame.K_t: "T", pygame.K_g: "G", pygame.K_y: "Y",
    }
    return nombres.get(tecla, "?")


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("NEXUS")
        self.pantalla_completa = True
        self.screen = self._crear_ventana()
        self.ancho, self.alto = self.screen.get_size()
        self.clock = pygame.time.Clock()

        self.fuentes = construir_fuentes()
        self.font = self.fuentes["subtitle"]
        self.small_font = self.fuentes["small"]

        self.transitions = TransitionManager()
        self.current_screen = "menu"
        self.menu_buttons = botones_menu(self.ancho, self.alto)
        self.menu_selected = 0
        self.pantalla_anterior = "partida"

        self.mundo = None
        self.jugadores = []
        # Pasos previos a la partida.
        self.cantidad_jugadores = MINIMO_JUGADORES
        self.cantidad_seleccionada = 0   # índice en screens.seleccion.OPCIONES
        self.seleccion_roles = []
        self.zonas = []          # zonas del mapa ya convertidas a píxeles
        self.mostrar_hitboxes = False
        self.aliens = []
        self.escondites = []
        self.objetos = None   # lo que está puesto en el mapa (objetos_mapa.py)
        self.mision = None    # fases, celdas y consumibles (mision.py)
        self.tutorial = None  # los primeros 30 s (tutorial.py)
        self.eventos = None   # apagón, alarma, compuertas (eventos.py)
        self.infiltrado = None  # misión secundaria del infiltrado de NEXUS (infiltrado.py)
        self.logros = None      # árbol de logros de la partida (logros.py)
        self.puertas_dobles, self.compuertas = [], []   # puertas.py
        self.pausa = None     # MenuPausa mientras está abierto (Esc en la partida)
        self.oscuridad = True # [L] la apaga (para probar o para quien la necesite)
        self.mandos = Mandos()  # controles de Xbox para los jugadores 3 y 4
        self.equipo = Equipo()
        self._nuevo_ambiente()
        # Lo de las habilidades de los roles (acciones_rol.py).
        self.terminales, self.paneles, self.piezas = [], [], []
        self.senuelos, self.senales = [], []
        self.arbol_alien = None
        self.mostrar_arbol_alien = False
        self.alien_en_vista = 0      # cuál alien muestra la vista del árbol
        self.credit_scroll = reiniciar_scroll()

        self.tiempo_restante_ms = DURACION_RONDA_S * 1000

        self.running = True

    # -- Ventana ---------------------------------------------------------------

    @staticmethod
    def _tamano_escritorio():
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

        Se usa NOFRAME y no pygame.FULLSCREEN a propósito: la pantalla completa
        exclusiva cambia el modo de video del monitor y Windows reacomoda las
        ventanas de las demás aplicaciones, dejándolas descolocadas al salir.
        """
        if self.pantalla_completa:
            return pygame.display.set_mode(self._tamano_escritorio(), pygame.NOFRAME)
        return pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))

    def _aplicar_tamano(self):
        self.ancho, self.alto = self.screen.get_size()
        self.menu_buttons = botones_menu(self.ancho, self.alto)
        self.menu_selected = min(self.menu_selected, len(self.menu_buttons) - 1)

    def alternar_pantalla_completa(self):
        self.pantalla_completa = not self.pantalla_completa
        self.screen = self._crear_ventana()
        self._aplicar_tamano()

    # -- Estructuras de datos ---------------------------------------------------

    # -- Partida ----------------------------------------------------------------

    # -- Paso 1: cuántos juegan --------------------------------------------------

    def abrir_cantidad(self):
        self.cantidad_seleccionada = 0
        self.transitions.request(self, "cantidad")

    def confirmar_cantidad(self):
        self.cantidad_jugadores = OPCIONES[self.cantidad_seleccionada]
        self.abrir_seleccion_roles()

    # -- Paso 2: qué rol juega cada uno ------------------------------------------

    def abrir_seleccion_roles(self):
        """Prepara el estado de la selección, uno por jugador."""
        self.seleccion_roles = []
        for puesto in range(self.cantidad_jugadores):
            teclas = TECLAS_POR_PUESTO[puesto]
            self.seleccion_roles.append({
                "cursor": puesto % len(ROLES),
                "listo": False,
                "rol": None,
                "controles": (f"Mando {puesto - 1}" if self.mandos.hay_mando(puesto)
                              else NOMBRE_CONTROLES[puesto]),
                # "Flechas" en vez de "ARRIBA/ABAJO": más corto y es como la
                # gente llama a esas teclas.
                "tecla_mover": ("Stick" if self.mandos.hay_mando(puesto)
                                else "Flechas" if pygame.K_UP in teclas["arriba"]
                                else f"{_nombre(teclas['arriba'][0])}/{_nombre(teclas['abajo'][0])}"),
                "tecla_ok": "A" if self.mandos.hay_mando(puesto) else _nombre(teclas["interactuar"][0]),
            })
        self.transitions.request(self, "roles")

    def _tecla_en_seleccion(self, key):
        """Reparte la tecla entre los jugadores que están escogiendo rol."""
        for puesto, estado in enumerate(self.seleccion_roles):
            teclas = TECLAS_POR_PUESTO[puesto]
            if key in teclas["interactuar"]:
                self._confirmar_rol(puesto, estado)
                return
            if estado["listo"]:
                continue
            if key in teclas["arriba"]:
                estado["cursor"] = (estado["cursor"] - 1) % len(ROLES)
                return
            if key in teclas["abajo"]:
                estado["cursor"] = (estado["cursor"] + 1) % len(ROLES)
                return

    def _confirmar_rol(self, puesto, estado):
        if estado["listo"]:
            # Volver a pulsar deshace la elección, por si se equivocó.
            estado["listo"] = False
            estado["rol"] = None
            return
        elegido = ROLES[estado["cursor"]]["nombre"]
        if any(otro["listo"] and otro["rol"] == elegido
               for i, otro in enumerate(self.seleccion_roles) if i != puesto):
            return  # ese rol ya lo tomaron
        estado["listo"] = True
        estado["rol"] = elegido
        if all(e["listo"] for e in self.seleccion_roles):
            self.iniciar_partida()

    # -- Paso 3: la partida ------------------------------------------------------

    def iniciar_partida(self):
        """Carga el mapa, arma los árboles y crea a los jugadores."""
        self.pausa = None
        nombre_mapa = objetos_mapa.mapa_activo()
        if self.mundo is None or self.mundo.nombre_mapa != nombre_mapa:
            self.mundo = Mundo(nombre_mapa)
        # Si se reutiliza el mundo de la ronda anterior, se quita lo que esa
        # ronda le agregó (la puerta de la prisión): si no, quedaba una puerta
        # invisible que no se abría con el código.
        self.mundo.reiniciar_paredes()
        # Dónde va cada cosa del mapa: lo que se puso con el editor de mapa, y
        # lo que no, de data/ (ver objetos_mapa.py).
        self.objetos = objetos_mapa.cargar(nombre_mapa)
        self._preparar_zonas()

        self.tiempo_restante_ms = DURACION_RONDA_S * 1000

        self.jugadores = []
        centro = (self.mundo.ancho // 2, self.mundo.alto // 2)
        if self.objetos.get("spawn"):
            centro = (int(self.objetos["spawn"][0] * self.mundo.ancho),
                      int(self.objetos["spawn"][1] * self.mundo.alto))
        for puesto, estado in enumerate(self.seleccion_roles):
            nombre_personaje = estado["rol"]     # sprites en Imagenes/Personajes/<Rol>/
            ruta = os.path.join("Imagenes", "Personajes", nombre_personaje)
            personaje = Personaje(0, 0, ruta, velocidad=4,
                                  controles=CONTROLES_POR_PUESTO[puesto])
            personaje.rol = estado["rol"]

            # Se reparten alrededor del centro para que no salgan encimados.
            angulo = puesto * 2 * math.pi / max(1, len(self.seleccion_roles))
            preferido = (centro[0] + math.cos(angulo) * 130,
                         centro[1] + math.sin(angulo) * 90)
            x, y = self.mundo.punto_libre(preferido, personaje.hitbox_w, personaje.hitbox_h)
            personaje.hitbox.topleft = (int(x), int(y))
            personaje.sync_sprite_from_hitbox()

            jugador = Jugador(personaje, estado["rol"], puesto,
                              con_mando=self.mandos.hay_mando(puesto))
            jugador.spawn = personaje.hitbox.topleft
            jugador.nombre_personaje = nombre_personaje
            personaje.controles_nombre = jugador.controles_nombre
            self.jugadores.append(jugador)

        # Los iconos de las habilidades se dejan listos aquí, mientras el
        # jugador todavía está viendo cargar, y no la primera vez que abre el
        # panel a mitad de la ronda.
        precargar_iconos([j.rol for j in self.jugadores])

        self._preparar_escondites()
        self.terminales, self.paneles, self.piezas = acciones_rol.preparar_estaciones(self.mundo, self.objetos)
        self.senuelos, self.senales = [], []
        self._crear_aliens()

        self.equipo = Equipo()
        for jugador in self.jugadores:
            jugador.equipo = self.equipo
        self.mision = Mision(self, self.objetos)
        self.puertas_dobles = puertas.crear_puertas_dobles(self.objetos, self.mundo)
        self.compuertas = puertas.crear_compuertas(self.objetos, self.mundo)
        self._nuevo_ambiente()
        self.tutorial, self.eventos = None, None
        self.infiltrado = CasoInfiltrado(self, self.objetos) if self.mision.activa else None
        self.logros = GestorLogros(self)     # uno nuevo cada partida: se reinician solos
        if self.mision.activa:
            self.tiempo_restante_ms = DURACION_MISION_S * 1000
            self.eventos = GestorEventos(self, cajas=crear_cajas(self.objetos, self.mundo))
            if TUTORIAL_ACTIVO:
                self.tutorial = Tutorial(self.jugadores)
                for alien in self.aliens:
                    alien.accion, alien.aturdido = "DESCANSAR", True
                self.decir("tutorial", forzar=True)
            else:
                self.decir("inicio", forzar=True)
        self._avisar_zonas_inalcanzables()
        self.transitions.request(self, "partida")

    def _crear_aliens(self):
        """Un alien por ruta del mapa (las que se trazan en el editor de mapa).

        Una ruta de un solo punto es un guardia: se queda ahí, mirando.

        Todos comparten el mismo árbol de comportamiento: es contenido
        (data/comportamiento_alien.py). Lo que cambia entre aliens es la ruta
        y su tipo (data/tipos_alien.py: velocidad, vista y oído).
        """
        self.arbol_alien = ArbolComportamiento(ARBOL_ALIEN)
        self.aliens = []
        tipos = self.objetos.get("tipos_aliens") or []
        rutas = [(ruta, tipos[i] if i < len(tipos) else "rastreador")
                 for i, ruta in enumerate(self.objetos["rutas_aliens"]) if len(ruta) >= 1]
        for numero, (ruta, tipo) in enumerate(rutas, start=1):
            puntos = [(int(rx * self.mundo.ancho), int(ry * self.mundo.alto)) for rx, ry in ruta]
            alien = Alien(numero, puntos, self.arbol_alien, tipo)
            for i, j in self.mundo.tramos_bloqueados(puntos, alien.hitbox.width,
                                                     alien.hitbox.height):
                print(f"[AVISO] La ruta del {alien.nombre} choca con una pared entre los "
                      f"puntos {i} y {j}. Muévela con el editor de mapa.")
            self.aliens.append(alien)
        self.alien_en_vista = 0
        self.mostrar_arbol_alien = False

    def _preparar_escondites(self):
        """Pasa los escondites de data/escondites.py a rects en píxeles."""
        self.escondites = []
        for datos in self.objetos["escondites"]:
            escondite = dict(datos)
            escondite["rect"] = pygame.Rect(0, 0, ANCHO_ENTRADA, ALTO_ENTRADA)
            escondite["rect"].center = (int(datos["rx"] * self.mundo.ancho),
                                        int(datos["ry"] * self.mundo.alto))
            escondite["ocupante"] = None       # el jugador que está adentro
            escondite["revisado_por"] = None   # el alien que lo está revisando
            escondite["enfriamiento_ms"] = 0   # tiempo en que los aliens lo ignoran
            self.escondites.append(escondite)

    def escondite_bajo(self, jugador):
        """Escondite libre frente al que está parado el jugador, o None."""
        for escondite in self.escondites:
            if escondite["ocupante"] is None and escondite["rect"].colliderect(jugador.hitbox):
                return escondite
        return None

    # -- Que se sienta: sonido, susto y la IA de la nave -------------------------

    def _nuevo_ambiente(self):
        self.ambiente = Ambiente()
        self.narrador = Narrador(al_hablar=lambda: self.ambiente.sonar("ia_voz", 0.7))
        self._aviso_pulso_ms = 0
        self._aviso_tiempo_dado = False

    def sonar(self, nombre, volumen=1.0):
        self.ambiente.sonar(nombre, volumen)

    def decir(self, evento, rol=None, forzar=False):
        return self.narrador.decir(evento, rol, forzar)

    def _actualizar_ambiente(self, dt):
        # Durante el tutorial los aliens duermen: no se oyen sus pasos.
        self.ambiente.actualizar(dt, self.jugadores, [] if self.en_tutorial else self.aliens)
        self.narrador.actualizar(dt)
        self._aviso_pulso_ms = max(0, self._aviso_pulso_ms - dt)
        asustados = [j for j in self.jugadores if j.pulso > 85 and j.preso is None]
        if asustados and self._aviso_pulso_ms == 0:
            if self.decir("pulso_alto", asustados[0].rol):
                self._aviso_pulso_ms = 25000
        if (self.mision is not None and self.mision.activa and not self._aviso_tiempo_dado
                and self.tiempo_restante_ms <= 60000):
            self._aviso_tiempo_dado = True
            self.decir("poco_tiempo", forzar=True)

    @property
    def sin_luz(self):
        """Hay un apagón: no funciona nada eléctrico (terminales, NEXUS,
        teclado de la prisión, consolas, sellos, puertas para dos, escaneo)."""
        return self.eventos is not None and self.eventos.apagon

    @property
    def en_tutorial(self):
        return self.tutorial is not None and self.tutorial.activo

    def _terminar_tutorial(self):
        """Los aliens despiertan y empieza a correr el reloj."""
        for alien in self.aliens:
            alien.aturdido = False
            alien.descanso_ms = 0
            alien.accion = "PATRULLAR"
        self.sonar("susto", 0.6)
        self.decir("despertar", forzar=True)

    def _colisiona_jugador(self, rect):
        """Las paredes, y además lo que solo frena a los jugadores (puertas.py)."""
        return (self.mundo.colisiona(rect)
                or puertas.bloquea(self.puertas_dobles, self.compuertas, rect))

    def _puerta_doble_abierta(self, puerta):
        if self.logros is not None:
            self.logros.conseguir("trabajo_en_equipo")
        self.sonar("puerta")
        self.decir("puerta_doble")

    def _alien_revisa(self, jugador, alien, escondite):
        """Un alien llegó a revisar un escondite: arranca el minijuego."""
        if jugador is None:
            return
        jugador.minijuego = MinijuegoLatidos(jugador.pulso, alien, escondite)
        self.decir("escondite_revisado", jugador.rol)
        jugador.avisar(f"¡El {alien.nombre} revisa tu escondite!", (236, 70, 60))

    def _actualizar_minijuegos(self, dt):
        for jugador in self.jugadores:
            juego = jugador.minijuego
            if juego is None:
                continue
            alien = juego.alien
            if alien.escondite_objetivo is not juego.escondite:
                # El alien dejó de revisar (lo hackearon): se acabó el peligro.
                jugador.minijuego = None
                jugador.avisar("El alien se fue de tu escondite.", (96, 200, 120))
                continue
            juego.actualizar(dt)
            if not juego.terminado:
                continue
            if juego.resultado == "calmado":
                jugador.minijuego = None
                alien.rendirse()
                self.decir("escondite_calmado", jugador.rol)
                if self.logros is not None:
                    self.logros.conseguir("fantasma", jugador)
                jugador.sumar_puntos(5)
                jugador.avisar("Te calmaste. El alien se fue. +5", (96, 200, 120))
            else:
                alien.entrar_al_escondite()
                self._atrapar(jugador, alien)

    def _atrapar(self, jugador, alien):
        """Lo llama un alien cuando su árbol llega a la hoja ATRAPAR."""
        if jugador is None:
            return
        donde = jugador.hitbox.center
        if self.logros is not None:
            self.logros.al_atrapar(jugador)
        jugador.atrapado()
        self.ambiente.susto(jugador)
        if jugador.vidas <= 0:
            # Tercera vez: queda fuera de la partida, y suelta lo que llevaba
            # (y las herramientas de su rol) donde lo atraparon.
            jugador.eliminar()
            # Primero las pruebas del infiltrado: soltar_al_morir vacía el inventario.
            if self.infiltrado is not None:
                self.infiltrado.soltar(jugador, donde)
            if self.mision is not None:
                self.mision.soltar_al_morir(jugador, donde)
            self.decir("eliminado", jugador.rol, forzar=True)
            self.sonar("eliminado", 0.8)
            jugador.avisar("Te atraparon 3 veces. Estás fuera.", (236, 70, 60))
            for otro in self.jugadores:
                if otro is not jugador:
                    otro.avisar(f"¡Perdimos al {jugador.rol}!", (236, 70, 60))
            return
        self.decir("atrapado", jugador.rol, forzar=True)
        if self.mision is not None and self.mision.encarcelar(jugador):
            vidas = jugador.vidas
            jugador.avisar(f"¡Te encerraron! Te queda{'n' if vidas > 1 else ''} {vidas} "
                           f"vida{'s' if vidas > 1 else ''}.", (236, 70, 60))
            return
        jugador.sumar_puntos(-PUNTOS_POR_SER_ATRAPADO)
        jugador.avisar(f"¡Te atrapó el {alien.nombre}! -{PUNTOS_POR_SER_ATRAPADO}",
                       (236, 70, 60))

    def _avisar_zonas_inalcanzables(self):
        """Avisa por consola si alguna zona quedó encerrada tras una pared.

        Una terminal metida en un cuarto cerrado se dibuja en el mapa pero no
        hay forma de llegar. Es el tipo de error que solo se nota jugando, así
        que mejor que el juego lo diga al arrancar.
        """
        if not self.jugadores or self.mundo is None:
            return
        referencia = self.jugadores[0]
        # Con la puerta de la prisión cerrada casi nada se alcanza: se revisa
        # como si estuviera abierta, que es como se juega después de la fase 1.
        puerta = self.mision.puerta if self.mision is not None else None
        cerrada = puerta is not None and puerta in self.mundo.paredes
        if cerrada:
            self.mundo.paredes.remove(puerta)
        malas = self.mundo.zonas_inalcanzables(
            self.zonas, referencia.hitbox.topleft,
            referencia.personaje.hitbox_w, referencia.personaje.hitbox_h)
        if cerrada:
            self.mundo.paredes.append(puerta)
        for zona in malas:
            print(f"[AVISO] La zona '{zona['clave']}' ({zona['nombre']}) no se puede "
                  f"alcanzar caminando. Muévela con el editor de mapa.")

    def _preparar_zonas(self):
        """Las zonas donde se interactúa con algo del mapa: las Terminales
        NEXUS (abren el caso del infiltrado, infiltrado.py)."""
        self.zonas = []
        for i, (rx, ry) in enumerate(self.objetos.get("nexus", []), start=1):
            radio = int(0.02 * self.mundo.ancho)
            self.zonas.append({
                "clave": f"nexus_{i}", "nombre": "Terminal NEXUS",
                "pista": "El caso del infiltrado.", "tipo": "nexus",
                "roles": [], "color": (90, 220, 230),
                "rect": pygame.Rect(int(rx * self.mundo.ancho) - radio,
                                    int(ry * self.mundo.alto) - radio, radio * 2, radio * 2),
            })

    def zona_bajo(self, jugador):
        """Zona utilizable por ese jugador sobre la que está parado, o None."""
        for zona in self.zonas:
            if zona["roles"] and jugador.rol not in zona["roles"]:
                continue
            if zona["rect"].colliderect(jugador.hitbox):
                return zona
        return None

    def _actualizar_partida(self, dt=0):
        if not self.jugadores or self.mundo is None:
            return
        teclas = self.mandos.envolver(pygame.key.get_pressed())
        en_tutorial = self.en_tutorial
        if en_tutorial:
            self.tutorial.actualizar(dt)
            if not self.tutorial.activo:
                self._terminar_tutorial()
        for jugador in self.jugadores:
            if jugador.panel is not None and jugador.panel.get("tipo") == "emision":
                # Sus teclas de moverse mueven el cursor del mapa de la Emisión.
                dx, dy = jugador.personaje.leer_movimiento(teclas)
                acciones_rol.mover_cursor_emision(self, jugador, dx, dy, dt or 16)
            jugador.actualizar(teclas, colisiona=self._colisiona_jugador)
            jugador.zona_cerca = self.zona_bajo(jugador)
            jugador.actualizar_mensaje(dt)
            jugador.info = acciones_rol.linea_de_estado(jugador)

        # Tecla de interactuar mantenida: apagar consolas, reparar la cápsula
        # y los paneles de las puertas para dos.
        sosteniendo = []
        for jugador in self.jugadores:
            mantiene = any(teclas[k] for k in jugador.teclas.get("interactuar", ()))
            jugador.progreso = None
            if mantiene and not jugador.ocupado and not jugador.escondido and not jugador.preso:
                sosteniendo.append(jugador)
                if self.mision is not None:
                    self.mision.mantener(jugador, dt)
                if self.eventos is not None:
                    self.eventos.mantener(jugador, dt)
            if self.mision is not None and self.mision.activa:
                jugador.objetivo = self.mision.objetivo()
                jugador.pista_mision = self.mision.pista(jugador)
            if self.infiltrado is not None and not jugador.pista_mision:
                jugador.pista_mision = self.infiltrado.pista(jugador)
            pista_puerta = puertas.pista(self.puertas_dobles, jugador)
            if pista_puerta and not jugador.preso:
                jugador.pista_mision = "Puerta sin energía" if self.sin_luz else pista_puerta
            pista_caja = self.eventos.pista(jugador) if self.eventos is not None else None
            if pista_caja and not jugador.preso:
                jugador.pista_mision = pista_caja
        # Las puertas para dos son eléctricas: en un apagón no abren.
        puertas.actualizar(self.puertas_dobles, [] if self.sin_luz else sosteniendo, dt,
                           self._puerta_doble_abierta)

        acciones_rol.actualizar(self, dt)
        if self.sin_luz:
            for jugador in self.jugadores:
                if jugador.pista_mision or jugador.preso:
                    continue
                estacion = getattr(jugador, "estacion_cerca", None)
                if jugador.zona_cerca is not None and jugador.zona_cerca["tipo"] == "nexus":
                    jugador.pista_mision = "Terminal NEXUS sin energía"
                elif estacion is not None and estacion["tipo"] == "terminal":
                    jugador.pista_mision = "Terminal sin energía"
        for jugador in self.jugadores:
            jugador.escondite_cerca = (None if jugador.escondido or jugador.zona_cerca
                                       or jugador.estacion_cerca
                                       else self.escondite_bajo(jugador))
        for escondite in self.escondites:
            escondite["enfriamiento_ms"] = max(0, escondite["enfriamiento_ms"] - dt)

        if not en_tutorial:
            for alien in self.aliens:
                alien.actualizar(dt, self.mundo, self.jugadores, self._atrapar,
                                 self.escondites, self._alien_revisa)
            if self.eventos is not None:
                self.eventos.actualizar(dt)
        self._actualizar_minijuegos(dt)
        self._actualizar_pulsos(dt)
        self._actualizar_ambiente(dt)
        if self.logros is not None:
            self.logros.actualizar(dt)

        if self.mision is not None:
            self.mision.actualizar(dt)
            if self.mision.resultado is not None:
                self.terminar_ronda()
                return

        if not en_tutorial:
            self.tiempo_restante_ms -= dt
        if self.tiempo_restante_ms <= 0:
            self.tiempo_restante_ms = 0
            self.terminar_ronda()

    def _extras_dibujo(self):
        """Lo del mapa que dibujan las habilidades (screens/roles.py)."""
        return {
            "terminales": self.terminales, "paneles": self.paneles, "piezas": self.piezas,
            "senuelos": self.senuelos, "senales": self.senales, "mision": self.mision,
            "puertas_dobles": self.puertas_dobles, "compuertas": self.compuertas,
            "eventos": self.eventos, "tutorial": self.tutorial, "infiltrado": self.infiltrado,
            # Campo de visión siempre; la oscuridad de la linterna, solo en un apagón.
            "vision": self.oscuridad,
            "oscuridad": self.oscuridad and self.eventos is not None and self.eventos.apagon,
            "sin_luz": self.sin_luz,
        }

    def _actualizar_pulsos(self, dt):
        """Cada jugador ajusta su pulso según el alien más cercano."""
        for jugador in self.jugadores:
            centro = jugador.hitbox.center
            if self.en_tutorial:
                jugador.actualizar_pulso(dt, None, False)
                continue
            distancia = min((math.hypot(a.centro[0] - centro[0], a.centro[1] - centro[1])
                             for a in self.aliens), default=None)
            if not jugador.cazable:
                distancia = None
            visto = any(a.objetivo is jugador for a in self.aliens)
            jugador.actualizar_pulso(dt, distancia, visto)

    def terminar_ronda(self):
        if self.mision is not None:
            self.mision.terminar_por_tiempo()
        if self.logros is not None:
            self.logros.al_terminar()
        if self.mision is not None and self.mision.activa:
            self.sonar("victoria" if self.mision.resultado == "victoria" else "derrota", 0.8)
        for jugador in self.jugadores:
            jugador.cerrar_panel()
        self.transitions.request(self, "resultados")

    # -- Abrir zonas ------------------------------------------------------------

    def interactuar(self, jugador):
        """El jugador presionó su tecla de interacción sobre una zona."""
        zona = self.zona_bajo(jugador)
        if zona is None:
            return
        if zona["tipo"] == "nexus":
            self._abrir_nexus(jugador, zona)

    def _abrir_nexus(self, jugador, zona):
        """Terminal NEXUS: el caso del infiltrado (infiltrado.py). Es lo único
        que hay en NEXUS: ver sospechosos, subir pruebas y acusar."""
        if self.sin_luz:
            jugador.avisar("La terminal NEXUS está apagada: no hay luz.", (245, 130, 120))
            return
        if self.logros is not None:
            self.logros.conseguir("conectado", jugador)
        if self.infiltrado is None:
            jugador.abrir_panel({
                "tipo": "aviso", "titulo": zona["nombre"],
                "cuerpo": ["NEXUS no tiene conexión en este mapa."],
                "pie": f"[{jugador.nombre_tecla('interactuar')}] salir",
            })
            return
        jugador.abrir_panel(self.infiltrado.panel_terminal(jugador, zona))

    # -- Resolver la opción elegida ---------------------------------------------

    def confirmar(self, jugador):
        """El jugador confirmó la opción sobre la que tiene el cursor."""
        panel = jugador.panel
        if panel is None:
            return

        tipo = panel.get("tipo")
        if tipo in ("aviso", "resultado"):
            jugador.cerrar_panel()
            return
        if tipo == "habilidades":
            self._confirmar_habilidad(jugador)
            return
        if tipo == "emision":
            acciones_rol.poner_emision(self, jugador)
            return

        accion = panel.get("accion")
        indice = jugador.cursor
        if accion == "codigo" and self.mision is not None:
            self.mision.resolver_codigo(jugador, indice)
        elif accion in ("infiltrado_menu", "infiltrado_acusar"):
            self._resolver_infiltrado(jugador, panel, indice)

    def _resolver_infiltrado(self, jugador, panel, indice):
        """Menú de la terminal durante el caso del infiltrado (infiltrado.py)."""
        caso = self.infiltrado
        if caso is None:
            jugador.cerrar_panel()
            return
        if panel["accion"] == "infiltrado_acusar":
            candidatos = panel["candidatos"]
            if indice >= len(candidatos) or not caso.activo:
                jugador.cerrar_panel()      # "Mejor no"
                return
            texto, puntos = caso.acusar(jugador, candidatos[indice])
            jugador.tareas_hechas += 1
            self._panel_resultado(jugador, texto, puntos)
            return
        acciones = panel["acciones"]
        if indice >= len(acciones):
            return
        eleccion = acciones[indice]
        if eleccion == "subir" and caso.activo:
            texto, puntos = caso.subir(jugador)
            jugador.tareas_hechas += 1
            self._panel_resultado(jugador, texto, puntos)
        elif eleccion == "acusar" and caso.activo:
            jugador.abrir_panel(caso.panel_acusar(jugador))
        else:
            jugador.cerrar_panel()

    def _panel_resultado(self, jugador, texto, puntos):
        if puntos > 0:
            resumen, color = f"+{puntos} puntos", (120, 230, 150)
        elif puntos < 0:
            resumen, color = f"{puntos} puntos", (245, 130, 120)
        else:
            resumen, color = "sin puntos", (220, 220, 220)
        jugador.avisar(resumen, color)
        jugador.abrir_panel({
            "tipo": "resultado",
            "titulo": resumen,
            "cuerpo": [texto],
            "pie": f"[{jugador.nombre_tecla('interactuar')}] seguir",
        })

    # -- Habilidades -------------------------------------------------------------

    def alternar_habilidades(self, jugador):
        if jugador.panel is not None and jugador.panel.get("tipo") == "habilidades":
            jugador.cerrar_panel()
        elif jugador.panel is None:
            jugador.abrir_panel({"tipo": "habilidades"})

    def _confirmar_habilidad(self, jugador):
        opciones = jugador.arbol.opciones()
        if not opciones:
            jugador.cerrar_panel()
            return
        indice = min(jugador.cursor, len(opciones) - 1)
        # Las habilidades se pagan con los puntos del EQUIPO (ver mision.Equipo).
        ok, mensaje, costo = jugador.arbol.desbloquear(opciones[indice].clave,
                                                       jugador.puntos_para_habilidades)
        if ok:
            if jugador.equipo is not None:
                jugador.equipo.gastar(costo)
            else:
                jugador.sumar_puntos(-costo)
            jugador.avisar(mensaje, (255, 214, 64))
            self.sonar("acierto", 0.7)
            jugador.cursor = 0
        else:
            jugador.avisar(mensaje, (245, 130, 120))

    # -- Entrada ------------------------------------------------------------------

    def _tecla_en_partida(self, key):
        """Reparte la tecla al jugador dueño de esa tecla.

        Cada rama sale con `return` SOLO si la tecla era de ese jugador. Antes,
        la rama del jugador con un panel abierto terminaba en un `return` suelto
        que se ejecutaba siempre, incluso cuando la tecla no era suya: mientras
        el jugador 1 tenía algo abierto se tragaba todas las teclas y el
        jugador 2 no podía abrir nada. Al revés no pasaba, porque el jugador 1
        se revisa primero y su rama sí hacía `continue`.
        """
        for jugador in self.jugadores:
            # Escondido manda sobre todo lo demás: la tecla de interactuar es
            # la del minijuego si un alien lo está revisando, y si no, la de
            # salir. Mientras está metido no abre habilidades ni zonas.
            # Encerrado en una celda: no puede hacer nada hasta que lo saquen.
            if jugador.preso is not None or jugador.eliminado:
                if any(jugador.es_tecla(key, a) for a in jugador.teclas):
                    return
                continue

            if jugador.escondido:
                if jugador.es_tecla(key, "interactuar"):
                    if jugador.minijuego is not None:
                        acierto = jugador.minijuego.presionar(jugador)
                        self.sonar("acierto" if acierto else "fallo", 0.6)
                    else:
                        jugador.salir_del_escondite()
                    return
                if jugador.es_tecla(key, "habilidades") or jugador.es_tecla(key, "habilidad"):
                    return
                continue

            # El mapa de la Emisión abierto: la tecla de habilidad o la del
            # árbol lo cierran sin gastar la habilidad.
            if (jugador.panel is not None and jugador.panel.get("tipo") == "emision"
                    and (jugador.es_tecla(key, "habilidad") or jugador.es_tecla(key, "habilidades"))):
                jugador.cerrar_panel()
                return

            if jugador.es_tecla(key, "habilidades"):
                self.alternar_habilidades(jugador)
                return

            if jugador.es_tecla(key, "habilidad"):
                if (self.en_tutorial and not jugador.ocupado
                        and not self.tutorial.esta_listo(jugador)):
                    # En el tutorial, la tecla de habilidad pasa de paso.
                    self.tutorial.siguiente(jugador)
                    self.sonar("menu_ok", 0.5)
                    if not self.tutorial.activo:
                        self._terminar_tutorial()
                    return
                if not jugador.ocupado:
                    acciones_rol.usar_habilidad(self, jugador)
                return

            if not jugador.ocupado:
                if jugador.es_tecla(key, "interactuar"):
                    # Lo de la misión (celdas, puerta, notas, cápsula...) va
                    # primero; después zona, estación de su rol y escondite.
                    if self.eventos is not None and self.eventos.caja_cerca(jugador):
                        jugador.avisar("Mantén la tecla para cambiar los fusibles.", (255, 214, 64))
                        return
                    if self.eventos is not None and self.eventos.caja_falsa_cerca(jugador):
                        jugador.avisar("Esta caja está bien. Busquen la que parpadea en rojo.",
                                       (245, 130, 120))
                        return
                    if puertas.panel_cerca(self.puertas_dobles, jugador) is not None:
                        jugador.avisar("Mantén la tecla aquí mientras otro mantiene el otro panel.",
                                       (255, 214, 64))
                        return
                    if self.mision is not None and self.mision.interactuar(jugador):
                        return
                    if self.infiltrado is not None and self.infiltrado.interactuar(jugador):
                        return
                    estacion = (None if self.zona_bajo(jugador)
                                else acciones_rol.estacion_bajo(self, jugador))
                    escondite = (None if self.zona_bajo(jugador) or estacion
                                 else self.escondite_bajo(jugador))
                    if estacion is not None:
                        acciones_rol.usar_estacion(self, jugador, estacion)
                    elif escondite is not None:
                        jugador.esconderse(escondite)
                    else:
                        self.interactuar(jugador)
                    return
                continue  # no era suya: que la vea el siguiente

            total = self._total_opciones(jugador)
            if jugador.es_tecla(key, "arriba"):
                jugador.mover_cursor(-1, total)
                self.sonar("menu_mover", 0.35)
                return
            if jugador.es_tecla(key, "abajo"):
                jugador.mover_cursor(1, total)
                self.sonar("menu_mover", 0.35)
                return
            if jugador.es_tecla(key, "interactuar"):
                self.sonar("menu_ok", 0.4)
                self.confirmar(jugador)
                return
            # Tampoco era suya aunque tenga un panel abierto: se sigue buscando.

    def _total_opciones(self, jugador):
        panel = jugador.panel or {}
        if panel.get("tipo") == "habilidades":
            return len(jugador.arbol.opciones())
        return len(panel.get("opciones", []))

    # -- Loop principal -------------------------------------------------------------

    def run(self):
        while self.running:
            dt = self.clock.tick(DEFAULT_FPS)
            self._manejar_eventos()
            self._sonido_de_fondo()
            if self.current_screen == "partida" and self.transitions.is_idle():
                if self.pausa is not None:
                    self.pausa.actualizar(dt)   # el juego queda congelado
                else:
                    self._actualizar_partida(dt)
            self.transitions.update(self, dt)
            self._dibujar()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _sonido_de_fondo(self):
        """El zumbido de la nave suena durante la partida; se calla en los
        apagones (las máquinas se apagan) y baja en la pausa."""
        if self.current_screen == "partida" and self.mundo is not None:
            if self.eventos is not None and self.eventos.apagon:
                volumen = 0.0
            else:
                volumen = 0.12 if self.pausa is not None else 0.35
            audio_manager.bucle("ambiente", volumen)
        elif audio_manager.sonando_bucle:
            audio_manager.parar_bucle()

    def _manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.running = False
            elif evento.type == pygame.KEYDOWN:
                self._manejar_tecla(evento.key)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._manejar_click(evento.pos)
            elif evento.type == pygame.MOUSEMOTION and self.current_screen == "partida":
                if self.pausa is not None:
                    self.pausa.mover_mouse(evento.pos)
                else:
                    self._mouse_en_mapa(evento.pos)
            elif evento.type in (pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION,
                                 pygame.JOYAXISMOTION, pygame.JOYDEVICEADDED,
                                 pygame.JOYDEVICEREMOVED):
                for puesto, accion in self.mandos.evento(evento):
                    self._tecla_mando(puesto, accion)
                if evento.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                    self._sincronizar_mandos()

    def _tecla_mando(self, puesto, accion):
        """Un botón del mando: en partida y en la selección de rol es la tecla
        virtual de ese jugador; en los menús hace de flechas, Enter y Esc."""
        if self.current_screen == "partida" and (self.pausa is not None or accion == "pausa"):
            # START abre la pausa; con la pausa abierta el mando la maneja
            # como en los menús (cruceta, A para aceptar, B o START para volver).
            tecla = {"arriba": pygame.K_UP, "abajo": pygame.K_DOWN,
                     "izquierda": pygame.K_LEFT, "derecha": pygame.K_RIGHT,
                     "interactuar": pygame.K_RETURN, "volver": pygame.K_ESCAPE,
                     "pausa": pygame.K_ESCAPE}.get(accion)
            if tecla is not None:
                self._manejar_tecla(tecla)
            return
        if accion in ("izquierda", "derecha"):
            return     # fuera del árbol de logros no hacen nada (el stick ya mueve)
        if accion == "pausa":
            accion = "volver" if self.current_screen == "roles" else "interactuar"
        if self.current_screen in ("partida", "roles"):
            if accion == "volver":
                jugador = next((j for j in self.jugadores if j.puesto == puesto), None)
                if self.current_screen == "partida" and jugador is not None and jugador.ocupado:
                    jugador.cerrar_panel()
                return
            self._manejar_tecla(tecla_virtual(puesto, accion))
            return
        tecla = {"arriba": pygame.K_UP, "abajo": pygame.K_DOWN,
                 "interactuar": pygame.K_RETURN}.get(accion)
        if accion == "volver" and self.current_screen != "menu":
            tecla = pygame.K_ESCAPE   # en el menú, Esc cierra el juego: ahí B no hace nada
        if tecla is not None:
            self._manejar_tecla(tecla)

    def _sincronizar_mandos(self):
        """Se conectó o desconectó un mando con la partida andando."""
        for jugador in self.jugadores:
            if jugador.puesto in PUESTOS_CON_MANDO:
                jugador.con_mando = self.mandos.hay_mando(jugador.puesto)
                jugador.puede_moverse = jugador.con_mando and not jugador.eliminado
                jugador.controles_nombre = (f"Mando {jugador.puesto - 1}" if jugador.con_mando
                                            else NOMBRE_CONTROLES[jugador.puesto])

    def _manejar_tecla(self, key):
        if key == pygame.K_F11:
            self.alternar_pantalla_completa()
            return
        if self.transitions.active:
            return
        if self.current_screen in ("menu", "cantidad", "roles") or (
                self.current_screen == "partida" and self.pausa is not None):
            if key in TECLAS_MOVER_MENU:
                self.sonar("menu_mover", 0.5)
            elif key in TECLAS_OK_MENU:
                self.sonar("menu_ok", 0.6)

        if self.current_screen == "menu":
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_selected = (self.menu_selected - 1) % len(self.menu_buttons)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selected = (self.menu_selected + 1) % len(self.menu_buttons)
            elif key == pygame.K_RETURN:
                self._activar_opcion_menu(self.menu_buttons[self.menu_selected].action)
            elif key == pygame.K_ESCAPE:
                self.running = False

        elif self.current_screen == "cantidad":
            if key in (pygame.K_UP, pygame.K_w):
                self.cantidad_seleccionada = (self.cantidad_seleccionada - 1) % len(OPCIONES)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.cantidad_seleccionada = (self.cantidad_seleccionada + 1) % len(OPCIONES)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.confirmar_cantidad()
            elif key == pygame.K_ESCAPE:
                self.transitions.request(self, "menu")

        elif self.current_screen == "roles":
            if key == pygame.K_ESCAPE:
                self.transitions.request(self, "cantidad")
            else:
                self._tecla_en_seleccion(key)

        elif self.current_screen == "partida" and self.pausa is not None:
            self._accion_pausa(self.pausa.tecla(key))

        elif self.current_screen == "partida":
            if key == pygame.K_h:
                self.mostrar_hitboxes = not self.mostrar_hitboxes
            elif key == pygame.K_b:
                self.mostrar_arbol_alien = not self.mostrar_arbol_alien
            elif key == pygame.K_l:
                self.oscuridad = not self.oscuridad
            elif key == pygame.K_n and self.aliens:
                self.alien_en_vista = (self.alien_en_vista + 1) % len(self.aliens)
            elif key == pygame.K_ESCAPE:
                self.pausa = MenuPausa(self)
                self.sonar("pausa", 0.6)
            else:
                self._tecla_en_partida(key)

        elif self.current_screen == "resultados":
            if key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.transitions.request(self, "menu")

        elif self.current_screen in ("ayuda", "creditos"):
            if key in (pygame.K_RETURN, pygame.K_BACKSPACE, pygame.K_ESCAPE):
                self.transitions.request(self, self.pantalla_anterior)

    def _accion_pausa(self, accion):
        """Lo que pidió el menú de pausa (pausa.py)."""
        if accion == "continuar":
            self.pausa = None
        elif accion == "terminar":
            self.pausa = None
            for jugador in self.jugadores:
                jugador.cerrar_panel()
            self.transitions.request(self, "menu")
        elif accion == "pantalla_completa":
            self.alternar_pantalla_completa()

    def _jugador_con_mapa_en(self, pos):
        """(jugador, punto del mundo) si `pos` cae en el mapa de la Emisión de
        alguien, o (None, None)."""
        for jugador in self.jugadores:
            panel = jugador.panel
            if panel is None or panel.get("tipo") != "emision" or "rect_mapa" not in panel:
                continue
            rect, escala = panel["rect_mapa"], panel["escala_mapa"]
            if rect.collidepoint(pos):
                return jugador, ((pos[0] - rect.x) / escala, (pos[1] - rect.y) / escala)
        return None, None

    def _mouse_en_mapa(self, pos):
        jugador, punto = self._jugador_con_mapa_en(pos)
        if jugador is not None:
            jugador.panel["cursor_mapa"] = [punto[0], punto[1]]

    def _manejar_click(self, pos):
        if self.current_screen == "partida":
            if self.pausa is not None:
                if not self.transitions.active:
                    self._accion_pausa(self.pausa.click(pos))
                return
            jugador, punto = self._jugador_con_mapa_en(pos)
            if jugador is not None:
                acciones_rol.poner_emision(self, jugador, punto)
            return
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
            self.abrir_cantidad()
        elif accion == "salir":
            self.running = False
        else:
            # Los créditos siempre arrancan desde el principio: si no, entrar y
            # salir varias veces los retomaba a mitad de camino.
            if accion == "creditos":
                self.credit_scroll = reiniciar_scroll()
            self.pantalla_anterior = "menu"
            self.transitions.request(self, accion)

    # -- Dibujo -----------------------------------------------------------------

    def _dibujar(self):
        if self.current_screen == "menu":
            render_menu(self.screen, self.menu_buttons, self.menu_selected)
        elif self.current_screen == "cantidad":
            render_cantidad(self.screen, self.cantidad_seleccionada)
        elif self.current_screen == "roles":
            viewports = calcular_viewports(self.ancho, self.alto, self.cantidad_jugadores)
            render_roles(self.screen, viewports, self.seleccion_roles)
        elif self.current_screen == "partida":
            render_partida(self.screen, self.mundo, self.jugadores, self.zonas,
                           self.tiempo_restante_ms / 1000.0, self.mostrar_hitboxes,
                           self.aliens, self.escondites, self._extras_dibujo())
            self.narrador.dibujar(self.screen)
            if self.mostrar_arbol_alien and self.aliens:
                render_arbol_alien(self.screen, self.aliens[self.alien_en_vista],
                                   self.arbol_alien, self.alien_en_vista + 1, len(self.aliens))
            if self.pausa is None:
                render_aviso_logro(self.screen, self.logros)
            else:
                render_pausa(self.screen, self.pausa)
        elif self.current_screen == "resultados":
            render_resultados(self.screen, self.jugadores,
                              self.font, self.small_font, self.mision, self.equipo,
                              self.infiltrado, self.logros)
        elif self.current_screen == "ayuda":
            render_ayuda(self.screen, self.small_font)
        elif self.current_screen == "creditos":
            self.credit_scroll = render_creditos(self.screen, self.small_font, self.credit_scroll)

        self.transitions.draw(self.screen)


if __name__ == "__main__":
    Game().run()
