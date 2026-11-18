"""Qué pasa en la partida cuando un jugador pierde la conexión (modo en red).

Antes, si se caía el wifi de una laptop, su jugador se quedaba parado donde
estaba con todo lo que llevaba: el decodificador del Tecnomante, las piezas,
el kit... y los demás no podían seguir sin él. Tampoco se enteraban.

Ahora (lo llama el servidor en cada cuadro, `Servidor._revisar_conexiones`):

1. **Pierde la conexión** (`perdio`): se queda quieto y los aliens no lo cazan
   (`puede_moverse = False`); si un alien estaba revisando su escondite, se
   rinde (no puede jugar el minijuego). Encima de él sale "Sin conexión" y a
   los demás les llega un aviso. El cliente intenta volver solo
   (cliente.RECONECTAR_S).
2. **No vuelve en GRACIA_S** (`se_fue`): deja caer lo que llevaba donde estaba,
   como cuando lo eliminan (`Mision.soltar_al_morir`: sus piezas y
   consumibles, y lo de su rol: el decodificador del Tecnomante, el kit del
   Forjador, el abono del Biomante; y las pruebas del infiltrado). Deja de
   verse, los prisioneros que lo seguían se quedan, y no cuenta para ganar ni
   para perder. Aviso a todos y la IA lo comenta.
3. **Vuelve** (`volvio`): aparece donde estaba, se puede mover otra vez, con
   unos segundos sin que lo cacen; lo que soltó sigue en el piso.

Un corte corto (el wifi que se va un segundo) solo llega al paso 1.
"""

GRACIA_S = 8.0               # sin conexión más que esto: suelta sus cosas
INVULNERABLE_AL_VOLVER_MS = 3000
COLOR_AVISO = (255, 180, 90)
COLOR_VUELVE = (96, 200, 120)


def _nombre(juego, jugador):
    numero = juego.jugadores.index(jugador) + 1 if jugador in juego.jugadores else "?"
    return f"J{numero} ({jugador.rol})"


def _a_los_demas(juego, jugador, texto, color):
    for otro in juego.jugadores:
        if otro is not jugador:
            otro.avisar(texto, color)


def perdio(juego, jugador):
    """Se le cayó la conexión: quieto, sin que lo cacen, y aviso."""
    jugador.sin_conexion = True
    jugador.puede_moverse = False
    jugador.sigilo = False
    minijuego = getattr(jugador, "minijuego", None)
    if minijuego is not None:
        # (sin conexión no puede apretar: el alien se rinde, como si se calmara)
        jugador.minijuego = None
        alien = getattr(minijuego, "alien", None)
        if alien is not None and hasattr(alien, "rendirse"):
            alien.rendirse()
    if not getattr(jugador, "eliminado", False):
        _a_los_demas(juego, jugador, f"{_nombre(juego, jugador)} perdió la conexión. "
                                     "Esperando a que vuelva...", COLOR_AVISO)


def se_fue(juego, jugador):
    """No volvió a tiempo: suelta lo que llevaba y sale de la partida
    (hasta que vuelva)."""
    if getattr(jugador, "desconectado", False) or getattr(jugador, "eliminado", False):
        return
    jugador.desconectado = True
    donde = jugador.hitbox.center
    jugador.cerrar_panel()
    jugador.progreso = None
    if jugador.escondite is not None:
        jugador.salir_del_escondite()
    npcs = getattr(juego, "npcs", None)
    for npc in getattr(npcs, "npcs", ()) or ():
        if getattr(npc, "siguiendo", None) is jugador:
            npc.siguiendo = None
            if hasattr(npc, "decir"):
                npc.decir("¿Dónde se metió? Me quedo aquí...")
    _a_los_demas(juego, jugador, f"{_nombre(juego, jugador)} se desconectó.", COLOR_AVISO)
    # Primero las pruebas del infiltrado: soltar_al_morir vacía el inventario.
    if getattr(juego, "infiltrado", None) is not None:
        juego.infiltrado.soltar(jugador, donde)
    if getattr(juego, "mision", None) is not None:
        juego.mision.soltar_al_morir(jugador, donde)
    juego.decir("desconectado", jugador.rol, forzar=True)


def volvio(juego, jugador):
    """Se reconectó: vuelve a jugar donde estaba."""
    se_habia_ido = getattr(jugador, "desconectado", False)
    jugador.sin_conexion = False
    jugador.desconectado = False
    if getattr(jugador, "eliminado", False):
        return
    jugador.puede_moverse = True
    jugador.invulnerable_ms = max(jugador.invulnerable_ms, INVULNERABLE_AL_VOLVER_MS)
    _a_los_demas(juego, jugador, f"{_nombre(juego, jugador)} volvió a conectarse.", COLOR_VUELVE)
    if se_habia_ido:
        jugador.avisar("Volviste. Lo que llevabas quedó en el piso donde te desconectaste.",
                       COLOR_VUELVE)
        juego.decir("reconectado", jugador.rol)
    else:
        jugador.avisar("Volviste a conectarte.", COLOR_VUELVE)
