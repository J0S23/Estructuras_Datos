"""Las tareas con minijuego (misiones/minijuegos.py), en local y en red.

Antes, apagar una consola, reparar la cápsula, encender la caja de fusibles o
echarle abono a la planta era mantener la tecla de interactuar. Ahora
(`Game.minijuegos`), al presionar la tecla frente a la tarea se abre su
minijuego en la vista de quien la hace; al ganarlo pasa lo mismo que al
llenar la barra. En red lo juega el servidor con las teclas que mandan los
clientes, y el cliente lo dibuja (cliente_servidor/espejo.py, `_tarea`). En
las pruebas que ponen `minijuegos = False` sigue siendo mantener la tecla.

También se abren aquí los arreglos de las noticias verdaderas de NEXUS
(redes/nexus.py): un casillero con candado se fuerza con la ganzúa, una caja
de fusibles con los breakers botados se arregla con las palancas, etc.

El minijuego va en el panel del jugador ({"tipo": "tarea", "mini": ...}; no
"juego": esa clave no viaja por la red, cliente_servidor/estado.SALTAR):
mientras lo juega no camina, y si un alien llega, lo atrapa.

Un minijuego que se deja a medias (se cierra, lo atrapan, se va a hacer otra
cosa) queda guardado por su tarea (`Game.minis_guardados`, {(clave, fácil):
minijuego}; Diego, nov 21: "cuando me salgo y vuelvo a entrar todo cambia y mi
progreso se borra"): al volver a la misma consola, caja, cápsula, planta,
noticia o candado sigue igual, con lo que ya llevaba (también si vuelve otro
jugador con la misma dificultad del minijuego). Si alguien lo tiene abierto,
el otro no puede entrar ("Alguien ya está con esto"). Al ganarlo se borra.
"""

from misiones import minijuegos

COLOR_MAL = (245, 130, 120)

# Los sonidos de los minijuegos -> los que tiene el juego (Audio/SFX).
SONIDOS = {"menu_mover": "menu_mover", "acierto": "acierto", "fallo": "fallo",
           "girar": "tecleo", "palanca": "encajar", "soltar": "recoger"}


def activas(juego):
    return getattr(juego, "minijuegos", False)


def de(jugador):
    """El minijuego que está jugando (o None)."""
    panel = jugador.panel or {}
    return panel.get("mini") if panel.get("tipo") == "tarea" else None


def _guardados(juego):
    guardados = getattr(juego, "minis_guardados", None)
    if guardados is None:
        guardados = juego.minis_guardados = {}
    return guardados


def _en_uso(juego, mini, jugador):
    """¿Otro jugador tiene abierto este mismo minijuego?"""
    return any(otro is not jugador and de(otro) is mini for otro in getattr(juego, "jugadores", ()))


def empezar(juego, jugador, tipo, al_ganar, facil=False, titulo=None, clave=None):
    """Abre el minijuego de la tarea `clave` (sigue el que había a medias, si
    lo hay). Devuelve el minijuego, o None si otro lo está jugando."""
    guardados = _guardados(juego)
    juego_mini, nuevo = None, True
    if clave is not None:
        juego_mini = guardados.get((clave, bool(facil)))
        if juego_mini is not None and (juego_mini.ganado or type(juego_mini).__name__.lower() != tipo):
            guardados.pop((clave, bool(facil)), None)
            juego_mini = None
        # Si otro está con esta misma tarea (aunque con la otra dificultad), no.
        if any(c == clave and _en_uso(juego, m, jugador) for (c, _), m in guardados.items()):
            jugador.avisar("Alguien ya está con esto: hay que esperar a que termine.", COLOR_MAL)
            return None
        nuevo = juego_mini is None
    if juego_mini is None:
        juego_mini = minijuegos.crear(tipo, facil, titulo=titulo)
        if clave is not None:
            guardados[(clave, bool(facil))] = juego_mini
    jugador.abrir_panel({"tipo": "tarea", "mini": juego_mini, "al_ganar": al_ganar})
    juego.sonar("menu_ok", 0.5)
    juego_mini.retomado = not nuevo
    return juego_mini


def intentar(juego, jugador):
    """La tecla de interactuar frente a algo: si es una tarea con minijuego,
    lo abre (o avisa por qué no se puede). True si se encargó de la tecla."""
    if not activas(juego) or jugador.preso or getattr(jugador, "eliminado", False):
        return False
    rol = jugador.rol

    # La caja de fusibles buena, en un apagón.
    eventos = getattr(juego, "eventos", None)
    if eventos is not None and eventos.caja_cerca(jugador) is not None:
        empezar(juego, jugador, "interruptores", lambda: eventos.restaurar_luz(jugador),
                facil=rol == "Tecnomante", titulo="Caja de fusibles: sube las palancas",
                clave=("fusibles", id(eventos.caja)))
        return True

    mision = getattr(juego, "mision", None)
    if mision is not None and mision.activa:
        consola, aviso = mision.consola_para(jugador)
        if aviso:
            jugador.avisar(aviso, COLOR_MAL)
            return True
        if consola is not None:
            empezar(juego, jugador, "senal", lambda: _apagar(mision, consola, jugador),
                    facil=rol == "Tecnomante", titulo="Consola: sintoniza la señal para apagarla",
                    clave=("consola", id(consola)))
            return True
        lista, aviso = mision.capsula_para(jugador)
        if aviso:
            jugador.avisar(aviso, COLOR_MAL)
            return True
        if lista:
            empezar(juego, jugador, "cables", lambda: mision.terminar_reparacion(jugador),
                    facil=rol == "Forjador", titulo="Cápsula: conecta los cables",
                    clave=("capsula",))
            return True

    planta = getattr(juego, "guardia_planta", None)
    if planta is not None and planta._cerca_planta(jugador) and planta.puede_cultivar(jugador):
        from misiones.guardia import es_biomante
        biomante = es_biomante(jugador)
        mini = empezar(juego, jugador, "abono", lambda: _crecer(planta, jugador, biomante), facil=biomante,
                       titulo="Haz crecer la planta" if biomante else "Echa el abono en la maceta",
                       clave=("planta",))
        if mini is None:
            return True
        # La planta de verdad crece con cada acierto (la ven todos) y, si lo
        # deja a medias, el minijuego sigue desde donde iba (el mismo, si lo
        # dejó guardado; si no, uno nuevo desde el progreso de la planta: p.
        # ej. lo empezó otro rol con la otra dificultad).
        p = planta.planta
        if not getattr(mini, "retomado", False):
            mini.empezar_en(p["progreso"])
        mini.al_acertar = lambda avance: p.__setitem__("progreso", max(p["progreso"], min(0.99, avance)))
        return True

    # Lo que cuenta una noticia verdadera de NEXUS: verificarlo es arreglarlo.
    red = getattr(juego, "nexus", None)
    if red is not None and hasattr(red, "noticia_para"):
        pub = red.noticia_para(jugador)
        if pub is not None:
            datos = pub.rumor
            empezar(juego, jugador, datos["arreglo"], lambda: red.arreglar(jugador, pub),
                    titulo=datos.get("titulo_arreglo"), clave=("noticia", pub.id))
            return True

    # Un casillero con candado (aunque no haya leído la noticia).
    for escondite in getattr(juego, "escondites", ()):
        if escondite.get("candado") and escondite["rect"].colliderect(jugador.hitbox):
            empezar(juego, jugador, "ganzua", lambda e=escondite: _abrir_candado(juego, jugador, e),
                    titulo="El casillero tiene candado: fuérzalo", clave=("candado", id(escondite)))
            return True
    return False


def _apagar(mision, consola, jugador):
    if consola["progreso"] < 1:
        mision.apagar_consola(consola, jugador)


def _crecer(planta, jugador, biomante):
    p = planta.planta
    if p is not None and not p["crecida"]:
        p["progreso"] = 1.0
        planta._crecer(jugador, biomante)


def _abrir_candado(juego, jugador, escondite):
    red = getattr(juego, "nexus", None)
    pub = red.noticia_de_escondite(escondite) if red is not None and hasattr(red, "noticia_de_escondite") else None
    if pub is not None:
        red.arreglar(jugador, pub)
    else:
        escondite["candado"] = False
        jugador.avisar("Abrí el candado: el casillero ya se puede usar.", (120, 230, 150))


def tecla(juego, jugador, accion):
    """Una acción del jugador en su minijuego ("arriba"... "ok")."""
    mini = de(jugador)
    if mini is None:
        return
    sonido = mini.tecla(accion)
    if sonido:
        juego.sonar(SONIDOS.get(sonido, sonido), 0.45)


def actualizar(juego, dt):
    for jugador in juego.jugadores:
        mini = de(jugador)
        if mini is None:
            continue
        if jugador.preso or getattr(jugador, "eliminado", False):
            jugador.cerrar_panel()
            continue
        mini.actualizar(dt)
        if mini.listo:
            al_ganar = jugador.panel.get("al_ganar")
            jugador.cerrar_panel()
            guardados = _guardados(juego)
            for clave in [c for c, m in guardados.items() if m is mini]:
                del guardados[clave]
            if al_ganar is not None:
                al_ganar()


def dibujar(screen, vista, jugador):
    mini = de(jugador)
    if mini is not None:
        mini.dibujar(screen, vista, jugador)
