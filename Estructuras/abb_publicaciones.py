"""Árbol binario de búsqueda (ABB) de publicaciones, ordenadas por veracidad.

Las cinco preguntas que plantea el laboratorio:

1) ¿Qué problema resuelve?
   Decidir en qué orden el jugador enfrenta las publicaciones que circulan
   en Civitas. La ciudad puede tener muchas publicaciones pendientes y la
   más dudosa es la que urge atender, porque es la que más desinformación
   genera si se propaga. El ABB mantiene esas publicaciones ordenadas por
   veracidad y permite sacar siempre la peor primero.

2) ¿Por qué esta estructura?
   Porque el juego necesita tres cosas sobre el mismo conjunto: mantenerlo
   ordenado, buscar por nivel de veracidad, y retirar publicaciones ya
   atendidas. En un ABB las tres son O(log n) en el caso promedio, y el
   recorrido inorden entrega el orden sin tener que reordenar nada.
   Con una lista habría que recorrerla entera o reordenarla en cada turno.

3) ¿Qué variante se usa?
   Un ABB clásico, sin balanceo (no es AVL ni rojo-negro). La clave es la
   veracidad estimada (0-100) y el contenido es el título y el tipo de la
   publicación. No admite claves repetidas: insertar una clave existente
   reemplaza su contenido, y quien inserta se encarga de desplazar la clave
   si quiere conservar ambas (ver Game._construir_arboles en App.py).
   Limitación conocida: si las publicaciones se insertaran ya ordenadas, el
   árbol degeneraría en una lista y las operaciones pasarían a O(n).

4) ¿Cómo se insertan y eliminan elementos?
   Se inserta bajando por el árbol comparando contra la clave de cada nodo:
   menor va al subárbol izquierdo, mayor al derecho, hasta encontrar un
   hueco. Para eliminar hay tres casos: si el nodo es hoja se quita; si
   tiene un solo hijo, ese hijo lo reemplaza; y si tiene dos hijos se busca
   su sucesor inorden (el mínimo del subárbol derecho), se copian sus datos
   al nodo y se elimina el sucesor de su posición original.
   **No hay rebalanceo**: la forma del árbol depende del orden de inserción.

5) ¿Cómo se realiza su recorrido?
   El recorrido principal es inorden (izquierdo - nodo - derecho), que por
   la propiedad del ABB entrega las publicaciones ordenadas de menor a
   mayor veracidad. Por eso el juego toma el primer elemento del recorrido
   para obtener la publicación más dudosa. `buscar_menores_a` hace un
   recorrido parcial: poda el subárbol derecho cuando ya superó el umbral.
"""

from Estructuras.nodo_abb import NodoPublicacion


class ArbolPublicaciones:
    def __init__(self):
        self.raiz = None

    def insertar(self, veracidad, titulo, tipo):
        def _insertar(nodo, veracidad, titulo, tipo):
            if nodo is None:
                return NodoPublicacion(veracidad, titulo, tipo)
            if veracidad < nodo.veracidad:
                nodo.izquierdo = _insertar(nodo.izquierdo, veracidad, titulo, tipo)
            elif veracidad > nodo.veracidad:
                nodo.derecho = _insertar(nodo.derecho, veracidad, titulo, tipo)
            else:
                nodo.titulo = titulo
                nodo.tipo = tipo
            return nodo

        self.raiz = _insertar(self.raiz, veracidad, titulo, tipo)

    def buscar(self, veracidad):
        actual = self.raiz
        while actual is not None:
            if veracidad == actual.veracidad:
                return actual
            if veracidad < actual.veracidad:
                actual = actual.izquierdo
            else:
                actual = actual.derecho
        return None

    def _minimo(self, nodo):
        while nodo is not None and nodo.izquierdo is not None:
            nodo = nodo.izquierdo
        return nodo

    def eliminar(self, veracidad):
        def _eliminar(nodo, veracidad):
            if nodo is None:
                return None
            if veracidad < nodo.veracidad:
                nodo.izquierdo = _eliminar(nodo.izquierdo, veracidad)
                return nodo
            if veracidad > nodo.veracidad:
                nodo.derecho = _eliminar(nodo.derecho, veracidad)
                return nodo

            if nodo.izquierdo is None and nodo.derecho is None:
                return None
            if nodo.izquierdo is None:
                return nodo.derecho
            if nodo.derecho is None:
                return nodo.izquierdo

            minimo = self._minimo(nodo.derecho)
            nodo.veracidad = minimo.veracidad
            nodo.titulo = minimo.titulo
            nodo.tipo = minimo.tipo
            nodo.derecho = _eliminar(nodo.derecho, minimo.veracidad)
            return nodo

        self.raiz = _eliminar(self.raiz, veracidad)

    def recorrido_inorden(self):
        resultado = []

        def _inorden(nodo):
            if nodo is None:
                return
            _inorden(nodo.izquierdo)
            resultado.append({
                "veracidad": nodo.veracidad,
                "titulo": nodo.titulo,
                "tipo": nodo.tipo,
            })
            _inorden(nodo.derecho)

        _inorden(self.raiz)
        return resultado

    def buscar_menores_a(self, umbral):
        """Devuelve las publicaciones con veracidad menor al umbral, ordenadas.

        Aprovecha la propiedad del ABB en vez de revisar todos los nodos: si la
        veracidad del nodo actual ya alcanzó el umbral, todo su subárbol derecho
        tiene claves aún mayores, así que se poda completo y no se visita.
        """
        resultado = []

        def _recorrer(nodo):
            if nodo is None:
                return
            # El subárbol izquierdo siempre puede tener claves menores.
            _recorrer(nodo.izquierdo)
            if nodo.veracidad >= umbral:
                # Este nodo y todo lo que está a su derecha se salen del rango.
                return
            resultado.append({
                "veracidad": nodo.veracidad,
                "titulo": nodo.titulo,
                "tipo": nodo.tipo,
            })
            _recorrer(nodo.derecho)

        _recorrer(self.raiz)
        return resultado
