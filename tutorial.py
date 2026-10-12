"""Tutorial de 30 segundos al empezar la partida.

En la feria la gente se sienta a jugar sin haber leído nada. Antes de que los
aliens despierten, cada jugador ve en su mitad de la pantalla unos pasos
cortos. Los de moverse se completan haciéndolos; los demás pasan solos tras
unos segundos. Mientras dura:

- los aliens duermen (no se mueven ni ven ni oyen),
- el reloj de la misión no corre,
- no hay eventos aleatorios.

Termina cuando todos los que se pueden mover acabaron los pasos, cuando cada
uno presiona su tecla de habilidad para saltarlo, o a los 30 segundos.
"""

DURACION_S = 30
MS_PASO_LECTURA = 4200
MS_SIGILO_NECESARIO = 700

# {mover}, {sigilo}, {interactuar}, {habilidad} y {habilidades} se cambian por
# las teclas de cada jugador. "accion" dice cómo se completa el paso.
PASOS = [
    {"texto": "Muévete con {mover}.", "accion": "mover"},
    {"texto": "Mantén {sigilo} mientras caminas: vas lento pero casi no haces ruido.",
     "accion": "sigilo"},
    {"texto": "El anillo a tu alrededor es tu ruido. Si un alien queda adentro, te oye. "
              "Entre más asustado, más grande.", "accion": "leer"},
    {"texto": "Si se va la luz, solo alumbra tu linterna y de los aliens solo ves los "
              "ojos. Busquen la caja de fusibles que parpadea en rojo y enciéndanla.",
     "accion": "leer"},
    {"texto": "{interactuar}: usar, leer notas y esconderte. Si te atrapan vas a una "
              "celda y tus compañeros te sacan.", "accion": "leer"},
    {"texto": "{habilidad}: usar tu habilidad.  {habilidades}: árbol de habilidades. "
              "¡Escapen juntos!", "accion": "leer"},
]


class Tutorial:
    def __init__(self, jugadores, duracion_s=DURACION_S):
        self.restante_ms = duracion_s * 1000
        self.activo = True
        self.estado = {id(j): {"paso": 0, "ms": 0, "sigilo_ms": 0, "listo": False}
                       for j in jugadores}
        self.jugadores = list(jugadores)

    def _de(self, jugador):
        return self.estado.setdefault(id(jugador), {"paso": 0, "ms": 0, "sigilo_ms": 0,
                                                    "listo": False})

    def actualizar(self, dt):
        if not self.activo:
            return
        self.restante_ms -= dt
        for jugador in self.jugadores:
            e = self._de(jugador)
            if e["listo"]:
                continue
            paso = PASOS[e["paso"]]
            e["ms"] += dt
            hecho = False
            if paso["accion"] == "mover":
                hecho = jugador.personaje.moviendose or e["ms"] > 6000
            elif paso["accion"] == "sigilo":
                if jugador.personaje.moviendose and jugador.sigilo:
                    e["sigilo_ms"] += dt
                hecho = e["sigilo_ms"] >= MS_SIGILO_NECESARIO or e["ms"] > 8000
            else:
                hecho = e["ms"] >= MS_PASO_LECTURA
            if hecho:
                e["paso"] += 1
                e["ms"] = 0
                if e["paso"] >= len(PASOS):
                    e["paso"] = len(PASOS) - 1
                    e["listo"] = True
        moviles = [j for j in self.jugadores if j.puede_moverse] or self.jugadores
        if self.restante_ms <= 0 or all(self._de(j)["listo"] for j in moviles):
            self.activo = False

    def saltar(self, jugador):
        e = self._de(jugador)
        e["listo"] = True
        e["paso"] = len(PASOS) - 1
        self.actualizar(0)

    def texto(self, jugador):
        """(número de paso, total, texto ya con sus teclas) o None si ya acabó."""
        if not self.activo:
            return None
        e = self._de(jugador)
        if e["listo"]:
            return (len(PASOS), len(PASOS), "¡Listo! Esperando a los demás...")
        mover = "WASD" if jugador.puesto == 0 else "las flechas" if jugador.puesto == 1 \
            else "el stick" if getattr(jugador, "con_mando", False) else jugador.controles_nombre
        texto = PASOS[e["paso"]]["texto"].format(
            mover=mover, sigilo=jugador.nombre_tecla("sigilo"),
            interactuar=jugador.nombre_tecla("interactuar"),
            habilidad=jugador.nombre_tecla("habilidad"),
            habilidades=jugador.nombre_tecla("habilidades"))
        return (e["paso"] + 1, len(PASOS), texto)

    @property
    def segundos(self):
        return max(0, self.restante_ms) // 1000 + 1
