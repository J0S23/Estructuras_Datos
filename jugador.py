"""Un jugador de la partida: su personaje, su rol, sus puntos y su progresión.

Antes `Game.jugadores` era una lista de `Personaje`. Ahora cada entrada es un
`Jugador`, que envuelve al personaje y le agrega todo lo que es del jugador y
no del muñeco: el rol, los puntos, su árbol de habilidades y el panel que
tenga abierto en su mitad de la pantalla.

Cada jugador tiene su propio juego de teclas, incluidas las de navegar los
paneles, porque la partida es local y los dos juegan en el mismo teclado: si
compartieran las teclas de elegir opción, uno le respondería los diálogos al
otro.
"""

from collections import defaultdict

import pygame

from Estructuras.arbol_habilidades import construir_arbol
from data.habilidades import ARBOLES_POR_ROL
from data.tareas import OBJETIVOS


# Teclas de cada PUESTO, no de cada rol: el rol se escoge al empezar la
# partida, así que ya no se puede repartir el teclado por rol. El puesto 1
# juega con WASD, el 2 con las flechas.
#
# Los puestos 3 y 4 llevan teclas **provisionales**, y solo sirven para la
# pantalla de selección de rol: en partida no se mueven porque les toca mando y
# eso todavía no está hecho. Cuando se implemente, se cambia solo este bloque.
TECLAS_PUESTO_1 = {
    "arriba": (pygame.K_w,),
    "abajo": (pygame.K_s,),
    "interactuar": (pygame.K_e,),
    "habilidades": (pygame.K_q,),
}

TECLAS_PUESTO_2 = {
    "arriba": (pygame.K_UP,),
    "abajo": (pygame.K_DOWN,),
    "interactuar": (pygame.K_RETURN, pygame.K_KP_ENTER),
    "habilidades": (pygame.K_RSHIFT,),
}

TECLAS_PUESTO_3 = {
    "arriba": (pygame.K_i,),
    "abajo": (pygame.K_k,),
    "interactuar": (pygame.K_o,),
    "habilidades": (pygame.K_u,),
}

TECLAS_PUESTO_4 = {
    "arriba": (pygame.K_t,),
    "abajo": (pygame.K_g,),
    "interactuar": (pygame.K_y,),
    "habilidades": (pygame.K_r,),
}

TECLAS_POR_PUESTO = [TECLAS_PUESTO_1, TECLAS_PUESTO_2, TECLAS_PUESTO_3, TECLAS_PUESTO_4]

# Cómo se llama su esquema de control en pantalla.
NOMBRE_CONTROLES = ["WASD", "Flechas", "Mando 1 (I/K/O)", "Mando 2 (T/G/Y)"]

# Puestos que todavía no se pueden mover.
PUESTOS_SIN_MOVIMIENTO = (2, 3)

# Cuánto dura el mensajito de feedback ("+15 puntos") sobre el personaje.
DURACION_MENSAJE_MS = 2200

# Teclado "todo suelto": se le pasa a Personaje.actualizar cuando el jugador
# tiene un panel abierto, para que siga animándose quieto en vez de caminar
# mientras lee. Es un defaultdict porque Personaje indexa por código de tecla.
SIN_TECLAS = defaultdict(bool)


class Jugador:
    def __init__(self, personaje, rol, puesto=0):
        self.personaje = personaje
        self.puesto = puesto
        self.teclas = TECLAS_POR_PUESTO[puesto % len(TECLAS_POR_PUESTO)]
        self.controles_nombre = NOMBRE_CONTROLES[puesto % len(NOMBRE_CONTROLES)]
        self.puede_moverse = puesto not in PUESTOS_SIN_MOVIMIENTO

        self.puntos = 0
        self.tareas_hechas = 0
        self.rol = None
        self.objetivo = ""
        self.arbol = construir_arbol("", None)
        self.asignar_rol(rol)

        # Panel abierto en su viewport (None = está caminando por el mapa).
        self.panel = None
        self.cursor = 0

        # Mensaje corto de feedback y su tiempo restante.
        self.mensaje = ""
        self.mensaje_color = (255, 255, 255)
        self.mensaje_ms = 0

        # Zona del mapa sobre la que está parado, para la pista de "presiona E".
        self.zona_cerca = None

        # Línea extra del HUD, propia de cada rol. El ciudadano la usa para el
        # aviso de cuántas cadenas dudosas siguen circulando, que sale de la
        # búsqueda por rango del ABB.
        self.info = ""

    def asignar_rol(self, rol):
        """Le da un rol al jugador y rearma lo que depende de él.

        Se llama al terminar la selección, no en el constructor, porque el
        jugador existe desde antes de que sepa qué va a jugar.
        """
        self.rol = rol
        self.objetivo = OBJETIVOS.get(rol, "")
        self.arbol = construir_arbol(rol, ARBOLES_POR_ROL.get(rol))

    # -- Estado ----------------------------------------------------------------

    @property
    def ocupado(self):
        """True si tiene un panel abierto: mientras tanto no camina."""
        return self.panel is not None

    def es_tecla(self, key, accion):
        return key in self.teclas.get(accion, ())

    def nombre_tecla(self, accion):
        """Nombre legible de su tecla, para las pistas en pantalla."""
        teclas = self.teclas.get(accion, ())
        if not teclas:
            return "?"
        nombres = {
            pygame.K_w: "W", pygame.K_s: "S", pygame.K_e: "E", pygame.K_q: "Q",
            pygame.K_UP: "↑", pygame.K_DOWN: "↓",
            pygame.K_RETURN: "ENTER", pygame.K_KP_ENTER: "ENTER",
            pygame.K_RSHIFT: "SHIFT DER",
            pygame.K_i: "I", pygame.K_k: "K", pygame.K_o: "O", pygame.K_u: "U",
            pygame.K_t: "T", pygame.K_g: "G", pygame.K_y: "Y", pygame.K_r: "R",
        }
        return nombres.get(teclas[0], "?")

    # -- Puntos y mensajes ------------------------------------------------------

    def sumar_puntos(self, cantidad):
        self.puntos = max(0, self.puntos + int(cantidad))

    def avisar(self, texto, color=(255, 255, 255)):
        self.mensaje = texto
        self.mensaje_color = color
        self.mensaje_ms = DURACION_MENSAJE_MS

    def actualizar_mensaje(self, dt):
        if self.mensaje_ms > 0:
            self.mensaje_ms = max(0, self.mensaje_ms - dt)
            if self.mensaje_ms == 0:
                self.mensaje = ""

    # -- Paneles ----------------------------------------------------------------

    def abrir_panel(self, panel):
        self.panel = panel
        self.cursor = 0

    def cerrar_panel(self):
        self.panel = None
        self.cursor = 0

    def mover_cursor(self, delta, total):
        if total <= 0:
            self.cursor = 0
            return
        self.cursor = (self.cursor + delta) % total

    # -- Atajos al personaje -----------------------------------------------------

    @property
    def hitbox(self):
        return self.personaje.hitbox

    def actualizar(self, teclas, colisiona):
        """Mueve al personaje, salvo que tenga un panel abierto o no tenga mando."""
        if self.ocupado or not self.puede_moverse:
            self.personaje.actualizar(SIN_TECLAS, colisiona=colisiona)
            return
        self.personaje.actualizar(teclas, colisiona=colisiona)

    def dibujar(self, screen, offset):
        self.personaje.dibujar(screen, offset)
