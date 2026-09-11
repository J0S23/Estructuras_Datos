class NodoPublicacion:
    """Nodo de un árbol binario de búsqueda para publicaciones."""

    def __init__(self, veracidad, titulo, tipo, izquierdo=None, derecho=None):
        self.veracidad = veracidad
        self.titulo = titulo
        self.tipo = tipo
        self.izquierdo = izquierdo
        self.derecho = derecho

    def __repr__(self):
        return f"NodoPublicacion(veracidad={self.veracidad}, titulo={self.titulo!r}, tipo={self.tipo!r})"
