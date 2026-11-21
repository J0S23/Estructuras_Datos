"""Lo que el cliente hace él mismo apenas se presiona (nov 21, Diego: "en red
disminuye los lagazos que puede haber por ping alto").

Moverse ya no espera al servidor (prediccion.py), pero todo lo demás sí: en
un minijuego, cada flecha o cada giro de un cable se veía cuando volvía la
instantánea (con 80 ms de ping, ~250 ms después); lo mismo el cursor de un
menú (el celular, la terminal NEXUS, el árbol de habilidades). Aquí el
cliente lo aplica a SU copia en el mismo cuadro (`presionar`), con las mismas
funciones que usa el servidor, y lo anota con el número de la intención.

Las instantáneas que llegan todavía no lo incluyen (el servidor no lo ha
visto): cada vez que el espejo vuelve a copiar la sección del jugador
(`Espejo.completos`), se vuelve a poner encima lo anotado que el servidor
todavía no usó (`reaplicar`, con los `ack` de esa instantánea). Cuando el
ack lo alcanza, se borra: desde ahí ya viene en lo del servidor. Si el
servidor decidió otra cosa (lo atraparon y se cerró el minijuego), gana lo
del servidor.

Solo lo que da lo mismo aquí y allá: mover el cursor, girar una pieza, una
palanca, la frecuencia de la señal (`Minijuego.predecible`). Lo que depende
del momento (soltar el abono, fijar un pin) o del azar, y lo que abre o
cierra cosas, sigue esperando al servidor.
"""

from juego import tareas

# Las teclas del minijuego de una tarea (como app._tecla_en_partida).
MINIJUEGO = {"arriba": "arriba", "abajo": "abajo", "izquierda": "izquierda", "derecha": "derecha",
             "interactuar": "ok"}
MOSAICO = {"arriba": (-1, 0), "abajo": (1, 0), "izquierda": (0, -1), "derecha": (0, 1)}
MAX_ANOTADAS = 40


def _hacer(g, j, accion, solo=None):
    """Aplica `accion` a la copia del jugador `j` si se puede predecir.
    Devuelve a qué la aplicó ("mini" o "cursor") o None. Con `solo`, solo
    si es a eso (al volver a ponerla: si ya no hay minijuego, no va al menú)."""
    if j.preso is not None or getattr(j, "eliminado", False):
        return None
    presentacion = getattr(g, "presentacion", None)
    if presentacion is not None and getattr(presentacion, "abierta", False):
        return None
    mini = tareas.de(j)
    if mini is not None:
        a = MINIJUEGO.get(accion)
        if solo not in (None, "mini") or a is None or not hasattr(mini, "predecible") \
                or not mini.predecible(a):
            return None
        mini.tecla(a)
        return "mini"
    if solo not in (None, "cursor"):
        return None
    panel = j.panel
    if not isinstance(panel, dict) or panel.get("tipo") in ("emision", "tarea"):
        return None
    if j.escondido and panel.get("tipo") != "celular":
        return None
    if panel.get("tipo") == "celular" and accion in ("izquierda", "derecha"):
        return None            # (cambiar de pestaña: lo arma el servidor)
    filas = panel.get("filas")
    if filas:
        if accion not in MOSAICO:
            return None
        from juego.app import mover_en_mosaico
        j.cursor = mover_en_mosaico(filas, j.cursor, *MOSAICO[accion])
        return "cursor"
    if accion not in ("arriba", "abajo"):
        return None
    try:
        total = g._total_opciones(j)
    except (AttributeError, TypeError):
        return None
    if total <= 0:
        return None
    j.mover_cursor(-1 if accion == "arriba" else 1, total)
    return "cursor"


class Eco:
    def __init__(self):
        self.activo = True
        self.anotadas = {}       # número de jugador -> [(n de la intención, acción, "mini"/"cursor")]

    def presionar(self, g, i, accion, n):
        """El jugador `i` (de esta laptop) presionó `accion`, que salió en la
        intención `n`."""
        if not self.activo or not 0 <= i < len(g.jugadores):
            return
        tipo = _hacer(g, g.jugadores[i], accion)
        if tipo is not None:
            lista = self.anotadas.setdefault(i, [])
            lista.append((n, accion, tipo))
            del lista[:-MAX_ANOTADAS]

    def reaplicar(self, g, completos, acks):
        """Después de copiar la instantánea: lo que el servidor ya usó se
        borra; lo que no, se vuelve a poner encima de lo que llegó."""
        for i in list(self.anotadas):
            if acks is None:
                # (no se sabe qué incluye esta instantánea: mejor no adivinar)
                self.anotadas.pop(i)
                continue
            ack = acks[i] if i < len(acks) and isinstance(acks[i], int) else None
            lista = [x for x in self.anotadas[i] if ack is None or x[0] > ack]
            if not lista:
                self.anotadas.pop(i)
                continue
            self.anotadas[i] = lista
            if i in completos and 0 <= i < len(g.jugadores):
                for _, accion, tipo in lista:
                    _hacer(g, g.jugadores[i], accion, solo=tipo)

    def soltar(self):
        self.anotadas.clear()
