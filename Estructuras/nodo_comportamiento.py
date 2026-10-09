class NodoComportamiento:
    """Nodo del árbol de comportamiento de un alien.

    Hay dos tipos:

    - **pregunta**: tiene una `condicion` (el nombre de algo que el alien sabe
      responder con sí o no, como "ve_jugador") y exactamente dos hijos:
      `si` y `no`.
    - **accion**: es una hoja. Su `accion` es lo que el alien hace cuando el
      recorrido termina ahí ("PERSEGUIR", "PATRULLAR"...).

    `texto` es lo que se muestra en la vista del árbol.
    """

    def __init__(self, texto, tipo, condicion=None, accion=None):
        self.texto = texto
        self.tipo = tipo
        self.condicion = condicion
        self.accion = accion
        self.si = None
        self.no = None

    @property
    def es_hoja(self):
        return self.tipo == "accion"

    def hijos(self):
        """Hijos en orden (primero el `si`), sin los que falten."""
        return [h for h in (self.si, self.no) if h is not None]

    def __repr__(self):
        if self.es_hoja:
            return f"NodoComportamiento(accion={self.accion!r})"
        return f"NodoComportamiento(condicion={self.condicion!r})"
