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


def empezar(juego, jugador, tipo, al_ganar, facil=False, titulo=None):
    juego_mini = minijuegos.crear(tipo, facil, titulo=titulo)
    jugador.abrir_panel({"tipo": "tarea", "mini": juego_mini, "al_ganar": al_ganar})
    juego.sonar("menu_ok", 0.5)
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
                facil=rol == "Tecnomante", titulo="Caja de fusibles: sube las palancas")
        return True

    mision = getattr(juego, "mision", None)
    if mision is not None and mision.activa:
        consola, aviso = mision.consola_para(jugador)
        if aviso:
            jugador.avisar(aviso, COLOR_MAL)
            return True
        if consola is not None:
            empezar(juego, jugador, "senal", lambda: _apagar(mision, consola, jugador),
                    facil=rol == "Tecnomante", titulo="Consola: sintoniza la señal para apagarla")
            return True
        lista, aviso = mision.capsula_para(jugador)
        if aviso:
            jugador.avisar(aviso, COLOR_MAL)
            return True
        if lista:
            empezar(juego, jugador, "cables", lambda: mision.terminar_reparacion(jugador),
                    facil=rol == "Forjador", titulo="Cápsula: conecta los cables")
            return True

    planta = getattr(juego, "guardia_planta", None)
    if planta is not None and planta._cerca_planta(jugador) and planta.puede_cultivar(jugador):
        from misiones.guardia import es_biomante
        biomante = es_biomante(jugador)
        mini = empezar(juego, jugador, "abono", lambda: _crecer(planta, jugador, biomante), facil=biomante,
                       titulo="Haz crecer la planta" if biomante else "Echa el abono en la maceta")
        # La planta de verdad crece con cada acierto (la ven todos) y, si lo
        # deja a medias, el minijuego sigue desde donde iba.
        p = planta.planta
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
                    titulo=datos.get("titulo_arreglo"))
            return True

    # Un casillero con candado (aunque no haya leído la noticia).
    for escondite in getattr(juego, "escondites", ()):
        if escondite.get("candado") and escondite["rect"].colliderect(jugador.hitbox):
            empezar(juego, jugador, "ganzua", lambda e=escondite: _abrir_candado(juego, jugador, e),
                    titulo="El casillero tiene candado: fuérzalo")
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
            if al_ganar is not None:
                al_ganar()


def dibujar(screen, vista, jugador):
    mini = de(jugador)
    if mini is not None:
        mini.dibujar(screen, vista, jugador)
