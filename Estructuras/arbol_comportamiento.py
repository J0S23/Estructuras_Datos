"""Árbol de comportamiento de los aliens.

Las cinco preguntas que plantea el laboratorio:

1) ¿Qué problema resuelve?
   Decidir qué hace cada alien en cada momento (patrullar, ir a investigar un
   ruido, perseguir a un jugador, atraparlo...) a partir de lo que percibe.
   Sin el árbol, esa lógica sería una cadena de `if` anidados dentro del
   alien, difícil de leer y de cambiar.

2) ¿Por qué esta estructura?
   Porque una decisión de este tipo ES un árbol: se hace una pregunta, según
   la respuesta se pasa a otra pregunta, y al final se llega a una acción. Las
   preguntas más urgentes van más cerca de la raíz (ver a un jugador importa
   más que haber oído un ruido), así que el orden del árbol es la prioridad
   del alien. Además el árbol vive como datos en data/comportamiento_alien.py:
   agregar un comportamiento nuevo es colgar un nodo, sin tocar el código del
   alien.

3) ¿Qué variante se utiliza?
   Un árbol binario de decisión (no de búsqueda: no hay una clave ordenada,
   la forma la fija el diseño). Cada nodo interno es una pregunta de sí o no
   con dos hijos; cada hoja es una acción.

4) ¿Cómo se insertan y eliminan elementos?
   Se construye de arriba hacia abajo con `construir_desde_dict`, que recorre
   recursivamente un diccionario anidado y cuelga los hijos `si` y `no` de
   cada pregunta. Para agregar una conducta se reemplaza una hoja por una
   pregunta nueva con dos hojas (`insertar_pregunta`). No se eliminan nodos
   durante la partida.

5) ¿Cómo se realiza su recorrido?
   `decidir` hace un descenso desde la raíz hasta una hoja: en cada pregunta
   evalúa la condición con lo que el alien percibe y baja por `si` o por `no`.
   Es O(altura), no recorre el árbol entero. Devuelve la acción y el camino
   recorrido, que es lo que la vista del árbol resalta en vivo. Para dibujar
   el árbol completo se usa un recorrido por niveles (BFS) con `por_niveles`,
   y `preorden` sirve para listarlo por consola.
"""

from collections import deque

from Estructuras.nodo_comportamiento import NodoComportamiento


class ArbolComportamiento:
    def __init__(self, datos=None):
        self.raiz = self.construir_desde_dict(datos) if datos else None

    # -- Construcción -------------------------------------------------------------

    def construir_desde_dict(self, datos):
        """Construye el árbol recursivamente a partir de un diccionario.

        Una pregunta es {"pregunta": texto, "condicion": nombre, "si": {...},
        "no": {...}}; una acción es {"accion": NOMBRE, "texto": texto}.
        """
        if not isinstance(datos, dict):
            raise TypeError("Cada nodo del árbol debe ser un diccionario.")

        if "accion" in datos:
            return NodoComportamiento(datos.get("texto", datos["accion"]), "accion",
                                      accion=datos["accion"])

        if "condicion" not in datos or "si" not in datos or "no" not in datos:
            raise ValueError(f"Pregunta incompleta en el árbol: {datos!r}")
        nodo = NodoComportamiento(datos.get("pregunta", datos["condicion"]), "pregunta",
                                  condicion=datos["condicion"])
        nodo.si = self.construir_desde_dict(datos["si"])
        nodo.no = self.construir_desde_dict(datos["no"])
        return nodo

    def insertar_pregunta(self, accion_hoja, pregunta, condicion, accion_si, accion_no):
        """Reemplaza la hoja `accion_hoja` por una pregunta con dos hojas.

        Así se le enseña una conducta nueva al alien sin reconstruir el árbol.
        Devuelve True si encontró la hoja.
        """
        padre, lado = self._buscar_padre_de_hoja(self.raiz, None, None, accion_hoja)
        if lado is None and (self.raiz is None or self.raiz.accion != accion_hoja):
            return False
        nueva = NodoComportamiento(pregunta, "pregunta", condicion=condicion)
        nueva.si = NodoComportamiento(accion_si, "accion", accion=accion_si)
        nueva.no = NodoComportamiento(accion_no, "accion", accion=accion_no)
        if padre is None:
            self.raiz = nueva
        else:
            setattr(padre, lado, nueva)
        return True

    def _buscar_padre_de_hoja(self, nodo, padre, lado, accion):
        if nodo is None:
            return None, None
        if nodo.es_hoja:
            return (padre, lado) if nodo.accion == accion else (None, None)
        for nombre in ("si", "no"):
            encontrado = self._buscar_padre_de_hoja(getattr(nodo, nombre), nodo, nombre, accion)
            if encontrado[1] is not None:
                return encontrado
        return None, None

    # -- Recorridos ---------------------------------------------------------------

    def decidir(self, condiciones):
        """Baja de la raíz a una hoja según `condiciones`.

        `condiciones` es un diccionario {nombre_condicion: bool} con lo que el
        alien percibe en este frame. Devuelve (accion, camino), donde camino es
        la lista de nodos visitados, en orden, incluida la hoja.
        """
        camino = []
        nodo = self.raiz
        while nodo is not None:
            camino.append(nodo)
            if nodo.es_hoja:
                return nodo.accion, camino
            nodo = nodo.si if condiciones.get(nodo.condicion, False) else nodo.no
        return None, camino

    def por_niveles(self):
        """Recorrido por niveles (BFS): lista de (nodo, nivel, padre)."""
        if self.raiz is None:
            return []
        resultado = []
        cola = deque([(self.raiz, 0, None)])
        while cola:
            nodo, nivel, padre = cola.popleft()
            resultado.append((nodo, nivel, padre))
            for hijo in nodo.hijos():
                cola.append((hijo, nivel + 1, nodo))
        return resultado

    def preorden(self, nodo="raiz", nivel=0):
        """Recorrido en preorden: lista de (nodo, nivel)."""
        if nodo == "raiz":
            nodo = self.raiz
        if nodo is None:
            return []
        resultado = [(nodo, nivel)]
        for hijo in nodo.hijos():
            resultado.extend(self.preorden(hijo, nivel + 1))
        return resultado

    def hojas(self):
        return [n for n, _ in self.preorden() if n.es_hoja]

    def altura(self, nodo="raiz"):
        if nodo == "raiz":
            nodo = self.raiz
        if nodo is None:
            return 0
        return 1 + max((self.altura(h) for h in nodo.hijos()), default=0)

    def contar(self):
        return len(self.preorden())

    def condiciones(self):
        """Nombres de todas las condiciones que usa el árbol."""
        return {n.condicion for n, _ in self.preorden() if not n.es_hoja}
