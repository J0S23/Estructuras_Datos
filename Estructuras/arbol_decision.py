class ArbolDecision:
    """Árbol de decisiones para modelar consecuencias de una publicación.

    El recorrido real del árbol no se hace de forma automática; la elección del jugador
    guía la navegación por los hijos. Esto permite representar decisiones del tipo
    'Verificar', 'Compartir', 'Ignorar' y sus consecuencias de forma más natural.
    """

    def __init__(self, raiz):
        self.raiz = raiz

    def construir_desde_dict(self, data):
        """Construye un árbol recursivamente a partir de un diccionario anidado."""
        from Estructuras.nodo_decision import NodoDecision

        if not isinstance(data, dict):
            raise TypeError("La raíz debe ser un diccionario con estructura de árbol.")

        texto = data.get("texto", "")
        tipo = data.get("tipo", "publicacion")
        efectos = data.get("efectos", {})
        nodo = NodoDecision(texto=texto, tipo=tipo, efectos=efectos)

        for hijo in data.get("hijos", []):
            nodo.agregar_hijo(self.construir_desde_dict(hijo))

        return nodo

    def aplicar_efectos(self, nodo, estado_ciudad):
        if nodo is None:
            return
        for clave, valor in (nodo.efectos or {}).items():
            if clave in estado_ciudad:
                estado_ciudad[clave] = max(0, min(100, int(estado_ciudad[clave]) + int(valor)))

    def recorrer_por_eleccion(self, nodo_actual, eleccion_texto):
        if nodo_actual is None:
            return None
        for hijo in nodo_actual.hijos:
            if hijo.texto == eleccion_texto:
                return hijo
        for hijo in nodo_actual.hijos:
            if hijo.tipo == "opcion" and hijo.texto.lower() == eleccion_texto.lower():
                return hijo
        return None
