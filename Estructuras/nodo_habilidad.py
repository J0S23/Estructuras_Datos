"""Nodo del árbol de habilidades (árbol binario).

A diferencia del ABB, aquí la posición de un nodo no depende de una clave que
se compare: la forma del árbol la decide el diseño del juego. Lo que importa es
que cada nodo tiene a lo sumo dos hijos, porque al llegar a él el jugador
escoge una de dos ramas y pierde la otra para el resto de la ronda.
"""


class NodoHabilidad:
    def __init__(self, clave, nombre, descripcion, costo=0, detalle_puntos=""):
        self.clave = clave
        self.nombre = nombre
        self.descripcion = descripcion
        self.costo = costo
        self.detalle_puntos = detalle_puntos

        self.izquierdo = None
        self.derecho = None
        self.padre = None

        # Estado durante la partida.
        self.desbloqueada = False
        self.descartada = False  # el jugador eligió a su hermano

    @property
    def hijos(self):
        """Los hijos que existen, de izquierda a derecha."""
        return [h for h in (self.izquierdo, self.derecho) if h is not None]

    @property
    def es_hoja(self):
        return self.izquierdo is None and self.derecho is None

    def __repr__(self):
        estado = "desbloqueada" if self.desbloqueada else ("descartada" if self.descartada else "disponible")
        return f"NodoHabilidad({self.clave}, {estado})"
