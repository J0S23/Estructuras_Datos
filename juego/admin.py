"""Menú de admin (F1 en la partida): lanzar eventos sin esperarlos.

Para probar el juego (y para la sustentación): que se vaya la luz, que
vuelva, una alarma, la Sombra ya, un rumor de NEXUS, abrir puertas... Mientras
está abierto el juego queda congelado, como en la pausa; al escoger algo se
hace, el menú se cierra y arriba sale un aviso con lo que pasó.

Cada opción es {"texto", "accion"(juego) -> mensaje}; "estado"(juego), si
está, se muestra a la derecha (p. ej. si el modo invencible está prendido).
La partida en que se usó no anota sus logros en el historial del computador
(Guardado/logros.json): `Game.admin_usado`.

Solo en el juego local: en red, el estado es del servidor.
"""

INVENCIBLE_MS = 10 ** 9
ATURDIR_MS = 20000


# -- Lo que hace cada opción (devuelven el mensaje para el aviso) ----------------------

def _apagon(juego):
    ev = juego.eventos
    if ev is None:
        return "Este mapa no tiene eventos"
    if ev.apagon:
        return "Ya hay un apagón"
    if not ev.cajas:
        return "Este mapa no tiene cajas de fusibles"
    if ev.lanzar("apagon") is None:
        return "No hay ninguna caja de fusibles alcanzable ahora"
    return "Se fue la luz"


def _volver_luz(juego):
    ev = juego.eventos
    if ev is None or not ev.apagon:
        return "No hay apagón"
    ev.restaurar_luz(None)
    return "Volvió la luz"


def _sombra(juego):
    if juego.sombra is None:
        return "Esta partida no tiene Sombra"
    if juego.eventos is None or not juego.eventos.apagon:
        if _apagon(juego) != "Se fue la luz":
            return "La Sombra necesita un apagón y no se pudo cortar la luz"
    if juego.sombra in juego.aliens:
        return "La Sombra ya está"
    juego._apagon_ms = max(juego._apagon_ms, juego.RETRASO_SOMBRA_MS)
    juego._actualizar_sombra(0)
    if juego.sombra not in juego.aliens:
        # Lo normal es a 650-1700 px; si no hay (p. ej. encerrados al empezar),
        # donde sea que no la vean y se pueda llegar.
        punto = (juego._punto_para_sombra(200, 10 ** 6)
                 or juego._punto_para_sombra(200, 10 ** 6, a_oscuras=False))
        if punto is None:
            return "No encontré dónde poner a la Sombra (lejos y conectada con alguien)"
        juego.sombra.aparecer(punto)
        juego.aliens.append(juego.sombra)
        juego._sombra_alcanzo = False
        juego.decir("sombra", forzar=True)
    return "Apareció la Sombra"


def _evento(nombre, texto):
    def accion(juego):
        ev = juego.eventos
        if ev is None:
            return "Este mapa no tiene eventos"
        if ev.activo is not None:
            ev.terminar()                     # uno a la vez: el de ahora termina
        if ev.lanzar(nombre) is None:
            return "No se puede ahora" + (" (no hay compuertas libres)" if nombre == "compuerta" else "")
        return texto
    return accion


def _terminar_evento(juego):
    ev = juego.eventos
    if ev is None or ev.activo is None:
        return "No hay alarma ni cierre de emergencia"
    ev.terminar()
    return "Terminó el evento"


def _evento_al_azar(juego):
    ev = juego.eventos
    if ev is None:
        return "Este mapa no tiene eventos"
    nombre = ev.lanzar()
    return f"Evento: {nombre}" if nombre else "No hay ningún evento posible ahora"


def _rumor(juego):
    if juego.nexus is None:
        return "Esta partida no tiene NEXUS"
    return "Un bot publicó un rumor" if juego.nexus.lanzar_rumor() else \
        "No se pudo (sin bots, sin lugares o todos con 3 cosas por verificar)"


def _trampa(juego):
    cf = juego.cambiaformas
    if cf is None:
        return "Esta partida no tiene Cambiaformas"
    if not cf.disfrazado:
        cf._disfrazarse()
    return "El Cambiaformas publicó una trampa" if cf.suplantar() else \
        "No se pudo ahora (ya hay una trampa, o está siguiendo o cazando a alguien)"


def _aturdir(juego):
    aliens = [a for a in juego.aliens if not getattr(a, "oculta", False)]
    for alien in aliens:
        alien.aturdir(ATURDIR_MS)          # (el Guardia no se deja: es inmune)
    quietos = sum(1 for a in aliens if a.descanso_ms > 0)
    return f"{quietos} aliens fuera de combate {ATURDIR_MS // 1000} s"


def _invencible(juego):
    juego.admin_invencible = not getattr(juego, "admin_invencible", False)
    for jugador in juego.jugadores:
        jugador.invulnerable_ms = INVENCIBLE_MS if juego.admin_invencible else 0
    return "Modo invencible: " + ("sí" if juego.admin_invencible else "no")


def _abrir_puertas(juego):
    abiertas = 0
    mision = juego.mision
    if mision is not None:
        for i, puerta in enumerate(mision.puertas):
            if not puerta["abierta"]:
                mision.abrir_puerta(None, i)
                abiertas += 1
    for puerta in juego.puertas_dobles:
        if not puerta["abierta"]:
            puerta["abierta"] = True
            juego._puerta_doble_abierta(puerta)
            abiertas += 1
    return f"{abiertas} puertas abiertas" if abiertas else "No hay puertas cerradas"


def _liberar(juego):
    mision = juego.mision
    libres = 0
    for celda in (mision.celdas if mision is not None else ()):
        preso = celda["preso"]
        if preso is not None:
            celda["preso"], celda["fuga_ms"] = None, None
            mision._sacar_de_celda(preso, celda)
            libres += 1
    return f"{libres} liberados" if libres else "No hay nadie en las celdas"


def _si_no(valor):
    return "sí" if valor else "no"


OPCIONES = [
    {"texto": "Que se vaya la luz (apagón)", "accion": _apagon,
     "estado": lambda j: "a oscuras" if j.eventos is not None and j.eventos.apagon else ""},
    {"texto": "Que vuelva la luz", "accion": _volver_luz},
    {"texto": "Que aparezca la Sombra ya", "accion": _sombra,
     "estado": lambda j: "está" if j.sombra is not None and j.sombra in j.aliens else ""},
    {"texto": "Alarma (aliens en alerta)", "accion": _evento("alarma", "Suena la alarma")},
    {"texto": "Cierre de emergencia (baja una compuerta)", "accion": _evento("compuerta", "Bajó una compuerta")},
    {"texto": "Terminar la alarma o el cierre", "accion": _terminar_evento,
     "estado": lambda j: (j.eventos.activo or "") if j.eventos is not None else ""},
    {"texto": "Un evento al azar", "accion": _evento_al_azar},
    {"texto": "Rumor de un bot en NEXUS", "accion": _rumor},
    {"texto": "Trampa del Cambiaformas en NEXUS", "accion": _trampa},
    {"texto": f"Aturdir a todos los aliens ({ATURDIR_MS // 1000} s)", "accion": _aturdir},
    {"texto": "Modo invencible", "accion": _invencible,
     "estado": lambda j: _si_no(getattr(j, "admin_invencible", False))},
    {"texto": "Abrir todas las puertas", "accion": _abrir_puertas},
    {"texto": "Sacar a todos de las celdas", "accion": _liberar},
]


class MenuAdmin:
    def __init__(self, juego):
        self.juego = juego
        self.cursor = 0
        self.rects = []          # rect de cada opción en pantalla (para el mouse)

    def mover(self, paso):
        self.cursor = (self.cursor + paso) % len(OPCIONES)

    def estado(self, i):
        funcion = OPCIONES[i].get("estado")
        try:
            return funcion(self.juego) if funcion else ""
        except Exception:
            return ""

    def activar(self, i=None):
        """Hace la opción (la del cursor si no se dice) y devuelve el mensaje."""
        i = self.cursor if i is None else i
        self.juego.admin_usado = True
        return OPCIONES[i]["accion"](self.juego)

    def opcion_en(self, pos):
        return next((i for i, r in enumerate(self.rects) if r.collidepoint(pos)), None)
