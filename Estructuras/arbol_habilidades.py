"""Árbol binario de habilidades: la progresión de cada rol dentro de una ronda.

Las cinco preguntas que plantea el laboratorio:

1) ¿Qué problema resuelve?
   Darle al jugador una progresión durante la ronda sin volverla infinita.
   Cada rol empieza con su habilidad raíz y, a medida que gana puntos
   cumpliendo sus objetivos, desbloquea una habilidad más. Las habilidades
   desbloqueadas aparecen como opciones extra cuando el jugador interactúa,
   así que la progresión cambia lo que puede hacer, no solo un número.

2) ¿Por qué esta estructura?
   Porque la progresión es una decisión con consecuencia, no una lista de
   compras. Al llegar a un nodo el jugador elige **una de dos** ramas y la otra
   se cierra para el resto de la ronda: el candidato que se va por DEBATE nunca
   tendrá PRIORIDAD ni IMPACTO esa partida. Esa regla —dos opciones, una
   excluye a la otra, y lo que elijas determina qué se te abre después— es
   exactamente un árbol binario recorrido de la raíz hacia abajo. En una lista
   no existe la noción de "esto se abrió porque elegiste aquello".

3) ¿Qué variante se usa?
   Un árbol binario **no** de búsqueda: no hay clave que ordenar ni invariante
   de menor/mayor, porque la forma la fija el diseño del juego y no los datos.
   Se construye una sola vez desde un diccionario (data/habilidades.py) y
   durante la partida no se insertan ni eliminan nodos: lo único que cambia es
   el estado de cada uno (disponible / desbloqueada / descartada).

4) ¿Cómo se insertan y eliminan elementos?
   La construcción es recursiva: cada diccionario se vuelve un nodo y sus dos
   hijos se construyen igual, guardando el padre para poder subir. No hay
   eliminación: cuando el jugador escoge una rama, el hermano y todo su
   subárbol se marcan como descartados con un recorrido en preorden, pero
   siguen en memoria porque el panel los sigue dibujando en gris.

5) ¿Cómo se realiza su recorrido?
   Dos recorridos, cada uno para algo distinto. El panel de habilidades dibuja
   el árbol **por niveles** (BFS con una cola), que es lo que permite poner un
   nivel por fila. Y descartar una rama usa **preorden** (nodo, izquierdo,
   derecho), porque marcar al padre antes que a los hijos es lo natural cuando
   lo que se propaga baja por el árbol.
"""

from collections import deque

from Estructuras.nodo_habilidad import NodoHabilidad


class ArbolHabilidades:
    def __init__(self, rol=""):
        self.rol = rol
        self.raiz = None
        # Nodo más profundo ya desbloqueado: desde él cuelgan las opciones.
        self.actual = None

    # -- Construcción ---------------------------------------------------------

    def construir_desde_dict(self, datos):
        """Arma el árbol desde un diccionario anidado y devuelve la raíz.

        Formato esperado por nodo: clave, nombre, descripcion, costo,
        detalle_puntos e hijos (lista de 0 o 2 diccionarios iguales).
        """
        self.raiz = self._construir(datos, padre=None)
        if self.raiz is not None:
            # La raíz es la habilidad base del rol: se tiene desde el principio.
            self.raiz.desbloqueada = True
            self.actual = self.raiz
        return self.raiz

    def _construir(self, datos, padre):
        if datos is None:
            return None
        nodo = NodoHabilidad(
            clave=datos["clave"],
            nombre=datos.get("nombre", datos["clave"]),
            descripcion=datos.get("descripcion", ""),
            costo=datos.get("costo", 0),
            detalle_puntos=datos.get("detalle_puntos", ""),
        )
        nodo.padre = padre

        hijos = datos.get("hijos", []) or []
        if len(hijos) > 2:
            raise ValueError(
                f"El árbol de habilidades es binario y '{nodo.clave}' tiene {len(hijos)} hijos."
            )
        if len(hijos) >= 1:
            nodo.izquierdo = self._construir(hijos[0], nodo)
        if len(hijos) >= 2:
            nodo.derecho = self._construir(hijos[1], nodo)
        return nodo

    # -- Consultas -------------------------------------------------------------

    @property
    def vacio(self):
        return self.raiz is None

    def opciones(self):
        """Las habilidades que el jugador puede desbloquear ahora mismo.

        Son los hijos del nodo desbloqueado más profundo. Si ese nodo es hoja,
        no queda nada por desbloquear y devuelve una lista vacía.
        """
        if self.actual is None:
            return []
        return [h for h in self.actual.hijos if not h.desbloqueada and not h.descartada]

    def tiene(self, clave):
        """True si esa habilidad está desbloqueada. Es lo que consultan los eventos."""
        return any(n.clave == clave for n in self.desbloqueadas())

    def desbloqueadas(self):
        """El camino recorrido desde la raíz, de arriba hacia abajo."""
        camino, nodo = [], self.actual
        while nodo is not None:
            camino.append(nodo)
            nodo = nodo.padre
        return list(reversed(camino))

    def por_niveles(self):
        """Recorrido BFS: devuelve [(nodo, profundidad)] nivel por nivel.

        Lo usa el panel para dibujar un nivel por fila. Se hace con una cola:
        se saca un nodo, se dibuja, y se encolan sus hijos, de modo que todos
        los de un nivel salen antes que los del siguiente.
        """
        if self.raiz is None:
            return []
        resultado = []
        cola = deque([(self.raiz, 0)])
        while cola:
            nodo, profundidad = cola.popleft()
            resultado.append((nodo, profundidad))
            for hijo in nodo.hijos:
                cola.append((hijo, profundidad + 1))
        return resultado

    def altura(self):
        def _altura(nodo):
            if nodo is None:
                return 0
            return 1 + max(_altura(nodo.izquierdo), _altura(nodo.derecho))
        return _altura(self.raiz)

    # -- Progresión ------------------------------------------------------------

    def desbloquear(self, clave, puntos_disponibles):
        """Intenta desbloquear una habilidad. Devuelve (ok, mensaje, costo).

        Solo se puede desbloquear algo que esté colgando del nodo actual: no se
        salta niveles. Al lograrlo, el hermano y todo lo que colgaba de él
        quedan descartados para el resto de la ronda.
        """
        elegido = None
        for nodo in self.opciones():
            if nodo.clave == clave:
                elegido = nodo
                break
        if elegido is None:
            return False, "Esa habilidad no está disponible todavía.", 0
        if puntos_disponibles < elegido.costo:
            faltan = elegido.costo - puntos_disponibles
            return False, f"Te faltan {faltan} puntos para {elegido.nombre}.", 0

        elegido.desbloqueada = True
        for hermano in self.actual.hijos:
            if hermano is not elegido:
                self._descartar(hermano)
        self.actual = elegido
        return True, f"Desbloqueaste {elegido.nombre}.", elegido.costo

    def _descartar(self, nodo):
        """Marca en preorden el subárbol que el jugador dejó ir."""
        if nodo is None:
            return
        nodo.descartada = True
        self._descartar(nodo.izquierdo)
        self._descartar(nodo.derecho)


def construir_arbol(rol, datos):
    """Atajo: devuelve un ArbolHabilidades ya construido (o vacío si datos es None)."""
    arbol = ArbolHabilidades(rol)
    if datos is not None:
        arbol.construir_desde_dict(datos)
    return arbol
