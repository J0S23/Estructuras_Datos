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
# "habilidades" abre el panel del árbol; "habilidad" USA la habilidad activa
# que se haya escogido (ver acciones_rol.py).
TECLAS_PUESTO_1 = {
    "arriba": (pygame.K_w,),
    "abajo": (pygame.K_s,),
    "interactuar": (pygame.K_e,),
    "habilidades": (pygame.K_q,),
    "habilidad": (pygame.K_f,),
}

TECLAS_PUESTO_2 = {
    "arriba": (pygame.K_UP,),
    "abajo": (pygame.K_DOWN,),
    "interactuar": (pygame.K_RETURN, pygame.K_KP_ENTER),
    "habilidades": (pygame.K_RSHIFT,),
    "habilidad": (pygame.K_RCTRL,),
}

TECLAS_PUESTO_3 = {
    "arriba": (pygame.K_i,),
    "abajo": (pygame.K_k,),
    "interactuar": (pygame.K_o,),
    "habilidades": (pygame.K_u,),
    "habilidad": (pygame.K_p,),
}

TECLAS_PUESTO_4 = {
    "arriba": (pygame.K_t,),
    "abajo": (pygame.K_g,),
    "interactuar": (pygame.K_y,),
    "habilidades": (pygame.K_r,),
    "habilidad": (pygame.K_v,),
}

TECLAS_POR_PUESTO = [TECLAS_PUESTO_1, TECLAS_PUESTO_2, TECLAS_PUESTO_3, TECLAS_PUESTO_4]

# Cómo se llama su esquema de control en pantalla.
NOMBRE_CONTROLES = ["WASD", "Flechas", "Mando 1 (I/K/O)", "Mando 2 (T/G/Y)"]

# Puestos que todavía no se pueden mover.
PUESTOS_SIN_MOVIMIENTO = (2, 3)

# Cuánto dura el mensajito de feedback ("+15 puntos") sobre el personaje.
DURACION_MENSAJE_MS = 2200

# -- Pulso -------------------------------------------------------------------
# El pulso va de 0 a 100 y decide cuánto ruido hace el jugador: un alien que
# esté dentro de `radio_ruido` lo oye aunque no lo vea. Sube cuando hay un
# alien cerca (más entre más cerca) y se dispara si un alien lo está viendo;
# baja cuando está lejos y quieto.
PULSO_REPOSO = 18          # quieto y sin aliens cerca
PULSO_EXTRA_CAMINANDO = 12
PULSO_POR_CERCANIA = 62    # cuánto suma un alien pegado a él
DISTANCIA_QUE_ASUSTA = 400 # a partir de aquí un alien ya no sube el pulso
PULSO_SUBE_POR_S = 34
PULSO_BAJA_POR_S = 11
RADIO_RUIDO_BASE = 40
RADIO_RUIDO_POR_PULSO = 2.6

# Escondido, el latido se oye menos: el radio de ruido se multiplica por esto.
FACTOR_RUIDO_ESCONDIDO = 0.55

# Después de que lo atrapan, un rato en que los aliens no lo persiguen, para
# que no lo vuelvan a atrapar apenas reaparece.
INVULNERABLE_MS = 2500

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

        # Pulso (ver PULSO_* arriba) y la fase de su latido, que solo sirve
        # para animar el corazón del HUD al ritmo del pulso.
        self.pulso = float(PULSO_REPOSO)
        self.fase_latido = 0.0
        self.visto = False
        self.spawn = None            # dónde reaparece si lo atrapan

        # Escondites: en cuál está metido (None = afuera), cuál tiene cerca
        # para la pista de "presiona E", y el minijuego si un alien lo revisa.
        self.escondite = None
        self.escondite_cerca = None
        self.minijuego = None

        # Habilidades del rol (acciones_rol.py): recarga de la activa, efectos
        # con tiempo (nombre -> ms restantes), piezas del Forjador y la
        # estación que tiene enfrente, para la pista de "presiona E".
        self.recarga_ms = 0
        self.efectos = {}
        self.piezas = 0
        self.estacion_cerca = None
        self.invulnerable_ms = 0
        self.veces_atrapado = 0

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
            pygame.K_UP: "ARRIBA", pygame.K_DOWN: "ABAJO",
            pygame.K_RETURN: "ENTER", pygame.K_KP_ENTER: "ENTER",
            pygame.K_RSHIFT: "SHIFT DER", pygame.K_RCTRL: "CTRL DER",
            pygame.K_f: "F", pygame.K_p: "P", pygame.K_v: "V",
            pygame.K_i: "I", pygame.K_k: "K", pygame.K_o: "O", pygame.K_u: "U",
            pygame.K_t: "T", pygame.K_g: "G", pygame.K_y: "Y", pygame.K_r: "R",
        }
        return nombres.get(teclas[0], "?")

    def pista_mover(self):
        """Cómo se nombra en pantalla el par de teclas para mover el cursor.

        Para el puesto de las flechas devuelve "Flechas" en vez de los nombres
        sueltos: la tipografía del juego (Determination Mono) **no trae los
        glifos de flecha** (U+2190-2193), así que escribir "↑/↓" salía como dos
        cuadritos vacíos. Las tildes y la ñ sí están; el problema era solo con
        las flechas.
        """
        if pygame.K_UP in self.teclas.get("arriba", ()):
            return "Flechas"
        return f"{self.nombre_tecla('arriba')}/{self.nombre_tecla('abajo')}"

    # -- Pulso y aliens ------------------------------------------------------------

    @property
    def radio_ruido(self):
        """Hasta dónde se oye su latido, en píxeles del mundo."""
        radio = RADIO_RUIDO_BASE + self.pulso * RADIO_RUIDO_POR_PULSO
        if self.escondido:
            radio *= FACTOR_RUIDO_ESCONDIDO
        return radio

    @property
    def escondido(self):
        return self.escondite is not None

    def esconderse(self, escondite):
        """Se mete al escondite: deja de verse y de moverse."""
        self.escondite = escondite
        escondite["ocupante"] = self
        # Se para en la entrada, para que al salir quede en el mismo sitio.
        self.personaje.hitbox.center = escondite["rect"].center
        self.personaje.sync_sprite_from_hitbox()

    def salir_del_escondite(self):
        if self.escondite is not None:
            self.escondite["ocupante"] = None
        self.escondite = None
        self.minijuego = None

    @property
    def cazable(self):
        """Si los aliens lo pueden ver, oír y atrapar.

        Los puestos sin mando todavía no se mueven: si los aliens los cazaran,
        los atraparían una y otra vez sin que el jugador pudiera hacer nada.
        """
        return self.puede_moverse and self.invulnerable_ms <= 0

    @property
    def latidos_por_minuto(self):
        return int(60 + self.pulso * 1.1)

    def actualizar_pulso(self, dt, distancia_alien=None, visto=False):
        """Acerca el pulso a lo que "debería" ser con lo que está pasando.

        No salta de golpe: sube y baja a una velocidad fija, así que pasar
        rápido junto a un alien es menos peligroso que quedarse cerca.

        Mientras dura el minijuego del escondite el pulso solo lo mueven los
        aciertos y fallos (ver minijuego_latidos.py): aquí únicamente avanza
        la animación del latido.
        """
        self.visto = visto
        self.invulnerable_ms = max(0, self.invulnerable_ms - dt)
        segundos = dt / 1000
        if self.minijuego is not None:
            self.fase_latido = (self.fase_latido + self.latidos_por_minuto / 60 * segundos) % 1.0
            return

        objetivo = PULSO_REPOSO
        if self.personaje.moviendose:
            objetivo += PULSO_EXTRA_CAMINANDO
        if distancia_alien is not None and distancia_alien < DISTANCIA_QUE_ASUSTA:
            objetivo += PULSO_POR_CERCANIA * (1 - distancia_alien / DISTANCIA_QUE_ASUSTA)
        if visto:
            objetivo = 100

        if self.pulso < objetivo:
            self.pulso = min(objetivo, self.pulso + PULSO_SUBE_POR_S * segundos)
        else:
            self.pulso = max(objetivo, self.pulso - PULSO_BAJA_POR_S * segundos)
        self.pulso = max(0.0, min(100.0, self.pulso))

        self.fase_latido = (self.fase_latido + self.latidos_por_minuto / 60 * segundos) % 1.0

    def atrapado(self):
        """Lo atrapó un alien: vuelve a su punto de inicio y pierde puntos."""
        self.veces_atrapado += 1
        self.invulnerable_ms = INVULNERABLE_MS
        self.pulso = 45.0
        self.cerrar_panel()
        self.salir_del_escondite()
        if self.spawn is not None:
            self.personaje.hitbox.topleft = self.spawn
            self.personaje.sync_sprite_from_hitbox()

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
        """Mueve al personaje, salvo que tenga un panel abierto, esté escondido
        o no tenga mando."""
        if self.ocupado or self.escondido or not self.puede_moverse:
            self.personaje.actualizar(SIN_TECLAS, colisiona=colisiona)
            return
        self.personaje.actualizar(teclas, colisiona=colisiona)

    def dibujar(self, screen, offset):
        if self.escondido:
            return   # metido en el escondite: no se ve
        self.personaje.dibujar(screen, offset)
