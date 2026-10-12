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
from oscuridad import Linterna
from mandos import tecla_virtual, es_virtual, NOMBRE_BOTON


# Teclas de cada PUESTO, no de cada rol: el rol se escoge al empezar la
# partida, así que ya no se puede repartir el teclado por rol. El puesto 1
# juega con WASD, el 2 con las flechas.
#
# Los puestos 3 y 4 juegan con mando (mandos.py): cada botón es una "tecla
# virtual" que va al final de cada tupla. Las letras de teclado que tienen
# delante (I/K/O, T/G/Y...) siguen sirviendo para escoger rol sin mando; sin
# mando, en partida no se mueven.
# "habilidades" abre el panel del árbol; "habilidad" USA la habilidad activa
# que se haya escogido (ver acciones_rol.py).
TECLAS_PUESTO_1 = {
    "arriba": (pygame.K_w,),
    "abajo": (pygame.K_s,),
    "interactuar": (pygame.K_e,),
    "habilidades": (pygame.K_q,),
    "habilidad": (pygame.K_f,),
    "sigilo": (pygame.K_LSHIFT,),
}

TECLAS_PUESTO_2 = {
    "arriba": (pygame.K_UP,),
    "abajo": (pygame.K_DOWN,),
    "interactuar": (pygame.K_RETURN, pygame.K_KP_ENTER),
    "habilidades": (pygame.K_RSHIFT,),
    # La tecla "-" (junto al Shift derecho en los teclados en español; en los
    # de inglés es "/"). Ctrl derecho queda de respaldo: no todos los portátiles
    # lo tienen.
    "habilidad": (pygame.K_MINUS, pygame.K_SLASH, pygame.K_RCTRL),
    # AltGr en los teclados en español (SDL lo reporta como RALT o MODE), o
    # el 0 del teclado numérico, que queda junto a las flechas.
    "sigilo": (pygame.K_RALT, pygame.K_MODE, pygame.K_KP0),
}

def _con_mando(puesto, teclado):
    return {accion: tuple(teclas) + (tecla_virtual(puesto, accion),)
            for accion, teclas in teclado.items()}


TECLAS_PUESTO_3 = _con_mando(2, {
    "arriba": (pygame.K_i,),
    "abajo": (pygame.K_k,),
    "interactuar": (pygame.K_o,),
    "habilidades": (pygame.K_u,),
    "habilidad": (pygame.K_p,),
    "sigilo": (),
})

TECLAS_PUESTO_4 = _con_mando(3, {
    "arriba": (pygame.K_t,),
    "abajo": (pygame.K_g,),
    "interactuar": (pygame.K_y,),
    "habilidades": (pygame.K_r,),
    "habilidad": (pygame.K_v,),
    "sigilo": (),
})

TECLAS_POR_PUESTO = [TECLAS_PUESTO_1, TECLAS_PUESTO_2, TECLAS_PUESTO_3, TECLAS_PUESTO_4]

# Cómo se llama su esquema de control en pantalla.
NOMBRE_CONTROLES = ["WASD", "Flechas", "Mando 1 (I/K/O)", "Mando 2 (T/G/Y)"]

# Puestos que solo se mueven si tienen un mando conectado.
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

# Caminar normal hace ruido de pasos además del latido; en sigilo (tecla
# mantenida) se va a la mitad de velocidad, sin pasos y con el ruido reducido.
RUIDO_PASOS = 45
FACTOR_RUIDO_SIGILO = 0.6
FACTOR_VELOCIDAD_SIGILO = 0.5
PULSO_EXTRA_SIGILO = 3

# Después de que lo atrapan, un rato en que los aliens no lo persiguen, para
# que no lo vuelvan a atrapar apenas reaparece.
INVULNERABLE_MS = 2500

# Teclado "todo suelto": se le pasa a Personaje.actualizar cuando el jugador
# tiene un panel abierto, para que siga animándose quieto en vez de caminar
# mientras lee. Es un defaultdict porque Personaje indexa por código de tecla.
SIN_TECLAS = defaultdict(bool)


class Jugador:
    def __init__(self, personaje, rol, puesto=0, con_mando=False):
        self.personaje = personaje
        self.puesto = puesto
        self.teclas = TECLAS_POR_PUESTO[puesto % len(TECLAS_POR_PUESTO)]
        self.con_mando = con_mando
        self.controles_nombre = (f"Mando {puesto - 1}" if con_mando
                                 else NOMBRE_CONTROLES[puesto % len(NOMBRE_CONTROLES)])
        self.puede_moverse = puesto not in PUESTOS_SIN_MOVIMIENTO or con_mando

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
        self.sigilo = False          # mantiene la tecla de sigilo
        self.linterna = Linterna()   # hacia dónde alumbra (oscuridad.py)
        self.velocidad_base = personaje.velocidad
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

        # Misión (mision.py): la celda donde está encerrado (None = libre), los
        # consumibles que lleva ("decodificador", "kit"), lo que está haciendo
        # con la tecla mantenida (texto, 0 a 1) y el equipo con el que suma
        # puntos para las habilidades.
        self.preso = None
        self.objetos = set()
        self.progreso = None
        self.equipo = None
        self.pista_mision = None
        self.susto_ms = 0            # cuánto le queda al susto de ser atrapado
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
        if getattr(self, "con_mando", False) and any(es_virtual(t) for t in teclas):
            return NOMBRE_BOTON.get(accion, "?")
        teclas = [t for t in teclas if not es_virtual(t)]
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
            pygame.K_LSHIFT: "SHIFT IZQ", pygame.K_RALT: "ALT GR",
            pygame.K_MINUS: "-", pygame.K_SLASH: "/",
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
        if getattr(self, "con_mando", False):
            return "Stick"
        if pygame.K_UP in self.teclas.get("arriba", ()):
            return "Flechas"
        return f"{self.nombre_tecla('arriba')}/{self.nombre_tecla('abajo')}"

    # -- Pulso y aliens ------------------------------------------------------------

    @property
    def radio_ruido(self):
        """Hasta dónde se oye su latido, en píxeles del mundo."""
        radio = RADIO_RUIDO_BASE + self.pulso * RADIO_RUIDO_POR_PULSO
        if self.escondido:
            return radio * FACTOR_RUIDO_ESCONDIDO
        if self.sigilo:
            return radio * FACTOR_RUIDO_SIGILO
        if self.personaje.moviendose:
            radio += RUIDO_PASOS
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
        return self.puede_moverse and self.invulnerable_ms <= 0 and self.preso is None

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
            objetivo += PULSO_EXTRA_SIGILO if self.sigilo else PULSO_EXTRA_CAMINANDO
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
        # Lo que gana cada uno también le suma al equipo, que es con lo que se
        # desbloquean las habilidades.
        if self.equipo is not None:
            self.equipo.sumar(int(cantidad))

    @property
    def puntos_para_habilidades(self):
        return self.equipo.puntos if self.equipo is not None else self.puntos

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
        if self.ocupado or self.escondido or self.preso or not self.puede_moverse:
            self.sigilo = False
            self.personaje.actualizar(SIN_TECLAS, colisiona=colisiona)
            return
        self.sigilo = any(teclas[k] for k in self.teclas.get("sigilo", ()))
        self.personaje.velocidad = self.velocidad_base * (
            FACTOR_VELOCIDAD_SIGILO if self.sigilo else 1.0)
        self.personaje.actualizar(teclas, colisiona=colisiona)
        self.linterna.actualizar(self.personaje.direccion)

    def dibujar(self, screen, offset):
        if self.escondido:
            return   # metido en el escondite: no se ve
        self.personaje.dibujar(screen, offset)
