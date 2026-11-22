"""Tutorial al empezar la partida, sin tiempo: cada quien va a su ritmo.

En la feria la gente se sienta a jugar sin haber leído nada. Antes de que los
aliens despierten, cada jugador aprende HACIENDO (Diego, nov 21: "haz el
tutorial del inicio mucho más atractivo e interactivo"; antes eran 9 cuadros
de texto que se pasaban con la tecla de habilidad y solo moverse y el sigilo
se hacían de verdad):

1. Moverse.
2. Caminar en sigilo (y ver cómo se achica el anillo de ruido).
3. Esconderse en el casillero marcado.
4. Leer la nota marcada (ahí está el código de la puerta).
5. Sacar el celular (NEXUS).
6. Abrir el árbol de habilidades.
7. y 8. Dos tarjetas cortas con íconos: lo peligroso (el Cambiaformas, el
   apagón, la celda) y la misión.

Cada paso de "hacer" se completa solo al hacerlo (con un "¡Bien!" y un
destello: screens/tutorial.py lo dibuja); el casillero y la nota se marcan en
el mapa con un camino de puntos (`objetivo`). La tecla de habilidad sigue
pasando de paso (en los de hacer, "saltar": por si alguien se traba) y en las
tarjetas de leer es "siguiente".

Mientras dura:

- los aliens duermen (no se mueven ni ven ni oyen),
- el cronómetro de la partida no corre,
- no hay eventos aleatorios,
- la puerta de la prisión no abre (mision.py pregunta `juego.en_tutorial`),
  para que nadie avance con los aliens dormidos.

Termina, y la nave "arranca", solo cuando todos los que se pueden mover
terminaron sus pasos. Quien acaba primero puede caminar por la prisión
mientras espera a los demás.

En red el servidor lleva el estado de cada jugador (`estado`, un dict por
jugador con números: viaja en "tut_estado") y cada cliente lo dibuja con lo
suyo (el casillero y la nota los busca con su copia del mapa).
"""

import math

MS_SIGILO_NECESARIO = 900

# {mover}, {sigilo}, {interactuar}, {habilidad}, {habilidades}, {celular}, {soltar} y {vidas} se cambian por
# las teclas de cada jugador. "accion": lo que hay que hacer para completarlo ("leer" = pasar con la
# tecla de habilidad). "icono": el dibujo de la tarjeta (screens/tutorial.py). "teclas": qué teclas
# dibujar en la tarjeta. "puntos" (los de leer): [(icono, texto)].
PASOS = [
    {"titulo": "Muévete", "texto": "Camina con {mover}.",
     "accion": "mover", "icono": "mover", "teclas": ["mover"]},
    {"titulo": "Camina en sigilo",
     "texto": "Mantén {sigilo} mientras caminas: vas lento y tu anillo de ruido se achica. "
              "Si un alien queda dentro del anillo, te oye.",
     "accion": "sigilo", "icono": "sigilo", "teclas": ["sigilo", "mover"]},
    {"titulo": "Escóndete",
     "texto": "Ve al casillero marcado y métete con {interactuar}. Adentro los aliens no te ven, "
              "pero si te oyen pueden revisarlo.",
     "accion": "esconderse", "icono": "casillero", "teclas": ["interactuar"]},
    {"titulo": "Lee una nota",
     "texto": "Sal con {interactuar} y lee la nota marcada. En alguna nota está el código de la "
              "puerta.",
     "accion": "nota", "icono": "nota", "teclas": ["interactuar"]},
    {"titulo": "Saca tu celular",
     "texto": "Ábrelo con {celular}. En NEXUS los aliens riegan rumores: ve al lugar, toma una "
              "foto y desmiéntelo. Con el celular abierto no te mueves.",
     "accion": "celular", "icono": "celular", "teclas": ["celular"]},
    {"titulo": "Tus habilidades",
     "texto": "Abre tu árbol con {habilidades}. Con los puntos del equipo desbloqueas habilidades "
              "y las usas con {habilidad}.",
     "accion": "arbol", "icono": "arbol", "teclas": ["habilidades"]},
    {"titulo": "Ojo con esto", "accion": "leer", "icono": "peligro",
     "texto": "Un prisionero es el Cambiaformas. Si se va la luz, busquen la caja roja. "
              "Si te atrapan vas a una celda.",
     "puntos": [
         ("cambiaformas", "Un prisionero es el Cambiaformas: no habla y su nombre falla. "
                          "No te alejes de tu equipo."),
         ("apagon", "Si se va la luz, solo alumbra tu linterna: busquen la caja de fusibles "
                    "que parpadea en rojo."),
         ("celda", "Si te atrapan vas a una celda y tus compañeros te sacan. Tienes {vidas}."),
     ]},
    {"titulo": "La misión", "accion": "leer", "icono": "capsula",
     "texto": "Abran la puerta con el código, apaguen las consolas, reparen la cápsula y escapen juntos.",
     "puntos": [
         ("puerta", "Encuentren el código en las notas y abran la puerta."),
         ("prisionero", "{interactuar} junto a un prisionero: \"¿vienes conmigo?\". Llévalo a la cápsula."),
         ("capsula", "Apaguen las consolas, reparen la cápsula y ¡escapen juntos!"),
     ]},
]

# Lo que se dibuja encima del casillero y de la nota marcados.
LETREROS = {"esconderse": "Escóndete aquí", "nota": "Lee esta nota"}


def con_teclas(texto, jugador):
    """Cambia {mover}, {sigilo}... por las teclas de ese jugador."""
    esquema = getattr(jugador, "esquema", jugador.puesto)
    mover = "WASD" if esquema == 0 else "las flechas" if esquema == 1 \
        else "el stick" if getattr(jugador, "con_mando", False) else jugador.controles_nombre
    return texto.format(
        mover=mover, sigilo=jugador.nombre_tecla("sigilo"),
        interactuar=jugador.nombre_tecla("interactuar"),
        habilidad=jugador.nombre_tecla("habilidad"),
        habilidades=jugador.nombre_tecla("habilidades"),
        celular=jugador.nombre_tecla("celular"),
        soltar=jugador.nombre_tecla("soltar"),
        vidas=_vidas_texto(jugador))


def _vidas_texto(jugador):
    if getattr(jugador, "vidas_infinitas", False):
        return "vidas infinitas"
    n = getattr(jugador, "vidas_max", 3)
    return f"{n} vida{'s' if n != 1 else ''}"


def pasos_con_teclas(jugador):
    """Todos los pasos, ya con las teclas del jugador (para repasarlos en una
    Terminal NEXUS)."""
    salida = []
    for p in PASOS:
        if p.get("puntos"):
            cuerpo = " ".join(con_teclas(t, jugador) for _, t in p["puntos"])
        else:
            cuerpo = con_teclas(p["texto"], jugador)
        salida.append(f"{p['titulo']}: {cuerpo}")
    return salida


def _estado_nuevo():
    return {"paso": 0, "sigilo_ms": 0, "listo": False, "hechos": 0, "ultimo": -1}


class Tutorial:
    def __init__(self, jugadores, juego=None):
        self.activo = True
        self.juego = juego
        self.estado = {id(j): _estado_nuevo() for j in jugadores}
        self.jugadores = list(jugadores)
        self._notas_al_empezar = {}     # id(jugador) -> notas leídas al llegar al paso de la nota

    def _de(self, jugador):
        return self.estado.setdefault(id(jugador), _estado_nuevo())

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

    def paso_actual(self, jugador):
        """El dict de PASOS en que va (None si ya terminó o no hay tutorial)."""
        if not self.activo:
            return None
        e = self._de(jugador)
        if e["listo"]:
            return None
        return PASOS[min(e["paso"], len(PASOS) - 1)]

    def _avanzar(self, e, hecho=False):
        if hecho:
            # Lo hizo (no lo saltó): screens/tutorial.py lo celebra al ver que
            # `hechos` subió (también en red: viaja con el estado).
            e["hechos"] = e.get("hechos", 0) + 1
            e["ultimo"] = e["paso"]
        e["paso"] += 1
        e["sigilo_ms"] = 0
        if e["paso"] >= len(PASOS):
            e["paso"] = len(PASOS) - 1
            e["listo"] = True

    def _notas_leidas(self, jugador):
        mision = getattr(self.juego, "mision", None)
        if mision is None:
            return 0
        return sum(1 for n in getattr(mision, "notas", ()) if jugador in n.get("leida_por", ()))

    def _hizo(self, jugador, e, accion, dt):
        """¿Ya hizo lo que pide este paso?"""
        panel = jugador.panel.get("tipo") if jugador.panel is not None else None
        if accion == "mover":
            return jugador.personaje.moviendose
        if accion == "sigilo":
            if jugador.personaje.moviendose and jugador.sigilo:
                e["sigilo_ms"] = e.get("sigilo_ms", 0) + dt
            return e.get("sigilo_ms", 0) >= MS_SIGILO_NECESARIO
        if accion == "esconderse":
            return jugador.escondido
        if accion == "nota":
            clave = id(jugador)
            leidas = self._notas_leidas(jugador)
            if clave not in self._notas_al_empezar:
                self._notas_al_empezar[clave] = leidas
            return leidas > self._notas_al_empezar[clave]
        if accion == "celular":
            return panel == "celular"
        if accion == "arbol":
            return panel == "habilidades"
        return False

    def actualizar(self, dt):
        if not self.activo:
            return
        for jugador in self.jugadores:
            e = self._de(jugador)
            if e["listo"]:
                continue
            accion = PASOS[e["paso"]]["accion"]
            if accion != "leer" and self._hizo(jugador, e, accion, dt):
                self._avanzar(e, hecho=True)
                self._notas_al_empezar.pop(id(jugador), None)
                if self.juego is not None and hasattr(self.juego, "sonar"):
                    self.juego.sonar("menu_ok", 0.8)
        hechos, total = self.listos()
        if hechos >= total:
            self.activo = False

    def siguiente(self, jugador):
        """Tecla de habilidad: pasa al siguiente paso (en los de hacer, lo
        salta; en el último, termina)."""
        e = self._de(jugador)
        if not e["listo"]:
            self._avanzar(e)
            self._notas_al_empezar.pop(id(jugador), None)
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
        return (e["paso"] + 1, len(PASOS), con_teclas(PASOS[e["paso"]]["texto"], jugador))

    # -- Lo que se marca en el mapa -----------------------------------------------------------

    def objetivo(self, jugador, juego=None):
        """((x, y) del mundo, letrero, rect) de lo que tiene que buscar en este
        paso (el casillero o la nota), o None."""
        juego = juego or self.juego
        paso = self.paso_actual(jugador)
        if paso is None or juego is None:
            return None
        accion = paso["accion"]
        if accion == "esconderse":
            if jugador.escondido:
                return None
            rect = _casillero_para(juego, jugador)
        elif accion == "nota":
            if jugador.escondido:
                return None            # primero tiene que salir (lo dice la tarjeta)
            rect = _nota_para(juego, jugador)
        else:
            return None
        if rect is None:
            return None
        return rect.center, LETREROS[accion], rect


def _cerca_primero(rects, jugador):
    cx, cy = jugador.hitbox.center
    return sorted(rects, key=lambda r: math.hypot(r.centerx - cx, r.centery - cy))


def _casillero_para(juego, jugador):
    """El casillero libre más cercano (sin candado, sin un prisionero ni otro
    jugador adentro)."""
    libres = [e["rect"] for e in getattr(juego, "escondites", ()) or ()
              if not e.get("candado") and e.get("npc") is None
              and e.get("ocupante") in (None, jugador)]
    libres = _cerca_primero(libres, jugador)
    return libres[0] if libres else None


def _nota_para(juego, jugador):
    """La nota más cercana que todavía no leyó (si ya leyó todas, la más cercana)."""
    mision = getattr(juego, "mision", None)
    notas = list(getattr(mision, "notas", ()) or ())
    if not notas:
        return None
    sin_leer = [n["rect"] for n in notas if jugador not in n.get("leida_por", ())]
    rects = _cerca_primero(sin_leer or [n["rect"] for n in notas], jugador)
    return rects[0] if rects else None
