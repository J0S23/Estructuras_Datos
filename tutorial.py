"""Tutorial al empezar la partida, sin tiempo: cada quien va a su ritmo.

En la feria la gente se sienta a jugar sin haber leído nada. Antes de que los
aliens despierten, cada jugador ve en su pantalla unos pasos cortos y pasa al
siguiente con su tecla de habilidad cuando ya lo leyó. Los de moverse y
caminar en sigilo también se completan solos al hacerlos. Mientras dura:

- los aliens duermen (no se mueven ni ven ni oyen),
- el reloj de la misión no corre,
- no hay eventos aleatorios,
- la puerta de la prisión no abre (mision.py pregunta `juego.en_tutorial`),
  para que nadie avance con los aliens dormidos.

Termina, y la nave "arranca", solo cuando todos los que se pueden mover
terminaron sus pasos. Quien acaba primero puede caminar por la prisión
mientras espera a los demás.
"""

MS_SIGILO_NECESARIO = 700

# {mover}, {sigilo}, {interactuar}, {habilidad} y {habilidades} se cambian por
# las teclas de cada jugador. "accion" dice si además se completa haciéndolo.
PASOS = [
    {"texto": "Muévete con {mover}.", "accion": "mover"},
    {"texto": "Mantén {sigilo} mientras caminas: vas lento pero casi no haces ruido.",
     "accion": "sigilo"},
    {"texto": "El anillo a tu alrededor es tu ruido. Si un alien queda adentro, te oye. "
              "Entre más asustado, más grande.", "accion": "leer"},
    {"texto": "No ves a través de las paredes. Si se va la luz, solo alumbra tu "
              "linterna, nada eléctrico funciona y no verás a los aliens ni por dónde "
              "miran. Busquen la caja de fusibles que parpadea en rojo y enciéndanla.",
     "accion": "leer"},
    {"texto": "{interactuar}: usar, leer notas y esconderte. Si te atrapan vas a una "
              "celda y tus compañeros te sacan. Tienes 3 vidas.", "accion": "leer"},
    {"texto": "{habilidad}: usar tu habilidad.  {habilidades}: árbol de habilidades. "
              "¡Escapen juntos!", "accion": "leer"},
]


class Tutorial:
    def __init__(self, jugadores):
        self.activo = True
        self.estado = {id(j): {"paso": 0, "sigilo_ms": 0, "listo": False} for j in jugadores}
        self.jugadores = list(jugadores)

    def _de(self, jugador):
        return self.estado.setdefault(id(jugador), {"paso": 0, "sigilo_ms": 0, "listo": False})

    def _necesarios(self):
        """Los que tienen que terminarlo: los que se pueden mover (un puesto de
        mando sin mando conectado no puede ni presionar la tecla)."""
        return [j for j in self.jugadores if j.puede_moverse and not j.eliminado] or self.jugadores

    def listos(self):
        """(cuántos terminaron, cuántos tienen que terminar)."""
        necesarios = self._necesarios()
        return sum(self._de(j)["listo"] for j in necesarios), len(necesarios)

    def esta_listo(self, jugador):
        return self._de(jugador)["listo"]

    def _avanzar(self, e):
        e["paso"] += 1
        if e["paso"] >= len(PASOS):
            e["paso"] = len(PASOS) - 1
            e["listo"] = True

    def actualizar(self, dt):
        if not self.activo:
            return
        for jugador in self.jugadores:
            e = self._de(jugador)
            if e["listo"]:
                continue
            accion = PASOS[e["paso"]]["accion"]
            if accion == "mover" and jugador.personaje.moviendose:
                self._avanzar(e)
            elif accion == "sigilo":
                if jugador.personaje.moviendose and jugador.sigilo:
                    e["sigilo_ms"] += dt
                if e["sigilo_ms"] >= MS_SIGILO_NECESARIO:
                    self._avanzar(e)
        hechos, total = self.listos()
        if hechos >= total:
            self.activo = False

    def siguiente(self, jugador):
        """Tecla de habilidad: pasa al siguiente paso (en el último, termina)."""
        e = self._de(jugador)
        if not e["listo"]:
            self._avanzar(e)
        self.actualizar(0)

    def texto(self, jugador):
        """(número de paso, total, texto ya con sus teclas) o None si ya acabó."""
        if not self.activo:
            return None
        e = self._de(jugador)
        if e["listo"]:
            hechos, total = self.listos()
            return (len(PASOS), len(PASOS),
                    f"¡Listo! Esperando a los demás ({hechos}/{total} listos)...")
        mover = "WASD" if jugador.puesto == 0 else "las flechas" if jugador.puesto == 1 \
            else "el stick" if getattr(jugador, "con_mando", False) else jugador.controles_nombre
        texto = PASOS[e["paso"]]["texto"].format(
            mover=mover, sigilo=jugador.nombre_tecla("sigilo"),
            interactuar=jugador.nombre_tecla("interactuar"),
            habilidad=jugador.nombre_tecla("habilidad"),
            habilidades=jugador.nombre_tecla("habilidades"))
        return (e["paso"] + 1, len(PASOS), texto)
