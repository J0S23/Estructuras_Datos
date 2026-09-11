class NodoDecision:
    """Nodo N-ario para representar una decisión dentro del árbol de publicaciones."""

    def __init__(self, texto, tipo="opcion", hijos=None, efectos=None):
        self.texto = texto
        self.tipo = tipo
        self.hijos = hijos if hijos is not None else []
        self.efectos = efectos if efectos is not None else {}

    def agregar_hijo(self, nodo):
        self.hijos.append(nodo)

    def __repr__(self):
        return f"NodoDecision(texto={self.texto!r}, tipo={self.tipo!r}, hijos={len(self.hijos)})"
