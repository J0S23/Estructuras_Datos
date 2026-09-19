class NodoDialogo:
    """Nodo de un árbol de diálogo.

    Cada nodo es una intervención del NPC (`texto`) y sus hijos son las
    respuestas que el jugador puede dar. La respuesta del jugador se guarda en
    `respuesta`: es lo que se muestra como opción para llegar a este nodo.

    - `respuesta`: lo que dice el jugador para llegar aquí (None en la raíz).
    - `texto`: lo que contesta el NPC.
    - `efectos`: indicador -> delta que se aplica al llegar a este nodo.
    - `hijos`: siguientes respuestas posibles. Si está vacío, aquí termina
      la conversación.
    """

    def __init__(self, texto, respuesta=None, hijos=None, efectos=None):
        self.texto = texto
        self.respuesta = respuesta
        self.hijos = hijos if hijos is not None else []
        self.efectos = efectos if efectos is not None else {}

    def agregar_hijo(self, nodo):
        self.hijos.append(nodo)

    def es_final(self):
        return not self.hijos

    def __repr__(self):
        return f"NodoDialogo(texto={self.texto[:30]!r}..., hijos={len(self.hijos)})"
