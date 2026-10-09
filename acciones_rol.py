"""Lo que hace cada habilidad de los cuatro roles dentro de la partida.

El árbol de habilidades (Estructuras/arbol_habilidades.py) decide QUÉ tiene
desbloqueado cada jugador; este archivo decide qué PASA cuando lo usa. Se
pregunta siempre con `jugador.arbol.tiene(CLAVE)`, así que el árbol es lo que
abre o cierra cada acción: si el Tecnomante escogió ESCANEO, HACKEO quedó
descartado y las terminales ya no apagan aliens.

Tres formas de uso (campo `uso` de cada nodo en data/habilidades.py):
- pasiva: funciona sola (las dibuja screens/roles.py).
- estacion: tecla de interactuar frente a una terminal o un panel.
- activa: tecla de habilidad, en cualquier lado, con recarga.

Todo se apoya en lo que ya hacían los aliens: el escaneo y la interceptación
muestran su cono y su árbol; el señuelo y la señal falsa usan el mismo "oír un
ruido" que un latido; la regeneración baja el pulso, que es lo que delata.
"""

import math

import pygame


# -- Números de cada habilidad (para ajustar el balance, solo aquí) -----------------
DURACION_MAPA_TERMINAL_MS = 5000      # Conexión digital
RECARGA_TERMINAL_MS = 4000
RADIO_HACKEO = 520                    # Hackeo básico
DURACION_HACKEO_MS = 5000
RECARGA_HACKEO_MS = 15000
DURACION_ESCANEO_MS = 6000            # Escaneo de sistemas
DURACION_SENUELO_MS = 7000            # Fabricación improvisada
RADIO_SENUELO = 600
RADIO_AYUDA = 230                     # Regeneración e Impulso: hasta dónde llegan
CALMA_REGENERACION = 35
AMENAZA_REGENERACION = 30
DURACION_INTERCEPCION_MS = 8000       # Interceptación básica
DISTANCIA_EMISION = 320               # Emisión modulada: qué tan lejos cae la señal
RADIO_EMISION = 750
DURACION_SENAL_MS = 2500
ALCANCE_SINTONIA = 1000               # Sintonía de señales (flechas)

PUNTOS_HACKEO = 10
PUNTOS_REPARACION = 15
PUNTOS_AYUDA = 5

COLOR_BIEN = (96, 200, 120)
COLOR_MAL = (245, 130, 120)
COLOR_AVISO = (255, 214, 64)

# Hacia dónde mira el personaje, como vector, según el nombre de su dirección.
_VECTORES = {
    "north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0),
    "north-east": (0.707, -0.707), "north-west": (-0.707, -0.707),
    "south-east": (0.707, 0.707), "south-west": (-0.707, 0.707),
}


def _distancia(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _rect_en(rx, ry, tamano, mundo):
    rect = pygame.Rect(0, 0, *tamano)
    rect.center = (int(rx * mundo.ancho), int(ry * mundo.alto))
    return rect


# -- Preparar el mapa -----------------------------------------------------------------

def preparar_estaciones(mundo, objetos=None):
    """Terminales, paneles y piezas en píxeles.

    Salen de los objetos del mapa (objetos_mapa.py, lo que se pone con el
    editor); sin ellos, de data/estaciones.py.
    """
    from data import estaciones
    from data.estaciones import TAMANO_ESTACION, TAMANO_PIEZA
    if objetos is not None:
        lista_t, lista_p, lista_piezas = objetos["terminales"], objetos["paneles"], objetos["piezas"]
    else:
        lista_t, lista_p, lista_piezas = estaciones.TERMINALES, estaciones.PANELES, estaciones.PIEZAS

    terminales = []
    for datos in lista_t:
        t = dict(datos, tipo="terminal", recarga_ms=0)
        t["rect"] = _rect_en(datos["rx"], datos["ry"], TAMANO_ESTACION, mundo)
        terminales.append(t)
    paneles = []
    for datos in lista_p:
        p = dict(datos, tipo="panel", reparado=False)
        p["rect"] = _rect_en(datos["rx"], datos["ry"], TAMANO_ESTACION, mundo)
        paneles.append(p)
    piezas = [{"rect": _rect_en(rx, ry, TAMANO_PIEZA, mundo), "recogida": False}
              for rx, ry in lista_piezas]
    return terminales, paneles, piezas


# -- Consultas --------------------------------------------------------------------------

def habilidad_activa(jugador):
    """El nodo de la habilidad que se usa con la tecla de habilidad, o None."""
    for nodo in reversed(jugador.arbol.desbloqueadas()):
        if nodo.uso == "activa":
            return nodo
    return None


def estacion_bajo(juego, jugador):
    """(tipo, estación) que este jugador puede usar donde está parado, o None.

    Solo el Tecnomante usa terminales y solo el Forjador repara paneles: los
    demás pasan por encima sin que les salga la pista.
    """
    if jugador.arbol.tiene("CONEXION"):
        for t in juego.terminales:
            if t["rect"].colliderect(jugador.hitbox):
                return t
    if jugador.arbol.tiene("INGENIO"):
        for p in juego.paneles:
            if not p["reparado"] and p["rect"].colliderect(jugador.hitbox):
                return p
    return None


def companeros_cerca(juego, jugador, radio=RADIO_AYUDA, incluirse=False):
    centro = jugador.hitbox.center
    return [j for j in juego.jugadores
            if (incluirse or j is not jugador) and _distancia(centro, j.hitbox.center) <= radio]


# -- Estaciones (tecla de interactuar) ---------------------------------------------------

def usar_estacion(juego, jugador, estacion):
    if estacion["tipo"] == "terminal":
        _usar_terminal(juego, jugador, estacion)
    elif estacion["tipo"] == "panel":
        _reparar_panel(juego, jugador, estacion)


def _usar_terminal(juego, jugador, terminal):
    if terminal["recarga_ms"] > 0:
        jugador.avisar(f"La terminal se reinicia: {math.ceil(terminal['recarga_ms'] / 1000)} s",
                       COLOR_MAL)
        return
    # Conexión digital (la base): el mapa de la nave con los aliens.
    jugador.efectos["mapa"] = DURACION_MAPA_TERMINAL_MS
    terminal["recarga_ms"] = RECARGA_TERMINAL_MS

    if not jugador.arbol.tiene("HACKEO"):
        jugador.avisar("Conectado: estado de la nave en pantalla.", COLOR_AVISO)
        return
    apagados = [a for a in juego.aliens
                if _distancia(a.centro, terminal["rect"].center) <= RADIO_HACKEO]
    for alien in apagados:
        alien.aturdir(DURACION_HACKEO_MS)
    terminal["recarga_ms"] = RECARGA_HACKEO_MS
    if apagados:
        jugador.sumar_puntos(PUNTOS_HACKEO)
        jugador.avisar(f"Hackeo: {len(apagados)} alien(s) apagados. +{PUNTOS_HACKEO}", COLOR_BIEN)
    else:
        jugador.avisar("Hackeo: no había aliens cerca de esta terminal.", COLOR_AVISO)


def _reparar_panel(juego, jugador, panel):
    if not jugador.arbol.tiene("REPARACION"):
        jugador.avisar(f"Necesitas Reparación básica ([{jugador.nombre_tecla('habilidades')}])",
                       COLOR_MAL)
        return
    if jugador.piezas <= 0:
        jugador.avisar("Te falta una pieza para repararlo.", COLOR_MAL)
        return
    jugador.piezas -= 1
    panel["reparado"] = True
    jugador.sumar_puntos(PUNTOS_REPARACION)
    hechos = sum(p["reparado"] for p in juego.paneles)
    jugador.avisar(f"Panel reparado ({hechos}/{len(juego.paneles)}). +{PUNTOS_REPARACION}",
                   COLOR_BIEN)


# -- Habilidades activas (tecla de habilidad) ----------------------------------------------

def usar_habilidad(juego, jugador):
    """El jugador presionó su tecla de habilidad."""
    nodo = habilidad_activa(jugador)
    if nodo is None:
        if len(jugador.arbol.desbloqueadas()) <= 1:
            jugador.avisar(f"Escoge una habilidad con [{jugador.nombre_tecla('habilidades')}]",
                           COLOR_AVISO)
        else:
            jugador.avisar("Tu habilidad se usa en el mapa, no con esta tecla.", COLOR_AVISO)
        return False
    if jugador.recarga_ms > 0:
        jugador.avisar(f"{nodo.nombre}: {math.ceil(jugador.recarga_ms / 1000)} s", COLOR_MAL)
        return False

    usar = {
        "ESCANEO": _escaneo,
        "FABRICACION": _fabricar_senuelo,
        "REGENERACION": _regeneracion,
        "IMPULSO": _impulso,
        "INTERCEPCION": _intercepcion,
        "EMISION": _emision,
    }.get(nodo.clave)
    if usar is None or not usar(juego, jugador):
        return False
    jugador.recarga_ms = int(nodo.recarga_s * 1000)
    return True


def _escaneo(juego, jugador):
    jugador.efectos["mapa"] = DURACION_ESCANEO_MS
    jugador.efectos["escaneo"] = DURACION_ESCANEO_MS
    jugador.avisar("Escaneo: aliens y sus conos en el mapa.", COLOR_AVISO)
    return True


def _fabricar_senuelo(juego, jugador):
    if jugador.piezas <= 0:
        jugador.avisar("Necesitas una pieza para el señuelo.", COLOR_MAL)
        return False
    jugador.piezas -= 1
    juego.senuelos.append({"pos": jugador.hitbox.center, "ms": DURACION_SENUELO_MS,
                           "duracion": DURACION_SENUELO_MS})
    jugador.avisar("Señuelo armado: los aliens vendrán por el ruido.", COLOR_BIEN)
    return True


def _regeneracion(juego, jugador):
    ayudados = 0
    for otro in companeros_cerca(juego, jugador, incluirse=True):
        otro.pulso = max(0.0, otro.pulso - CALMA_REGENERACION)
        if otro is not jugador:
            ayudados += 1
            otro.avisar("La Biomante te calmó.", COLOR_BIEN)
    # Si alguien está escondido cerca y un alien lo revisa, le baja la amenaza.
    for otro in juego.jugadores:
        juego_escondite = otro.minijuego
        if (juego_escondite is not None and otro is not jugador and
                _distancia(jugador.hitbox.center, otro.hitbox.center) <= RADIO_AYUDA):
            juego_escondite.amenaza = max(0.0, juego_escondite.amenaza - AMENAZA_REGENERACION)
            ayudados += 1
    if ayudados:
        jugador.sumar_puntos(PUNTOS_AYUDA * ayudados)
    jugador.avisar(f"Regeneración: {ayudados} compañero(s) más tranquilos.", COLOR_BIEN)
    return True


def _impulso(juego, jugador):
    recargados = [o for o in companeros_cerca(juego, jugador) if o.recarga_ms > 0]
    if not recargados:
        jugador.avisar("Nadie cerca necesita energía.", COLOR_AVISO)
        return False
    for otro in recargados:
        otro.recarga_ms = 0
        otro.avisar("Impulso: tu habilidad está lista otra vez.", COLOR_BIEN)
    jugador.sumar_puntos(PUNTOS_AYUDA * len(recargados))
    jugador.avisar(f"Impulso a {len(recargados)} compañero(s). +{PUNTOS_AYUDA * len(recargados)}",
                   COLOR_BIEN)
    return True


def _intercepcion(juego, jugador):
    jugador.efectos["intercepcion"] = DURACION_INTERCEPCION_MS
    jugador.avisar("Interceptando: rutas y decisiones de los aliens.", COLOR_AVISO)
    return True


def _emision(juego, jugador):
    """La señal cae delante del jugador, lejos de él, para alejar a los aliens."""
    dx, dy = _VECTORES.get(jugador.personaje.direccion, (0, 1))
    origen = jugador.hitbox.center
    punto = origen
    # Avanza hasta DISTANCIA_EMISION o hasta la primera pared.
    for paso in range(16, DISTANCIA_EMISION + 1, 16):
        candidato = (origen[0] + dx * paso, origen[1] + dy * paso)
        if not juego.mundo.linea_libre(origen, candidato):
            break
        punto = candidato
    atraidos = [a for a in juego.aliens
                if _distancia(a.centro, punto) <= RADIO_EMISION and a.oir(punto)]
    juego.senales.append({"pos": (int(punto[0]), int(punto[1])), "ms": DURACION_SENAL_MS,
                          "duracion": DURACION_SENAL_MS})
    if atraidos:
        jugador.sumar_puntos(PUNTOS_AYUDA)
    jugador.avisar(f"Señal falsa: {len(atraidos)} alien(s) van a revisarla.", COLOR_AVISO)
    return True


# -- Cada frame -----------------------------------------------------------------------------

def actualizar(juego, dt):
    """Recargas, efectos, piezas, señuelos y la línea de estado del HUD."""
    for terminal in juego.terminales:
        terminal["recarga_ms"] = max(0, terminal["recarga_ms"] - dt)

    for jugador in juego.jugadores:
        jugador.recarga_ms = max(0, jugador.recarga_ms - dt)
        for nombre in list(jugador.efectos):
            jugador.efectos[nombre] -= dt
            if jugador.efectos[nombre] <= 0:
                del jugador.efectos[nombre]

        # Ingenio mecánico: el Forjador recoge las piezas al pasar por encima.
        if jugador.arbol.tiene("INGENIO") and not jugador.escondido:
            for pieza in juego.piezas:
                if not pieza["recogida"] and pieza["rect"].colliderect(jugador.hitbox):
                    pieza["recogida"] = True
                    jugador.piezas += 1
                    jugador.avisar(f"Pieza recogida ({jugador.piezas})", COLOR_BIEN)

        jugador.estacion_cerca = (None if jugador.escondido or jugador.zona_cerca
                                  else estacion_bajo(juego, jugador))

    # El señuelo hace ruido todo el rato que dura.
    for senuelo in juego.senuelos:
        senuelo["ms"] -= dt
        for alien in juego.aliens:
            if _distancia(alien.centro, senuelo["pos"]) <= RADIO_SENUELO:
                alien.oir(senuelo["pos"])
    juego.senuelos = [s for s in juego.senuelos if s["ms"] > 0]
    for senal in juego.senales:
        senal["ms"] -= dt
    juego.senales = [s for s in juego.senales if s["ms"] > 0]


def linea_de_estado(jugador):
    """Lo que dice la tercera línea del HUD: la habilidad y si está lista."""
    partes = []
    if jugador.arbol.tiene("INGENIO"):
        partes.append(f"Piezas: {jugador.piezas}")
    nodo = habilidad_activa(jugador)
    tecla = jugador.nombre_tecla("habilidad")
    if nodo is not None:
        if jugador.recarga_ms > 0:
            partes.append(f"{nodo.nombre}: {math.ceil(jugador.recarga_ms / 1000)} s")
        else:
            partes.append(f"[{tecla}] {nodo.nombre} lista")
    elif len(jugador.arbol.desbloqueadas()) <= 1:
        partes.append(f"[{jugador.nombre_tecla('habilidades')}] escoge tu habilidad")
    else:
        partes.append(f"{jugador.arbol.actual.nombre}: úsala en el mapa")
    return "  ·  ".join(partes)
