"""Árbol binario de búsqueda para publicaciones.

Las cinco preguntas que plantea el laboratorio son:
1) ¿Qué problema resuelve? Ordenar y buscar publicaciones por su nivel de veracidad.
2) ¿Por qué esta estructura? Porque permite búsquedas rápidas y recorrido ordenado.
3) ¿Qué variante se usa? Un ABB clásico, con clave veracidad y contenido del título/tipo.
4) ¿Cómo se inserta y elimina? Se insertan por clave veracidad y se eliminan reequilibrando subárboles.
5) ¿Cómo se recorre? Mediante recorrido inorden para obtener orden ascendente de veracidad.
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
        resultado = []

        def _recorrer(nodo):
            if nodo is None:
                return
            if nodo.veracidad < umbral:
                resultado.append({
                    "veracidad": nodo.veracidad,
                    "titulo": nodo.titulo,
                    "tipo": nodo.tipo,
                })
            _recorrer(nodo.izquierdo)
            _recorrer(nodo.derecho)

        _recorrer(self.raiz)
        return resultado
