class ArbolDecision:
    """Árbol N-ario de decisiones: qué puede hacer el jugador con una publicación.

    Las cinco preguntas que plantea el laboratorio:

    1) ¿Qué problema resuelve?
       Representar que una misma publicación admite varias acciones
       (verificar, compartir, ignorar, reportar) y que cada una lleva a
       consecuencias distintas sobre la ciudad. El árbol guarda esa
       ramificación completa: qué se puede hacer y en qué desemboca.

    2) ¿Por qué esta estructura?
       Porque una decisión con consecuencias es literalmente un árbol: hay
       un punto de partida (la publicación), unas ramas excluyentes (las
       opciones) y unos desenlaces (las consecuencias). Guardarlo así deja
       el contenido del juego como datos en data/publicaciones_ejemplo.py
       en vez de como condicionales en el código: agregar una publicación
       nueva no implica tocar la lógica.

    3) ¿Qué variante se utiliza?
       Un árbol N-ario (cada nodo tiene una cantidad libre de hijos), no
       binario, porque una publicación puede ofrecer 2, 3 o 4 acciones
       según el caso. Tiene tres niveles y cada nodo lleva un tipo:
       la raíz es 'publicacion', sus hijos son 'opcion' y los nietos son
       'consecuencia'. Cada nodo carga además un diccionario de efectos
       (indicador -> delta) que se aplica al pasar por él.

    4) ¿Cómo se insertan y eliminan elementos?
       Se construye de arriba hacia abajo con construir_desde_dict, que
       recorre recursivamente un diccionario anidado y va colgando cada
       hijo con NodoDecision.agregar_hijo. No se eliminan nodos durante la
       partida: el árbol de una publicación es contenido fijo, y la
       publicación completa se descarta del ABB cuando ya se atendió.

    5) ¿Cómo se realiza su recorrido?
       No se recorre de forma automática: **lo recorre el jugador**. Desde
       la raíz, la tecla que presiona elige a cuál hijo bajar
       (recorrer_por_eleccion busca el hijo por su texto), se aplican los
       efectos de ese nodo con aplicar_efectos, y se baja una vez más hasta
       la consecuencia. Por eso no es preorden ni inorden: es un descenso
       de la raíz a una hoja guiado por la decisión del usuario.
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
